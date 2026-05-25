import datetime
import hashlib
import http.server
import io
import os
import pathlib
import socketserver
import subprocess
import sys
import threading
import zipfile


ROOT = pathlib.Path(__file__).resolve().parent.parent
CHALLENGE_DIR = ROOT / "challenge"
DOWNLOAD_NAME = "myDataLeak-Revenge.zip"
GENERATOR_PATH = ROOT / "writeup_internal" / "generate_challenge.py"
PUBLIC_FILES = {
    "README.txt",
    "cleaned_students.csv",
    "cleaner.py",
    "raw_sys_a.csv",
    "raw_sys_b.csv",
    "raw_sys_c.json",
    "rules.yaml",
}

_GEN_LOCK = threading.Lock()
_LAST_GENERATED_AT = "not generated yet"
_LAST_SHA256 = "n/a"
_TOTAL_GENERATIONS = 0


def resolve_flag():
    return (
        os.environ.get("GZCTF_FLAG")
        or os.environ.get("DYNAMIC_FLAG")
        or os.environ.get("FLAG")
        or "flag{etl_retry_poisoning_leaks_shards}"
    )


def _run_generator():
    env = os.environ.copy()
    flag = resolve_flag()
    env["GZCTF_FLAG"] = flag
    env["DYNAMIC_FLAG"] = flag
    env["FLAG"] = flag
    subprocess.run([sys.executable, str(GENERATOR_PATH)], cwd=str(ROOT), env=env, check=True)


def _build_zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(CHALLENGE_DIR.rglob("*")):
            if file_path.is_file() and file_path.name in PUBLIC_FILES:
                zf.write(file_path, arcname=file_path.relative_to(CHALLENGE_DIR.parent))
    return buf.getvalue()


def generate_zip():
    global _LAST_GENERATED_AT, _LAST_SHA256, _TOTAL_GENERATIONS
    with _GEN_LOCK:
        _run_generator()
        payload = _build_zip_bytes()
        _TOTAL_GENERATIONS += 1
        _LAST_GENERATED_AT = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        _LAST_SHA256 = hashlib.sha256(payload).hexdigest()
    return payload


def render_index():
    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
  <title>myDataLeak-Revenge dynamic container</title>
  <style>
    :root {{
      --bg-1: #f7fafc;
      --bg-2: #e2e8f0;
      --text: #102a43;
      --btn: #0f766e;
      --btn-hover: #115e59;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      font-family: \"Segoe UI\", \"PingFang SC\", \"Microsoft YaHei\", sans-serif;
      background: radial-gradient(1000px 500px at -10% -10%, #dbeafe, transparent), linear-gradient(150deg, var(--bg-1), var(--bg-2));
      display: grid;
      place-items: center;
      padding: 20px;
    }}
    main {{
      width: min(740px, 100%);
      background: rgba(255,255,255,0.92);
      border: 1px solid #d9e2ec;
      border-radius: 18px;
      padding: 28px;
      box-shadow: 0 16px 36px rgba(16, 42, 67, 0.08);
    }}
    h1 {{ margin-top: 0; font-size: 1.75rem; }}
    p {{ line-height: 1.7; }}
    code {{ background: #f0f4f8; padding: 2px 6px; border-radius: 6px; }}
    .stats {{
      margin: 18px 0;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", monospace;
      background: #f8fafc;
      border: 1px solid #cbd5e1;
      border-radius: 12px;
      padding: 12px;
      overflow: auto;
    }}
    .download-btn {{
      appearance: none;
      border: 0;
      border-radius: 12px;
      font-size: 1rem;
      font-weight: 700;
      color: white;
      background: var(--btn);
      padding: 12px 16px;
      cursor: pointer;
    }}
    .download-btn:hover {{ background: var(--btn-hover); }}
  </style>
</head>
<body>
  <main>
    <h1>myDataLeak-Revenge dynamic container</h1>
    <p>Click to generate the hard-version package with <code>GZCTF_FLAG</code> and download a fresh ZIP.</p>
    <form method=\"POST\" action=\"/download\">
      <button class=\"download-btn\" type=\"submit\">Generate and Download ZIP</button>
    </form>
    <div class=\"stats\">
      total generations: {_TOTAL_GENERATIONS}<br>
      last generated at: {_LAST_GENERATED_AT}<br>
      last zip sha256: {_LAST_SHA256}
    </div>
    <p>Downloaded files exclude <code>inject_flag.py</code>, <code>verify.py</code>, and <code>retry.log</code>.</p>
  </main>
</body>
</html>
"""


class DynamicChallengeHandler(http.server.BaseHTTPRequestHandler):
    server_version = "myDataLeakDynamic/1.0"

    def _send_index(self):
        body = render_index().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_zip(self):
        try:
            payload = generate_zip()
        except Exception as exc:
            message = f"generation failed: {exc}\n".encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)
            return

        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", f'attachment; filename="{DOWNLOAD_NAME}"')
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send_index()
            return
        if self.path == "/download":
            self._send_zip()
            return
        self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/download":
            _ = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            self._send_zip()
            return
        self.send_error(404, "Not Found")

    def log_message(self, fmt, *args):
        message = fmt % args
        print(f"[{self.log_date_time_string()}] {self.client_address[0]} {message}")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    generate_zip()
    port = int(os.environ.get("APP_PORT", "8000"))
    with ThreadedHTTPServer(("0.0.0.0", port), DynamicChallengeHandler) as httpd:
        print(f"[+] Dynamic challenge server started on 0.0.0.0:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
