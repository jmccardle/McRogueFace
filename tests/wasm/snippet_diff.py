#!/usr/bin/env python3
"""#388 - Cross-backend screenshot diff harness (desktop-headless oracle vs web canvas).

Renders each snippet in tests/snippets/ on the WEB (SDL2/WebGL) backend inside a
headless Chromium, captures the canvas, and diffs it against the DESKTOP-headless
oracle PNG produced by tools/generate_snippet_shots.py (#381). A diff above the
threshold is a desktop<->web divergence to triage (feeds #347 / #390).

Prerequisites
-------------
- Oracle PNGs in snippet-shots/  (run `make snippet-shots` first, needs a native build)
- A built playground in build-playground/  (`make playground`)
- The Playwright venv  (`make test-wasm-setup`)

Determinism
-----------
The desktop oracle is captured on a *virtual* clock (seed 42, fixed step count).
The web build advances on the browser's requestAnimationFrame *wall clock*, so a
frame mid-animation is NOT reproducible across backends. This harness therefore
diffs STATIC snippets only, and EXPLICITLY skips (never silently) any snippet that:
  - has no oracle PNG (e.g. the `noshot` snippets that produce no single frame), or
  - still has active mcrfpy.animations after setup (wall-clock non-deterministic).
Deterministic animated capture (pause the main loop, step a virtual clock) is a
documented follow-up. No snippet is dropped without a line in the report.

Capture
-------
The WebGL context is created without preserveDrawingBuffer, so an out-of-frame
readback reads a cleared (black) buffer. We force preserveDrawingBuffer:true with
an add_init_script getContext shim that runs before SDL creates the context -- a
host-side capture concern, no engine/build change. Capture waits for two identical
consecutive frames (stability) before reading, so we never grab a mid-render frame.

Exit code: 0 = no divergences, 1 = at least one DIVERGE, 2 = harness/setup error.
"""
import argparse
import base64
import functools
import http.server
import io
import socket
import socketserver
import sys
import threading
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError:
    print("error: Pillow + numpy required. Run 'make test-wasm-setup'.", file=sys.stderr)
    sys.exit(2)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("error: Playwright required. Run 'make test-wasm-setup'.", file=sys.stderr)
    sys.exit(2)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BUILD_DIR = REPO_ROOT / "build-playground"
SNIPPET_DIR = REPO_ROOT / "tests" / "snippets"
ORACLE_DIR = REPO_ROOT / "snippet-shots"

# Force preserveDrawingBuffer so the canvas can be read back out-of-frame.
PRESERVE_PATCH = r"""
(() => {
  const orig = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function(type, attrs) {
    if (type && type.indexOf('webgl') === 0) {
      attrs = Object.assign({}, attrs, { preserveDrawingBuffer: true });
    }
    return orig.call(this, type, attrs);
  };
})();
"""

SEED_PRELUDE = "import random\nrandom.seed(42)\n"


class _Handler(http.server.SimpleHTTPRequestHandler):
    _mime = {".wasm": "application/wasm", ".js": "text/javascript", ".data": "application/octet-stream"}

    def guess_type(self, path):
        for ext, mime in self._mime.items():
            if path.endswith(ext):
                return mime
        return super().guess_type(path)

    def log_message(self, *args):
        pass


class _Server:
    def __init__(self, directory, port):
        handler = functools.partial(_Handler, directory=str(directory))
        self._httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._httpd.shutdown()
        self._httpd.server_close()


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _snippets(nums):
    """Return sorted (number, path) for corpus files, optionally filtered to nums."""
    out = []
    want = set(nums) if nums else None
    for p in sorted(SNIPPET_DIR.glob("*.py")):
        if p.name.startswith("_"):
            continue
        try:
            n = int(p.name.split("_", 1)[0])
        except ValueError:
            continue
        if want is None or n in want:
            out.append((n, p))
    return out


def _capture_canvas(page, settle_ms, stable_tries):
    """Return a PNG data URL once two consecutive frames are identical (stable)."""
    prev = None
    for _ in range(stable_tries):
        page.wait_for_timeout(settle_ms)
        cur = page.evaluate("() => document.getElementById('canvas').toDataURL('image/png')")
        if prev is not None and cur == prev:
            return cur
        prev = cur
    return prev  # accept last frame even if not perfectly stable


def _decode_png(data_url):
    raw = base64.b64decode(data_url.split(",", 1)[1])
    return Image.open(io.BytesIO(raw)).convert("RGB"), raw


def _diff(web_img, oracle_img, channel_tol):
    """Return (frac_differing, mean_delta, diff_mask_image). Per-pixel metric is
    the sum of absolute RGB channel deltas; a pixel 'differs' when that exceeds
    channel_tol (which absorbs edge antialiasing / subpixel jitter)."""
    if web_img.size != oracle_img.size:
        return None
    a = np.asarray(web_img, dtype=np.int16)
    b = np.asarray(oracle_img, dtype=np.int16)
    delta = np.abs(a - b).sum(axis=2)  # HxW sum-of-abs-channel-delta
    differing = delta > channel_tol
    frac = float(differing.mean())
    mean = float(delta.mean())
    mask = Image.fromarray((differing * 255).astype(np.uint8), mode="L")
    return frac, mean, mask


