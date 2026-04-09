#!/usr/bin/env python3
"""
可重复执行的测试图片生成脚本：
- 读取清单（JSON manifest）
- 生成缺失图片并落盘
- 支持 provider: http / mock（仅使用 Python 标准库，无三方依赖）
- 支持并发 / 跳过 / 覆盖 / 输出目录配置
"""

from __future__ import annotations

import argparse
import base64
import binascii
import concurrent.futures
import hashlib
import json
import os
import random
import struct
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# -----------------------------
# Manifest
# -----------------------------


@dataclass(frozen=True)
class ManifestItem:
    id: str
    path: str
    width: int
    height: int
    prompt: str = ""
    kind: str = ""
    tags: Tuple[str, ...] = ()
    format: str = "png"


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _as_str(x: Any, *, default: str = "") -> str:
    if x is None:
        return default
    if isinstance(x, str):
        return x
    raise ValueError(f"期望 string，实际: {type(x)}")


def _as_int(x: Any, *, field: str) -> int:
    _require(isinstance(x, int), f"字段 {field} 期望 int，实际: {type(x)}")
    return int(x)


def _as_str_list(x: Any, *, field: str) -> Tuple[str, ...]:
    if x is None:
        return ()
    _require(isinstance(x, list), f"字段 {field} 期望 list[string]，实际: {type(x)}")
    out: List[str] = []
    for v in x:
        _require(isinstance(v, str), f"字段 {field} 期望 list[string]，实际包含: {type(v)}")
        out.append(v)
    return tuple(out)


def _safe_rel_path(rel: str) -> str:
    # 约束：manifest 的 path 必须是相对路径（防止误写到仓库外）。
    p = Path(rel)
    _require(not p.is_absolute(), f"path 必须是相对路径，实际: {rel}")
    _require(".." not in p.parts, f"path 不允许包含 ..，实际: {rel}")
    # 统一为 POSIX 风格写法，但落盘仍用本机 Path
    return "/".join(p.parts)


def load_manifest(path: Path) -> List[ManifestItem]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(raw, dict), "manifest 顶层必须是 object")
    items = raw.get("items")
    _require(isinstance(items, list), "manifest.items 必须是数组")

    out: List[ManifestItem] = []
    for i, it in enumerate(items):
        _require(isinstance(it, dict), f"manifest.items[{i}] 必须是 object")
        item = ManifestItem(
            id=_as_str(it.get("id"), default="").strip(),
            path=_safe_rel_path(_as_str(it.get("path"), default="").strip()),
            width=_as_int(it.get("width"), field="width"),
            height=_as_int(it.get("height"), field="height"),
            prompt=_as_str(it.get("prompt"), default=""),
            kind=_as_str(it.get("kind"), default=""),
            tags=_as_str_list(it.get("tags"), field="tags"),
            format=_as_str(it.get("format"), default="png") or "png",
        )
        _require(item.id, f"manifest.items[{i}].id 不能为空")
        _require(item.path, f"manifest.items[{i}].path 不能为空")
        _require(item.width > 0 and item.height > 0, f"manifest.items[{i}] width/height 必须 > 0")
        _require(item.format.lower() == "png", f"当前仅支持 png，实际: {item.format}")
        out.append(item)
    return out


# -----------------------------
# Providers
# -----------------------------


class ImageProvider:
    def generate_png(self, item: ManifestItem) -> bytes:
        raise NotImplementedError


