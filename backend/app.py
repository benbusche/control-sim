"""Serve the frontend and simulation API on localhost."""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from pathlib import Path
import threading
import time

from .session import SimulationSession, TIME_STEP


FRONTEND = Path(__file__).resolve().parent.parent / "frontend"
session = SimulationSession()


class RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND), **kwargs)

    def log_message(self, format, *args):
        if self.path not in ("/api/state", "/api/control"):
            super().log_message(format, *args)

    def send_json(self, value, status=200):
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/state":
            self.send_json(session.snapshot())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != "/api/control":
            self.send_json({"error": "Not found"}, status=404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("Request body must be between 1 and 4096 bytes")
            command = json.loads(self.rfile.read(length))
            session.handle_command(command)
        except ValueError as error:
            self.send_json({"error": str(error)}, status=400)
            return

        self.send_json(session.snapshot())


def run_simulation():
    while True:
        started = time.monotonic()
        session.advance(TIME_STEP)
        time.sleep(max(0, TIME_STEP - (time.monotonic() - started)))


def main():
    threading.Thread(target=run_simulation, daemon=True).start()
    server = HTTPServer(("127.0.0.1", 8000), RequestHandler)
    print("Open http://127.0.0.1:8000 in your browser")
    server.serve_forever()


if __name__ == "__main__":
    main()