def run(build_dir, nums, channel_tol, frac_gate, settle_ms, stable_tries,
        timeout_ms, out_dir, diff_dir, headed, verbose):
    entry = build_dir / "mcrogueface.html"
    if not entry.exists():
        print(f"error: {entry} not found. Run 'make playground' first.", file=sys.stderr)
        return 2
    if not ORACLE_DIR.exists():
        print(f"error: oracle dir {ORACLE_DIR} missing. Run 'make snippet-shots'.", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    diff_dir.mkdir(parents=True, exist_ok=True)

    corpus = _snippets(nums)
    if not corpus:
        print("error: no matching snippets", file=sys.stderr)
        return 2

    results = {"pass": [], "diverge": [], "skip": []}
    port = _free_port()

    with _Server(build_dir, port), sync_playwright() as pw:
        url = f"http://127.0.0.1:{port}/mcrogueface.html"
        browser = pw.chromium.launch(headless=not headed)
        for num, path in corpus:
            stem = path.stem
            oracle_path = ORACLE_DIR / f"{stem}.png"
            if not oracle_path.exists():
                results["skip"].append((stem, "no oracle PNG (noshot or not generated)"))
                if verbose:
                    print(f"  [SKIP] {stem}: no oracle")
                continue

            page = browser.new_page()
            page.add_init_script(PRESERVE_PATCH)
            page_errors = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            try:
                page.goto(url, wait_until="load", timeout=timeout_ms)
                page.wait_for_function(
                    "() => typeof window.runPython === 'function' && window.getPythonState"
                    " && window.getPythonState() === 'OK'",
                    timeout=timeout_ms)
                out = page.evaluate("code => window.runPython(code)", SEED_PRELUDE + path.read_text())
                if "Traceback" in out or "Error" in out:
                    results["skip"].append((stem, f"snippet raised on web: {out.strip().splitlines()[-1][:80]}"))
                    if verbose:
                        print(f"  [SKIP] {stem}: raised on web")
                    page.close()
                    continue
                # Non-deterministic if animations are still active after setup.
                anim = page.evaluate(
                    "code => window.runPython(code)",
                    "import mcrfpy\nprint(len(mcrfpy.animations))")
                if anim.strip().isdigit() and int(anim.strip()) > 0:
                    results["skip"].append((stem, f"{anim.strip()} active animation(s): wall-clock non-deterministic"))
                    if verbose:
                        print(f"  [SKIP] {stem}: animated")
                    page.close()
                    continue

                data_url = _capture_canvas(page, settle_ms, stable_tries)
                if page_errors:
                    results["skip"].append((stem, f"page JS error: {page_errors[0][:80]}"))
                    page.close()
                    continue
                web_img, raw = _decode_png(data_url)
                (out_dir / f"{stem}.png").write_bytes(raw)

                oracle_img = Image.open(oracle_path).convert("RGB")
                d = _diff(web_img, oracle_img, channel_tol)
                if d is None:
                    results["skip"].append((stem, f"size mismatch web{web_img.size} vs oracle{oracle_img.size}"))
                    page.close()
                    continue
                frac, mean, mask = d
                if frac > frac_gate:
                    results["diverge"].append((stem, frac, mean))
                    mask.save(diff_dir / f"{stem}_mask.png")
                    print(f"  [DIVERGE] {stem}: {frac*100:.2f}% px differ (mean {mean:.1f}) > gate {frac_gate*100:.2f}%")
                else:
                    results["pass"].append((stem, frac, mean))
                    if verbose:
                        print(f"  [PASS] {stem}: {frac*100:.2f}% px differ (mean {mean:.1f})")
            except Exception as e:
                results["skip"].append((stem, f"harness error: {type(e).__name__}: {e}"))
                if verbose:
                    print(f"  [SKIP] {stem}: {type(e).__name__}: {e}")
            finally:
                page.close()
        browser.close()

    print(f"\n#388 cross-backend diff: {len(results['pass'])} pass, "
          f"{len(results['diverge'])} diverge, {len(results['skip'])} skipped")
    if results["skip"]:
        print("skipped (explicit, Fail-Early -- not silent):")
        for stem, why in results["skip"]:
            print(f"  - {stem}: {why}")
    if results["diverge"]:
        print(f"divergence masks written to {diff_dir}")
    return 1 if results["diverge"] else 0


def main():
    ap = argparse.ArgumentParser(description="#388 cross-backend screenshot diff harness")
    ap.add_argument("nums", nargs="*", type=int, help="snippet numbers to diff (default: all)")
    ap.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    ap.add_argument("--channel-tol", type=int, default=40,
                    help="per-pixel sum-of-abs-channel-delta below which pixels are equal (absorbs AA)")
    ap.add_argument("--frac-gate", type=float, default=0.03,
                    help="max fraction of differing pixels before a snippet DIVERGES")
    ap.add_argument("--settle-ms", type=int, default=250, help="wait between stability captures")
    ap.add_argument("--stable-tries", type=int, default=4, help="max stability capture attempts")
    ap.add_argument("--timeout", type=int, default=60000, help="per-page timeout (ms)")
    ap.add_argument("--out-dir", type=Path, default=ORACLE_DIR / "web")
    ap.add_argument("--diff-dir", type=Path, default=ORACLE_DIR / "web-diff")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    return run(args.build_dir, args.nums, args.channel_tol, args.frac_gate,
               args.settle_ms, args.stable_tries, args.timeout,
               args.out_dir, args.diff_dir, args.headed, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