class MockProvider(ImageProvider):
    """
    生成确定性的 PNG（仅用标准库），用于本地开发/离线/CI。
    """

    def generate_png(self, item: ManifestItem) -> bytes:
        seed_material = f"{item.id}|{item.path}|{item.width}x{item.height}|{item.prompt}|{item.kind}|{','.join(item.tags)}"
        seed = int(hashlib.sha256(seed_material.encode("utf-8")).hexdigest()[:16], 16)
        rng = random.Random(seed)

        # 生成一个简单的“块状渐变”图案，便于区分不同图片
        w, h = item.width, item.height
        block = max(8, min(w, h) // 12)
        pixels = bytearray(w * h * 4)

        base_r = rng.randrange(40, 216)
        base_g = rng.randrange(40, 216)
        base_b = rng.randrange(40, 216)
        accent_r = rng.randrange(40, 216)
        accent_g = rng.randrange(40, 216)
        accent_b = rng.randrange(40, 216)

        for y in range(h):
            by = (y // block) % 2
            for x in range(w):
                bx = (x // block) % 2
                t = (x / max(1, w - 1)) * 0.65 + (y / max(1, h - 1)) * 0.35
                if (bx ^ by) == 0:
                    r = int(base_r * (1 - t) + accent_r * t)
                    g = int(base_g * (1 - t) + accent_g * t)
                    b = int(base_b * (1 - t) + accent_b * t)
                else:
                    r = int(accent_r * (1 - t) + base_r * t)
                    g = int(accent_g * (1 - t) + base_g * t)
                    b = int(accent_b * (1 - t) + base_b * t)

                i = (y * w + x) * 4
                pixels[i + 0] = r & 0xFF
                pixels[i + 1] = g & 0xFF
                pixels[i + 2] = b & 0xFF
                pixels[i + 3] = 255

        return encode_png_rgba(w, h, bytes(pixels))


class HttpProvider(ImageProvider):
    """
    通用 HTTP provider（仅用标准库 urllib）：
    - POST JSON: {prompt,width,height,format="png",...}
    - 支持返回：
      1) image/* 直接返回 bytes
      2) JSON Base64: {"image_base64": "..."} 或 OpenAI 兼容 {"data":[{"b64_json":"..."}]}
      3) JSON URL: {"image_url": "..."} / {"url": "..."}（脚本会再 GET 一次）
    """

    def __init__(
        self,
        *,
        url: str,
        headers: Dict[str, str],
        timeout_s: float,
        retries: int,
        retry_backoff_s: float,
    ) -> None:
        self._url = url
        self._headers = headers
        self._timeout_s = timeout_s
        self._retries = max(0, retries)
        self._retry_backoff_s = max(0.0, retry_backoff_s)

    def generate_png(self, item: ManifestItem) -> bytes:
        payload = {
            "prompt": item.prompt or f"Test image: {item.id}",
            "width": item.width,
            "height": item.height,
            "format": "png",
            "id": item.id,
            "path": item.path,
            "kind": item.kind,
            "tags": list(item.tags),
        }

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "*/*", **self._headers}

        last_err: Optional[BaseException] = None
        for attempt in range(self._retries + 1):
            try:
                req = urllib.request.Request(self._url, data=body, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self._timeout_s) as resp:
                    content_type = (resp.headers.get("Content-Type") or "").lower()
                    data = resp.read()
                    if content_type.startswith("image/"):
                        return data
                    return _extract_png_from_json_or_url(data, content_type, timeout_s=self._timeout_s)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as e:
                last_err = e
                if attempt < self._retries:
                    time.sleep(self._retry_backoff_s * (2**attempt))
                    continue
                break

        raise RuntimeError(f"HTTP provider 生成失败: {last_err}") from last_err


def _extract_png_from_json_or_url(data: bytes, content_type: str, *, timeout_s: float) -> bytes:
    # 尝试按 JSON 解析
    try:
        obj = json.loads(data.decode("utf-8"))
    except Exception as e:
        preview = data[:200]
        raise ValueError(f"HTTP 返回非 image/* 且非 JSON（Content-Type={content_type}），前 200 字节: {preview!r}") from e

    def find_b64(o: Any) -> Optional[str]:
        if isinstance(o, dict):
            for k in ("image_base64", "b64_json", "base64", "png_base64"):
                v = o.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return None
        return None

    def find_url(o: Any) -> Optional[str]:
        if isinstance(o, dict):
            for k in ("image_url", "url"):
                v = o.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return None
        return None

    b64 = find_b64(obj)
    if b64 is None and isinstance(obj, dict) and isinstance(obj.get("data"), list) and obj["data"]:
        b64 = find_b64(obj["data"][0])
        if b64 is None and isinstance(obj["data"][0], dict):
            # 兼容 {"data":[{"url":"..."}]}
            url = find_url(obj["data"][0])
            if url:
                return _http_get_bytes(url, timeout_s=timeout_s)

    if b64 is None and isinstance(obj, dict) and isinstance(obj.get("images"), list) and obj["images"]:
        if isinstance(obj["images"][0], str):
            b64 = obj["images"][0].strip()

    if b64 is not None:
        try:
            return base64.b64decode(b64, validate=True)
        except binascii.Error as e:
            raise ValueError("解析 Base64 失败（字段包含非法字符/格式）") from e

    url = find_url(obj)
    if url:
        return _http_get_bytes(url, timeout_s=timeout_s)

    raise ValueError("JSON 响应中未找到可解析的图片字段（image_base64/b64_json/images/url 等）")


def _http_get_bytes(url: str, *, timeout_s: float) -> bytes:
    req = urllib.request.Request(url, headers={"Accept": "image/*,*/*"}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return resp.read()


# -----------------------------
# PNG encoder (RGBA)
# -----------------------------


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(chunk_type)
    crc = binascii.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def encode_png_rgba(width: int, height: int, rgba: bytes) -> bytes:
    _require(len(rgba) == width * height * 4, "rgba 数据长度不匹配")

    # 每行：filter(0) + raw rgba
    stride = width * 4
    raw = bytearray((stride + 1) * height)
    for y in range(height):
        row_start = y * (stride + 1)
        raw[row_start] = 0  # filter type 0
        src = y * stride
        raw[row_start + 1 : row_start + 1 + stride] = rgba[src : src + stride]

    compressed = zlib.compress(bytes(raw), level=6)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8bit RGBA
    return b"".join(
        [
            signature,
            _png_chunk(b"IHDR", ihdr),
            _png_chunk(b"IDAT", compressed),
            _png_chunk(b"IEND", b""),
        ]
    )


# -----------------------------
# Runner
# -----------------------------


@dataclass(frozen=True)
class JobResult:
    item_id: str
    path: str
    status: str  # generated / skipped / overwritten / failed
    detail: str = ""


def _write_atomic(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=str(target.parent), prefix=target.name + ".", suffix=".tmp") as f:
        tmp_path = Path(f.name)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(str(tmp_path), str(target))


def _build_provider(args: argparse.Namespace) -> ImageProvider:
    provider = (args.provider or "").strip().lower()
    if provider == "mock":
        return MockProvider()
    if provider == "http":
        url = (args.http_url or "").strip()
        _require(url, "provider=http 时必须提供 --http-url 或环境变量 YMD_TESTIMG_HTTP_URL")
        headers: Dict[str, str] = {}
        for h in args.http_header or []:
            if ":" not in h:
                raise ValueError(f"--http-header 期望 'Key: Value'，实际: {h!r}")
            k, v = h.split(":", 1)
            headers[k.strip()] = v.strip()
        return HttpProvider(
            url=url,
            headers=headers,
            timeout_s=float(args.timeout_s),
            retries=int(args.retries),
            retry_backoff_s=float(args.retry_backoff_s),
        )
    raise ValueError(f"未知 provider: {provider}（支持: mock/http）")


def _should_process(item: ManifestItem, *, only_kind: Optional[str]) -> bool:
    if not only_kind:
        return True
    return (item.kind or "").strip().lower() == only_kind.strip().lower()


def _run_one(
    provider: ImageProvider,
    item: ManifestItem,
    *,
    out_dir: Path,
    overwrite: bool,
    dry_run: bool,
) -> JobResult:
    target = out_dir / Path(item.path)

    exists = target.exists()
    if exists and not overwrite:
        return JobResult(item_id=item.id, path=str(target), status="skipped")

    if dry_run:
        return JobResult(item_id=item.id, path=str(target), status="overwritten" if exists else "generated", detail="dry-run")

    png = provider.generate_png(item)
    _write_atomic(target, png)
    return JobResult(item_id=item.id, path=str(target), status="overwritten" if exists else "generated")


def main(argv: Optional[List[str]] = None) -> int:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[2]  # .../ymd-server/scripts -> .../ymd

    default_manifest = repo_root / "ymd-server" / "testdata_images_manifest.json"
    default_out_dir = repo_root / "ymd-app" / "src" / "static" / "testdata"

    p = argparse.ArgumentParser(description="Generate testdata images from manifest (idempotent).")
    p.add_argument("--manifest", type=str, default=str(default_manifest), help="manifest JSON 文件路径")
    p.add_argument("--out-dir", type=str, default=str(default_out_dir), help="输出目录（manifest.path 相对该目录）")
    p.add_argument("--provider", type=str, default=os.getenv("YMD_TESTIMG_PROVIDER", "mock"), help="mock 或 http")

    # http provider
    p.add_argument("--http-url", type=str, default=os.getenv("YMD_TESTIMG_HTTP_URL", ""), help="HTTP 生成接口 URL（POST JSON）")
    p.add_argument(
        "--http-header",
        type=str,
        action="append",
        default=[],
        help="追加 HTTP Header，例如：--http-header 'Authorization: Bearer xxx'（可重复）",
    )
    p.add_argument("--timeout-s", type=float, default=float(os.getenv("YMD_TESTIMG_TIMEOUT_S", "60")), help="HTTP 超时（秒）")
    p.add_argument("--retries", type=int, default=int(os.getenv("YMD_TESTIMG_RETRIES", "2")), help="失败重试次数")
    p.add_argument(
        "--retry-backoff-s",
        type=float,
        default=float(os.getenv("YMD_TESTIMG_RETRY_BACKOFF_S", "0.8")),
        help="重试退避基数（秒），每次 *2",
    )

    # behavior
    p.add_argument("--concurrency", type=int, default=int(os.getenv("YMD_TESTIMG_CONCURRENCY", "4")), help="并发数（线程）")
    p.add_argument("--overwrite", action="store_true", help="覆盖已存在文件（默认跳过）")
    p.add_argument("--dry-run", action="store_true", help="只打印计划，不落盘、不请求")
    p.add_argument("--only-kind", type=str, default="", help="仅处理指定 kind（可选）")

    args = p.parse_args(argv)

    manifest_path = Path(args.manifest).resolve()
    out_dir = Path(args.out_dir).resolve()
    _require(manifest_path.exists(), f"manifest 文件不存在: {manifest_path}")

    items = load_manifest(manifest_path)
    only_kind = (args.only_kind or "").strip() or None
    items = [it for it in items if _should_process(it, only_kind=only_kind)]

    provider = _build_provider(args)
    concurrency = max(1, int(args.concurrency))

    started = time.time()
    results: List[JobResult] = []

    def task(it: ManifestItem) -> JobResult:
        try:
            return _run_one(
                provider,
                it,
                out_dir=out_dir,
                overwrite=bool(args.overwrite),
                dry_run=bool(args.dry_run),
            )
        except Exception as e:
            return JobResult(item_id=it.id, path=str(out_dir / it.path), status="failed", detail=str(e))

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(task, it) for it in items]
        for fut in concurrent.futures.as_completed(futs):
            r = fut.result()
            results.append(r)
            if r.status == "failed":
                print(f"[FAILED] {r.item_id} -> {r.path} | {r.detail}", file=sys.stderr)
            elif r.status == "skipped":
                print(f"[SKIP]   {r.item_id} -> {r.path}")
            elif r.status == "overwritten":
                print(f"[OVER]   {r.item_id} -> {r.path}{' (dry-run)' if r.detail else ''}")
            else:
                print(f"[GEN]    {r.item_id} -> {r.path}{' (dry-run)' if r.detail else ''}")

    # summary
    elapsed = time.time() - started
    cnt = {"generated": 0, "skipped": 0, "overwritten": 0, "failed": 0}
    for r in results:
        cnt[r.status] = cnt.get(r.status, 0) + 1

    print(
        f"Summary: total={len(results)} generated={cnt['generated']} overwritten={cnt['overwritten']} skipped={cnt['skipped']} failed={cnt['failed']} elapsed={elapsed:.2f}s"
    )
    return 1 if cnt["failed"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())

