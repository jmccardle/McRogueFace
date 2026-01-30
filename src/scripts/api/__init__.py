"""McRogueFace Game-to-API Bridge

Exposes any McRogueFace game to external clients (LLMs, accessibility tools,
Twitch integrations, testing harnesses) via a background HTTP server.

Usage:
    # In game script or via --exec
    import api
    api.start_server(port=8765)

    # Or auto-starts on import if run via --exec
"""

from .server import GameAPIServer

__version__ = "0.1.0"
__all__ = ["start_server", "stop_server", "get_server"]

_server = None


def start_server(port: int = 8765) -> GameAPIServer:
    """Start the API server on the specified port.

    Args:
        port: HTTP port to listen on (default: 8765)

    Returns:
        The GameAPIServer instance
    """
    global _server
    if _server is None:
        _server = GameAPIServer(port)
        _server.start()
    return _server


def stop_server() -> None:
    """Stop the API server if running."""
    global _server
    if _server is not None:
        _server.stop()
        _server = None


def get_server() -> GameAPIServer:
    """Get the current server instance, or None if not running."""
    return _server


# Auto-start when imported via --exec
# Check if we're being imported as main script
import sys
if __name__ == "__main__" or (hasattr(sys, '_called_from_exec') and sys._called_from_exec):
    start_server()
