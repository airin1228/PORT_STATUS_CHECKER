"""Port Status Checker: web version (Flask)

Run:
    pip install flask
    python app.py
Then open http://127.0.0.1:5000

By default only loopback and private-network hosts can be checked, so the app
can't be used to probe the public internet. Set ALLOW_PUBLIC=1 to lift that
(only do so on systems you are authorized to test).
"""

import ipaddress
import os
import socket

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
ALLOW_PUBLIC = os.environ.get("ALLOW_PUBLIC") == "1"


def check_port(ip: str, port: int, timeout: float = 2.0) -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            code = s.connect_ex((ip, port))
        except OSError:
            return "filtered"
    if code == 0:
        return "open"
    if code in (111, 61, 10061):  # refused: Linux, macOS, Windows
        return "closed"
    return "filtered"


@app.post("/api/check")
def api_check():
    data = request.get_json(silent=True) or {}
    host = str(data.get("host") or "127.0.0.1").strip()
    try:
        port = int(data.get("port"))
        if not 1 <= port <= 65535:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify(error="Port must be a whole number from 1 to 65535."), 400
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        return jsonify(error=f"Could not resolve host '{host}'."), 400

    addr = ipaddress.ip_address(ip)
    if not ALLOW_PUBLIC and not (addr.is_loopback or addr.is_private):
        return jsonify(error="Only localhost and private-network hosts are allowed on this server."), 403

    try:
        service = socket.getservbyport(port, "tcp")
    except OSError:
        service = "unknown"
    return jsonify(host=host, ip=ip, port=port, service=service, status=check_port(ip, port))


PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Port Status Checker</title>
<style>
:root{--bg:#f4f7fc;--card:#fff;--text:#16203a;--muted:#5b6885;--accent:#2f6fed;--border:#d9e0ee;--ok:#12a37f;--bad:#d64550;--warn:#d9822b}
@media(prefers-color-scheme:dark){:root{--bg:#0b1020;--card:#131a30;--text:#e8edfb;--muted:#9aa7c7;--accent:#6c9bff;--border:#26315a}}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:20px;background:var(--bg);color:var(--text);font:16px/1.6 system-ui,sans-serif}
.card{width:100%;max-width:460px;background:var(--card);border:1px solid var(--border);border-radius:20px;padding:28px;box-shadow:0 10px 40px rgba(0,0,0,.12)}
h1{margin:0 0 4px;font-size:1.6rem}p{margin:0 0 20px;color:var(--muted)}
label{display:block;font-size:.85rem;font-weight:600;margin:14px 0 6px}
input{width:100%;padding:12px 14px;border-radius:12px;border:1px solid var(--border);background:transparent;color:var(--text);font-size:1rem}
button{width:100%;margin-top:20px;padding:13px;border:0;border-radius:12px;background:var(--accent);color:#fff;font-size:1rem;font-weight:700;cursor:pointer}
#result{margin-top:20px;padding:16px;border-radius:12px;border:1px solid var(--border);display:none}
.status{font-size:1.4rem;font-weight:800}.open{color:var(--ok)}.closed{color:var(--bad)}.filtered{color:var(--warn)}
small{color:var(--muted)}
</style></head><body>
<div class="card">
<h1>&#128268; Port Status Checker</h1>
<p>Check whether a TCP port is open or closed.</p>
<label for="host">Host</label><input id="host" value="127.0.0.1">
<label for="port">Port number</label><input id="port" type="number" min="1" max="65535" placeholder="e.g. 80">
<button id="go">Check port</button>
<div id="result"></div>
<p style="margin-top:18px"><small>Open = a service accepted the connection. Closed = host refused it. Filtered = no reply (firewall or host down).</small></p>
</div>
<script>
const $ = id => document.getElementById(id);
async function run() {
  const r = $("result"); r.style.display = "block"; r.textContent = "Checking...";
  try {
    const res = await fetch("/api/check", {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({host: $("host").value, port: $("port").value})});
    const d = await res.json();
    if (!res.ok) { r.textContent = d.error; return; }
    r.innerHTML = '<div class="status ' + d.status + '">' + d.status.toUpperCase() + '</div>' +
      '<div>' + d.host + ' (' + d.ip + ') &middot; port ' + d.port + ' &middot; ' + d.service + '</div>';
  } catch (e) { r.textContent = "Request failed. Is the server running?"; }
}
$("go").onclick = run;
$("port").onkeydown = e => { if (e.key === "Enter") run(); };
</script></body></html>"""


@app.get("/")
def index():
    return render_template_string(PAGE)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
