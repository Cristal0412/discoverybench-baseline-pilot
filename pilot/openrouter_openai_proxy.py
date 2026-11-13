"""
Tiny local reverse proxy so Inspect's native "openai" provider (which the
discoverybench task's own internal LLM-judge scorer uses directly, via
get_model(f"openai/{model}") with model="gpt-4o-2024-08-06") can be pointed
at OpenRouter without any monkey-patching or editing installed packages.

Problem: when OPENAI_BASE_URL is pointed straight at OpenRouter, Inspect's
openai provider sends the bare model string "gpt-4o-2024-08-06" (the real
OpenAI model ID -- Inspect only uses the "openai/" prefix for its own CLI
provider routing, not in the request body). OpenRouter's catalog requires
the provider-prefixed ID "openai/gpt-4o-2024-08-06" instead and rejects
the bare name.

Fix: run this proxy on localhost, point OPENAI_BASE_URL at it instead of
OpenRouter directly. It rewrites any "model" field that has no "/" in it
by prefixing "openai/", forwards everything else unchanged to OpenRouter
using the real OPENROUTER_API_KEY (read from the environment this proxy
itself was started with -- the client's own Authorization header, even a
placeholder, is ignored), and streams the response straight back.

Usage:
  OPENROUTER_API_KEY=... python3 openrouter_openai_proxy.py [port]
  # then: OPENAI_BASE_URL=http://127.0.0.1:<port>/v1 OPENAI_API_KEY=unused ...
"""

import http.server
import json
import os
import sys
import urllib.error
import urllib.request

UPSTREAM = "https://openrouter.ai/api/v1"
API_KEY = os.environ["OPENROUTER_API_KEY"]


class Handler(http.server.BaseHTTPRequestHandler):
    def _proxy(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""

        if body:
            try:
                payload = json.loads(body)
                model = payload.get("model")
                if isinstance(model, str) and "/" not in model:
                    payload["model"] = f"openai/{model}"
                    body = json.dumps(payload).encode()
            except (json.JSONDecodeError, AttributeError):
                pass

        url = UPSTREAM + self.path
        req = urllib.request.Request(url, data=body, method=self.command)
        for k, v in self.headers.items():
            if k.lower() in ("host", "content-length", "authorization"):
                continue
            req.add_header(k, v)
        req.add_header("Authorization", f"Bearer {API_KEY}")
        if body:
            req.add_header("Content-Length", str(len(body)))

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() in ("transfer-encoding", "connection"):
                        continue
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            err_body = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)

    def do_POST(self):
        self._proxy()

    def do_GET(self):
        self._proxy()

    def log_message(self, fmt, *args):
        sys.stderr.write("[proxy] " + (fmt % args) + "\n")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"READY on 127.0.0.1:{port}", flush=True)
    server.serve_forever()
