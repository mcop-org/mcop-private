# Local App Launcher

The advanced UI can now be launched with one command from the repo root:

```bash
python3 scripts/run_app.py
```

What it does:

1. Starts the local backend on `http://127.0.0.1:8765`
2. Starts the Vite frontend on `http://127.0.0.1:5173`
3. Waits for both services to be reachable
4. Opens the browser automatically

Useful options:

```bash
python3 scripts/run_app.py --no-browser
python3 scripts/run_app.py --timeout 45
```

Shutdown:

- Press `Ctrl+C` in the launcher terminal to stop both child processes cleanly.
- If port `8765` or `5173` is already in use, the launcher exits early instead of trying to attach to an existing process.

This launcher is local-only and is intended as the bridge to a later packaged-app flow without changing the current service or frontend architecture.
