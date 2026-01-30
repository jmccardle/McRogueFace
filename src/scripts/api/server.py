"""HTTP server for the McRogueFace Game API.

Runs in a background daemon thread and provides REST endpoints for
scene introspection, affordance analysis, and input injection.
"""

import json
import threading
import hashlib
import time
import tempfile
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional

import mcrfpy

from .introspection import serialize_scene, get_scene_hash
from .affordances import extract_affordances, extract_keyboard_hints
from .input_handler import execute_action
from .metadata import get_game_metadata, set_game_metadata


class GameAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the game API."""

    # Class-level reference to server for metadata access
    api_server = None

    def log_message(self, format, *args):
        """Override to use custom logging instead of stderr."""
        # Enable for debugging
        print(f"[API] {format % args}", flush=True)

    def log_error(self, format, *args):
        """Log errors."""
        print(f"[API ERROR] {format % args}", flush=True)

    def send_json(self, data: Dict[str, Any], status: int = 200) -> None:
        """Send a JSON response."""
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: int = 400) -> None:
        """Send a JSON error response."""
        self.send_json({"error": message}, status)

    def send_file(self, filepath: str, content_type: str = 'application/octet-stream') -> None:
        """Send a file as response."""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(data))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_error_json("File not found", 404)

    def parse_json_body(self) -> Optional[Dict[str, Any]]:
        """Parse JSON body from request."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                return {}
            body = self.rfile.read(content_length)
            return json.loads(body.decode('utf-8'))
        except (json.JSONDecodeError, ValueError) as e:
            return None

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query)

            if path == '/scene':
                self.handle_scene()
            elif path == '/affordances':
                self.handle_affordances()
            elif path == '/screenshot':
                self.handle_screenshot(query)
            elif path == '/metadata':
                self.handle_metadata()
            elif path == '/wait':
                self.handle_wait(query)
            elif path == '/health':
                self.handle_health()
            elif path == '/':
                self.handle_health()  # Root path also returns health
            else:
                self.send_error_json("Unknown endpoint", 404)
        except Exception as e:
            print(f"[API] Error in do_GET: {e}", flush=True)
            import traceback
            traceback.print_exc()
            try:
                self.send_error_json(f"Internal error: {str(e)}", 500)
            except Exception:
                pass

    def do_POST(self):
        """Handle POST requests."""
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            if path == '/input':
                self.handle_input()
            elif path == '/metadata':
                self.handle_set_metadata()
            else:
                self.send_error_json("Unknown endpoint", 404)
        except Exception as e:
            print(f"[API] Error in do_POST: {e}", flush=True)
            import traceback
            traceback.print_exc()
            try:
                self.send_error_json(f"Internal error: {str(e)}", 500)
            except Exception:
                pass

    def handle_health(self) -> None:
        """Health check endpoint."""
        self.send_json({
            "status": "ok",
            "version": "0.1.0",
            "timestamp": time.time()
        })

    def handle_scene(self) -> None:
        """Return the current scene graph with semantic annotations."""
        try:
            # Try to use lock for thread safety, but fall back if not available
            try:
                with mcrfpy.lock():
                    scene_data = serialize_scene()
            except (RuntimeError, AttributeError):
                # Lock not available (e.g., main thread or headless mode issue)
                scene_data = serialize_scene()
            self.send_json(scene_data)
        except Exception as e:
            self.send_error_json(f"Scene introspection failed: {str(e)}", 500)

    def handle_affordances(self) -> None:
        """Return only interactive elements with their semantic labels."""
        try:
            # Try to use lock for thread safety
            try:
                with mcrfpy.lock():
                    scene = mcrfpy.current_scene
                    scene_name = scene.name if scene else "unknown"
                    affordances = extract_affordances()
                    keyboard_hints = extract_keyboard_hints()
            except (RuntimeError, AttributeError):
                scene = mcrfpy.current_scene
                scene_name = scene.name if scene else "unknown"
                affordances = extract_affordances()
                keyboard_hints = extract_keyboard_hints()

            self.send_json({
                "scene_name": scene_name,
                "affordances": affordances,
                "keyboard_hints": keyboard_hints,
                "timestamp": time.time()
            })
        except Exception as e:
            self.send_error_json(f"Affordance extraction failed: {str(e)}", 500)

    def handle_screenshot(self, query: Dict) -> None:
        """Return a PNG screenshot."""
        try:
            # Create temp file for screenshot
            fd, filepath = tempfile.mkstemp(suffix='.png')
            os.close(fd)

            # Take screenshot (may or may not need lock depending on mode)
            try:
                with mcrfpy.lock():
                    mcrfpy.automation.screenshot(filepath)
            except (RuntimeError, AttributeError):
                mcrfpy.automation.screenshot(filepath)

            # Check format preference
            format_type = query.get('format', ['binary'])[0]

            if format_type == 'base64':
                import base64
                with open(filepath, 'rb') as f:
                    data = f.read()
                b64 = base64.b64encode(data).decode('ascii')
                os.unlink(filepath)
                self.send_json({
                    "image": f"data:image/png;base64,{b64}",
                    "timestamp": time.time()
                })
            else:
                self.send_file(filepath, 'image/png')
                os.unlink(filepath)

        except Exception as e:
            self.send_error_json(f"Screenshot failed: {str(e)}", 500)

    def handle_metadata(self) -> None:
        """Return game metadata."""
        metadata = get_game_metadata()
        self.send_json(metadata)

    def handle_set_metadata(self) -> None:
        """Update game metadata."""
        data = self.parse_json_body()
        if data is None:
            self.send_error_json("Invalid JSON body")
            return

        set_game_metadata(data)
        self.send_json({"success": True})

    def handle_wait(self, query: Dict) -> None:
        """Long-poll endpoint that returns when scene state changes."""
        timeout = float(query.get('timeout', [30])[0])
        previous_hash = query.get('scene_hash', [None])[0]

        start_time = time.time()
        poll_interval = 0.1  # 100ms

        current_hash = None
        scene_name = "unknown"

        while time.time() - start_time < timeout:
            try:
                with mcrfpy.lock():
                    current_hash = get_scene_hash()
                    scene = mcrfpy.current_scene
                    scene_name = scene.name if scene else "unknown"
            except (RuntimeError, AttributeError):
                current_hash = get_scene_hash()
                scene = mcrfpy.current_scene
                scene_name = scene.name if scene else "unknown"

            if previous_hash is None:
                # First call - return current state
                self.send_json({
                    "changed": False,
                    "hash": current_hash,
                    "scene_name": scene_name
                })
                return

            if current_hash != previous_hash:
                self.send_json({
                    "changed": True,
                    "new_hash": current_hash,
                    "old_hash": previous_hash,
                    "scene_name": scene_name,
                    "reason": "state_change"
                })
                return

            time.sleep(poll_interval)

        # Timeout - no change
        self.send_json({
            "changed": False,
            "hash": current_hash,
            "scene_name": scene_name
        })

    def handle_input(self) -> None:
        """Inject keyboard or mouse input."""
        data = self.parse_json_body()
        if data is None:
            self.send_error_json("Invalid JSON body")
            return

        if 'action' not in data:
            self.send_error_json("Missing 'action' field")
            return

        try:
            result = execute_action(data)
            self.send_json(result)
        except ValueError as e:
            self.send_error_json(str(e), 400)
        except Exception as e:
            self.send_error_json(f"Input action failed: {str(e)}", 500)


