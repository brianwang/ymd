import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TagRules:
    max_tags: int = 10
    max_len: int = 20


# 允许字符：中文、英文、数字、下划线、连字符、中点（常用于中文人名/地名）
_TAG_ALLOWED_RE = re.compile(r"^[0-9A-Za-z_\u4e00-\u9fff·-]+$")

# 从正文解析 #标签：匹配以 # 开头的一段连续“允许字符”
# - 为了避免把 URL 中的 #fragment 误判得太离谱，这里要求 # 前一位不是字母数字下划线
_HASHTAG_RE = re.compile(r"(?<![0-9A-Za-z_])#([0-9A-Za-z_\u4e00-\u9fff·-]{1,64})")


def normalize_tag(tag: str) -> str:
    """
    归一化规则：
    - trim
    - 移除前导 #
    - 英文统一小写（中文不受影响）
    """
    t = (tag or "").strip()
    if t.startswith("#"):
        t = t[1:].strip()
    # 仅对 ASCII 字母做小写化，避免影响其它 unicode 字符
    t = "".join((c.lower() if "A" <= c <= "Z" else c) for c in t)
    return t


def extract_hashtags_from_content(content: str) -> list[str]:
    """
    从正文中解析 #标签，并做 normalize；不做数量/长度限制（限制由 validate_tags 处理）。
    """
    text = content or ""
    raw = [m.group(1) for m in _HASHTAG_RE.finditer(text)]
    return [normalize_tag(x) for x in raw if normalize_tag(x)]


def dedupe_preserve_order(tags: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in tags:
        if t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out


def validate_tags(tags: list[str], rules: TagRules = TagRules()) -> list[str]:
    """
    校验并返回“已归一化 + 去重 + 顺序稳定”的 tags。
    失败时抛 ValueError，用于 API 返回 4xx 可读错误。
    """
    normalized = [normalize_tag(t) for t in (tags or [])]
    normalized = [t for t in normalized if t]  # 过滤空白
    normalized = dedupe_preserve_order(normalized)

    if len(normalized) > rules.max_tags:
        raise ValueError(f"标签数量过多：最多支持 {rules.max_tags} 个")

    for t in normalized:
        if len(t) > rules.max_len:
            raise ValueError(f"标签过长：单个标签最多 {rules.max_len} 个字符（当前：{len(t)}）")
        if not _TAG_ALLOWED_RE.match(t):
            raise ValueError("标签包含非法字符：仅支持中文/英文/数字/下划线/连字符")

    return normalized


def merge_explicit_and_parsed_tags(*, explicit: list[str] | None, parsed: list[str] | None) -> list[str]:
    """
    合并显式 tags 与正文解析 tags：显式优先、去重、归一化。
    合并后仍需 validate_tags 做限制校验。
    """
    merged = []
    merged.extend(explicit or [])
    merged.extend(parsed or [])
    merged = [normalize_tag(t) for t in merged if normalize_tag(t)]
    return dedupe_preserve_order(merged)

