"""Local preview server for the site.

    python tools/serve.py        then open http://localhost:5173

It serves the web/ folder like any static server. It also has one extra trick
for review pictures: a page can send a picture of its canvas to /__shot?name=xyz
and it is saved as previews/browser_xyz.jpg. Only this machine can reach it.
"""
import os
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
# a port given on the command line wins, then $PORT (preview tools set it), then 5173
PORT = int(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PORT") or 5173)


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")      # always show the latest export while working
        super().end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        name = parse_qs(url.query).get("name", [""])[0]
        length = int(self.headers.get("Content-Length", 0))
        if url.path != "/__shot" or not re.fullmatch(r"[a-z0-9_]{1,40}", name) or not 0 < length < 20_000_000:
            self.send_error(400)
            return
        data = self.rfile.read(length)
        if data[:2] != b"\xff\xd8":                         # JPEG files start with these two bytes
            self.send_error(400)
            return
        out = ROOT / "previews"
        out.mkdir(exist_ok=True)
        (out / f"browser_{name}.jpg").write_bytes(data)
        self.send_response(204)
        self.end_headers()

    def log_message(self, fmt, *args):
        if "404" in (args[1] if len(args) > 1 else ""):
            super().log_message(fmt, *args)


if __name__ == "__main__":
    handler = partial(Handler, directory=str(ROOT / "web"))
    print(f"Serving web/ at http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), handler).serve_forever()
