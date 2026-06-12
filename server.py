#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server tĩnh phục vụ tool "Ghép Ảnh Logo EyePlus" (thư mục web/).
Dùng cho Railway: lắng nghe trên cổng do biến môi trường PORT cấp.
Không cần thư viện ngoài — chỉ dùng thư viện chuẩn của Python.
"""
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

BASE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE, "web")
PORT = int(os.environ.get("PORT", "8080"))


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Không cache để cập nhật tool là thấy ngay
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass  # gọn log


def main():
    handler = partial(Handler, directory=WEB_DIR)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), handler)
    print(f"Ghép Ảnh Logo EyePlus đang chạy tại cổng {PORT} (thư mục: {WEB_DIR})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