class GameAPIServer:
    """Background HTTP server for the game API."""

    def __init__(self, port: int = 8765):
        self.port = port
        self.server = None
        self.thread = None
        self._running = False

    def start(self) -> None:
        """Start the server in a background thread."""
        if self._running:
            return

        GameAPIHandler.api_server = self

        # Allow socket reuse to avoid "Address already in use" errors
        import socket
        class ReuseHTTPServer(HTTPServer):
            allow_reuse_address = True

        self.server = ReuseHTTPServer(('localhost', self.port), GameAPIHandler)
        self.server.timeout = 1.0  # Don't block forever on handle_request
        self._running = True

        self.thread = threading.Thread(
            target=self._serve_forever,
            daemon=True,
            name="GameAPI"
        )
        self.thread.start()
        print(f"[API] Game API running on http://localhost:{self.port}", flush=True)

    def _serve_forever(self) -> None:
        """Server loop (runs in background thread)."""
        try:
            while self._running:
                try:
                    self.server.handle_request()
                except Exception as e:
                    if self._running:  # Only log if we're still supposed to be running
                        print(f"[API] Request handling error: {e}", flush=True)
        except Exception as e:
            print(f"[API] Server thread error: {e}", flush=True)

    def stop(self) -> None:
        """Stop the server."""
        if not self._running:
            return

        self._running = False
        # Send a dummy request to unblock handle_request
        try:
            import urllib.request
            urllib.request.urlopen(f"http://localhost:{self.port}/health", timeout=0.5)
        except Exception:
            pass
        if self.thread:
            self.thread.join(timeout=2.0)
        if self.server:
            self.server.server_close()
        print("[API] Game API stopped", flush=True)

    @property
    def is_running(self) -> bool:
        return self._running
