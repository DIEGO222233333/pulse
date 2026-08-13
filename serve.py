#!/usr/bin/env python3
"""Mini-serveur local PULSE (port 8942) — interdit le cache navigateur
pour que chaque rechargement serve toujours la dernière version."""
import http.server, functools, os

PORT = 8942
ROOT = os.path.dirname(os.path.abspath(__file__))

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Expires", "0")
        super().end_headers()
    def log_message(self, *a):  # silencieux
        pass

if __name__ == "__main__":
    handler = functools.partial(NoCacheHandler, directory=ROOT)
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler) as srv:
        srv.serve_forever()
