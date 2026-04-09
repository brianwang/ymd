import os
import sys
import unittest

# 确保优先加载本仓库 ymd-server 下的 app 包（避免与环境中同名 app 冲突）
_SERVER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SERVER_ROOT not in sys.path:
    sys.path.insert(0, _SERVER_ROOT)

from app.services.post_tags import (
    TagRules,
    extract_hashtags_from_content,
    merge_explicit_and_parsed_tags,
    normalize_tag,
    validate_tags,
)


class TestPostTags(unittest.TestCase):
    def test_normalize_tag_strip_hash_and_lower(self):
        self.assertEqual(normalize_tag("  #HelloWorld "), "helloworld")
        self.assertEqual(normalize_tag("#露营"), "露营")

    def test_extract_hashtags_from_content(self):
        content = "今天去 #露营 了！顺便 #共居-体验 #HelloWorld"
        tags = extract_hashtags_from_content(content)
        self.assertEqual(tags, ["露营", "共居-体验", "helloworld"])

    def test_merge_and_validate_dedupe_preserve_order(self):
        explicit = ["露营", "共居", "露营", "#Hello"]
        parsed = ["#露营", "hello", "共居"]
        merged = merge_explicit_and_parsed_tags(explicit=explicit, parsed=parsed)
        # merge 只做归一化 + 去重（不校验长度/字符）
        self.assertEqual(merged, ["露营", "共居", "hello"])
        validated = validate_tags(merged, rules=TagRules(max_tags=10, max_len=20))
        self.assertEqual(validated, ["露营", "共居", "hello"])

    def test_validate_tags_too_many(self):
        tags = [f"t{i}" for i in range(11)]
        with self.assertRaises(ValueError) as ctx:
            validate_tags(tags, rules=TagRules(max_tags=10, max_len=20))
        self.assertIn("标签数量过多", str(ctx.exception))

    def test_validate_tags_too_long(self):
        with self.assertRaises(ValueError) as ctx:
            validate_tags(["a" * 21], rules=TagRules(max_tags=10, max_len=20))
        self.assertIn("标签过长", str(ctx.exception))

    def test_validate_tags_illegal_chars(self):
        with self.assertRaises(ValueError) as ctx:
            validate_tags(["bad tag"], rules=TagRules(max_tags=10, max_len=20))
        self.assertIn("非法字符", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
