"""LanguageTool-compatible HTTP server for Globasa grammar checking.

Exposes POST /v2/check — compatible with language_tool_python and LTeX+.

Usage:
    python -m GlobasaGrammarChecker.server [--port 8081]
"""
import json
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

from .checker import GrammarChecker

checker = GrammarChecker()


class LTHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/v2/check":
            self.send_error(404)
            return
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        params = parse_qs(body)
        text = params.get("text", [""])[0]
        language = params.get("language", ["glb"])[0]

        result = checker.check_to_lt_json(text, language)

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress default logging


def main():
    parser = argparse.ArgumentParser(description="Globasa grammar checker server")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), LTHandler)
    print(f"Globasa grammar checker listening on http://{args.host}:{args.port}/v2/check")
    server.serve_forever()


if __name__ == "__main__":
    main()
