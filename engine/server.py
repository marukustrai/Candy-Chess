"""A tiny stdlib HTTP server that exposes the JSON facade.

Start it from the repo root:

    python -m engine.server
    python -m engine.server --port 8765

Endpoints (all bodies are JSON):

    POST /games              start a new Phase 1 game
    POST /games/fen          body: {"fen": "..."}  start from a FEN
    GET  /games/<id>         current board state
    GET  /games/<id>/moves   all legal moves (optional ?square=e2)
    POST /games/<id>/moves   body: {"move": "e2e4"}  apply a move

Illegal moves return HTTP 400 with {"ok": false, "error": "...", "message": "..."}.
This is an API, not a visual UI, and there is no computer opponent.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from engine.api import ChessAPI

api = ChessAPI()


def _json_bytes(payload: object) -> bytes:
    return json.dumps(payload, indent=2).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        # Keep the demo quiet-ish; still print a one-line request log.
        sys_stderr_write = super().log_message
        sys_stderr_write(format, *args)

    def _send(self, code: int, payload: object) -> None:
        body = _json_bytes(payload)
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(200, {"ok": True})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        query = parse_qs(parsed.query)
        try:
            if parts == ["games"] or parts == ["health"]:
                if parts == ["health"]:
                    self._send(200, {"ok": True, "phase": 1})
                    return
                self._send(200, {"ok": True, "games": list(api._games)})
                return
            if len(parts) == 2 and parts[0] == "games":
                self._send(200, api.get(parts[1]))
                return
            if len(parts) == 3 and parts[0] == "games" and parts[2] == "moves":
                square = query.get("square", [None])[0]
                self._send(200, api.legal_moves(parts[1], square))
                return
        except KeyError as exc:
            self._send(404, {"ok": False, "error": "not_found", "message": str(exc)})
            return
        except ValueError as exc:
            self._send(400, {"ok": False, "error": "bad_request", "message": str(exc)})
            return
        self._send(404, {"ok": False, "error": "not_found", "message": f"No route for {self.path}"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(body, dict):
                raise ValueError("JSON body must be an object")
        except (ValueError, UnicodeDecodeError) as exc:
            self._send(400, {"ok": False, "error": "bad_request", "message": f"Invalid JSON: {exc}"})
            return

        try:
            if parts == ["games"]:
                self._send(201, api.new_game())
                return
            if parts == ["games", "fen"]:
                fen = body.get("fen")
                if not fen or not isinstance(fen, str):
                    raise ValueError("Missing 'fen' string")
                self._send(201, api.from_fen(fen))
                return
            if len(parts) == 3 and parts[0] == "games" and parts[2] == "moves":
                move = body.get("move")
                if not move or not isinstance(move, str):
                    raise ValueError("Missing 'move' string")
                result = api.apply(parts[1], move)
                code = 200 if result.get("ok") else 400
                self._send(code, result)
                return
        except KeyError as exc:
            self._send(404, {"ok": False, "error": "not_found", "message": str(exc)})
            return
        except ValueError as exc:
            self._send(400, {"ok": False, "error": "bad_request", "message": str(exc)})
            return
        self._send(404, {"ok": False, "error": "not_found", "message": f"No route for {self.path}"})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Candy Chess Phase 1 JSON HTTP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Candy Chess engine listening on http://{args.host}:{args.port}")
    print("POST /games  — start a Phase 1 game")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
