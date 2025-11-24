# Python Socket.IO client for MindServer

This folder contains a small example Python client that connects to the MindServer (the Socket.IO server in this repo).

Files:
- `settings.py` — mirror of `settings.js` values (connection details and defaults). You can edit or override via environment variables.
- `python_client.py` — simple Socket.IO client that connects, listens for `agents-status`, `bot-output`, and demonstrates `create-agent`.

Requirements
-----------
- Python 3.8+
- Install the Socket.IO client package:

```bash
pip install "python-socketio[client]"
```

Running the example
-------------------
1. Ensure the MindServer is running (typically `localhost:8080` by default). See the project `settings.js` and `main.js` for how the server is started.

2. Optionally override connection details by setting environment variables:

```bash
export MINDSERVER_HOST=localhost
export MINDSERVER_PORT=8080
```

3. Run the client:

```bash
python examples/python_client/python_client.py
```

What it does
-------------
- Connects to the MindServer using the host/port from `settings.py` (or environment overrides).
- Prints `agents-status`, `bot-output`, and `state-update` messages it receives.
- Emits a `create-agent` event (with a callback/ack) as a demonstration — adjust `python_client.py` to use a real profile/settings for a working agent.

Notes
-----
- `python_client.py` is meant as a minimal example. The MindServer expects agent settings that conform to `src/mindcraft/public/settings_spec.json` — if you want to programmatically create working agents, review that file to populate required keys.
- If you encounter `Import "socketio" could not be resolved` in your editor, install the dependency in your Python environment as shown above.

If you want, I can:
- Add a more complete example that reads one of the repo's JSON profiles and uses it for `create-agent`.
- Run a quick syntax check or attempt a connection in this environment (if you start the MindServer here first).
