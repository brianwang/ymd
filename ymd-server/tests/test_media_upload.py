import os
import sys
import tempfile
import unittest

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

# 确保优先加载本仓库 ymd-server 下的 app 包（避免与环境中同名 app 冲突）
_SERVER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _SERVER_ROOT not in sys.path:
    sys.path.insert(0, _SERVER_ROOT)

from app.api import media as media_api


def _build_test_app(static_dir: str) -> FastAPI:
    app = FastAPI()
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.include_router(media_api.router, prefix="/api/v1")
    return app


class TestMediaUpload(unittest.TestCase):
    def test_upload_audio_mp3_ok(self):
        with tempfile.TemporaryDirectory() as td:
            old_cwd = os.getcwd()
            os.chdir(td)
            try:
                app = _build_test_app(static_dir="uploads")
                client = TestClient(app)

                resp = client.post(
                    "/api/v1/media/upload",
                    files={"file": ("voice.mp3", b"fake-audio-bytes", "audio/mpeg")},
                )
                self.assertEqual(resp.status_code, 200, resp.text)
                data = resp.json()
                self.assertIn("url", data)
                self.assertIn("/static/", data["url"])
            finally:
                os.chdir(old_cwd)

    def test_upload_unsupported_ext_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            old_cwd = os.getcwd()
            os.chdir(td)
            try:
                app = _build_test_app(static_dir="uploads")
                client = TestClient(app)
                resp = client.post(
                    "/api/v1/media/upload",
                    files={"file": ("note.txt", b"hello", "text/plain")},
                )
                self.assertEqual(resp.status_code, 400, resp.text)
            finally:
                os.chdir(old_cwd)

    def test_upload_mismatched_content_type_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            old_cwd = os.getcwd()
            os.chdir(td)
            try:
                app = _build_test_app(static_dir="uploads")
                client = TestClient(app)
                resp = client.post(
                    "/api/v1/media/upload",
                    files={"file": ("voice.m4a", b"fake", "image/png")},
                )
                self.assertEqual(resp.status_code, 400, resp.text)
                self.assertIn("文件类型不匹配", resp.text)
            finally:
                os.chdir(old_cwd)

    def test_upload_audio_too_large_413_and_cleanup(self):
        with tempfile.TemporaryDirectory() as td:
            # 在用例内把上限压小，避免生成超大 payload
            old_limit = media_api._MAX_AUDIO_BYTES
            media_api._MAX_AUDIO_BYTES = 1024  # 1KB
            try:
                old_cwd = os.getcwd()
                os.chdir(td)
                try:
                    app = _build_test_app(static_dir="uploads")
                    client = TestClient(app)

                    payload = b"x" * 2048  # 2KB
                    resp = client.post(
                        "/api/v1/media/upload",
                        files={"file": ("voice.aac", payload, "audio/aac")},
                    )
                    self.assertEqual(resp.status_code, 413, resp.text)

                    # 确保没有残留半写入文件
                    leftover = os.listdir("uploads") if os.path.exists("uploads") else []
                    self.assertEqual(leftover, [])
                finally:
                    os.chdir(old_cwd)
            finally:
                media_api._MAX_AUDIO_BYTES = old_limit


if __name__ == "__main__":
    unittest.main()
