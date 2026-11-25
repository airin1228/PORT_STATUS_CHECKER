# 🔌 Port Status Checker

A small Python project that checks whether a TCP port on a given system is **open**, **closed** or **filtered**. It comes in two forms: a command-line script and a Flask web app. It is built to help you understand how systems communicate over networks.

## Features

- Checks any TCP port from 1 to 65535 on a hostname or IP address
- Three clear results: open, closed, filtered/unreachable
- Command-line tool with input validation, timeouts and meaningful exit codes
- Web interface with a JSON API
- Shows the common service name for a port (for example, 80 is http)
- Built on Python's standard library; only the web app needs Flask
- Web app blocks public targets by default, so it can't be used to probe the internet

## Project structure

```
port_checker_web/
├── app.py            # Flask web app (UI + /api/check endpoint)
├── port_checker.py   # Standalone command-line checker
├── requirements.txt  # Python dependencies (Flask)
└── README.md
```

## Requirements

- Python 3.8 or newer
- Flask (web app only)

## Installation

```bash
# optional: create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

The command-line script needs no installation at all.

## Usage

### Command line

```bash
python port_checker.py 80                          # check localhost
python port_checker.py 443 --host example.com      # check another host
python port_checker.py 22 --host 192.168.1.10 --timeout 3
python port_checker.py                             # prompts for the port
```

Example output:

```
Host:    127.0.0.1
Port:    80 (http)
Status:  OPEN
```

| Exit code | Meaning                                |
|-----------|----------------------------------------|
| 0         | Port is open                           |
| 1         | Port is closed or filtered/unreachable |
| 2         | Invalid input or host could not be resolved |

### Web app

```bash
python app.py
```

Open <http://127.0.0.1:5000>, enter a host and port, and press **Check port**.

### JSON API

```bash
curl -X POST http://127.0.0.1:5000/api/check \
  -H "Content-Type: application/json" \
  -d '{"host": "127.0.0.1", "port": 80}'
```

Response:

```json
{ "host": "127.0.0.1", "ip": "127.0.0.1", "port": 80, "service": "http", "status": "open" }
```

Errors return a JSON body with an `error` message and a 400 status (bad input or unresolved host) or 403 status (target not allowed).

## How it works

1. The hostname is resolved to an IP address using DNS.
2. A TCP socket is created with a short timeout.
3. `connect_ex()` attempts the TCP three-way handshake (SYN, SYN-ACK, ACK).
4. The return code is interpreted:

| Status       | What happened                                         | Typical cause                          |
|--------------|-------------------------------------------------------|----------------------------------------|
| **Open**     | Handshake completed                                   | A service is listening                 |
| **Closed**   | Host replied with a reset (RST)                       | Reachable, but nothing is listening    |
| **Filtered** | No reply before the timeout, or the network error     | Firewall dropping packets, host down   |

The "connection refused" error code differs by platform (111 on Linux, 61 on macOS, 10061 on Windows), and the code handles all three.

## Configuration

| Setting        | Where                     | Default     | Description                                              |
|----------------|---------------------------|-------------|----------------------------------------------------------|
| `--host`       | CLI                       | `127.0.0.1` | Target host                                              |
| `--timeout`    | CLI                       | `2.0`       | Seconds to wait for a response                           |
| `ALLOW_PUBLIC` | Environment variable (web) | unset       | Set to `1` to allow checking public (non-private) hosts  |

```bash
ALLOW_PUBLIC=1 python app.py     # Windows (PowerShell): $env:ALLOW_PUBLIC="1"; python app.py
```

## Security and responsible use

- Only check systems you **own or have written permission to test**. Unauthorized port scanning may violate network policies, terms of service or local law.
- By default the web app only accepts loopback and private-network targets. Enabling `ALLOW_PUBLIC` is your responsibility.
- The built-in Flask server is for development. If you expose the app to others, put it behind a production server (for example gunicorn), add authentication, and add rate limiting.

## Limitations

- TCP only (no UDP detection)
- One port per request
- "Filtered" can't distinguish a firewall from a host that is simply offline
- Results reflect the network path from the machine running the script, not from your own device

## Ideas for extending it

- Scan a range of ports and list only the open ones
- Use `concurrent.futures.ThreadPoolExecutor` to check many ports quickly
- Grab service banners with `recv()` after connecting
- Add UDP checks
- Inspect TLS certificates on port 443 with the `ssl` module
- Write tests that start a local server and assert it is reported as open

## License

No license has been chosen yet. Add a `LICENSE` file (for example MIT) before sharing the project publicly.
