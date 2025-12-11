import time
import socketio
from settings import MINDSERVER_HOST, MINDSERVER_PORT


class MindServerClient:
    def __init__(self):
        self.sio = socketio.Client(
            logger=False,
            engineio_logger=False
        )

        self.agents = []
        self.connected = False

        @self.sio.event
        def connect():
            self.connected = True
            print("[MindServer] ✅ Connected")
            # request agent list immediately
            self.sio.emit("listen-to-agents")

        @self.sio.event
        def disconnect():
            self.connected = False
            print("[MindServer] ❌ Disconnected")

        @self.sio.on("agents-status")
        def on_agents_status(data):
            self.agents = data or []
            names = [a.get("name") for a in self.agents]
            print("[MindServer] agents-status:", names)

    # --------------------------------------------------
    # Connection helpers
    # --------------------------------------------------

    def connect(self, wait_for_agents=True, timeout=5.0):
        url = f"http://{MINDSERVER_HOST}:{MINDSERVER_PORT}"
        self.sio.connect(url)

        if wait_for_agents:
            self._wait_for_agents(timeout)

    def _wait_for_agents(self, timeout):
        waited = 0.0
        step = 0.1
        while waited < timeout:
            if self.get_available_agents():
                return
            time.sleep(step)
            waited += step
        print("[MindServer] ⚠️ No agents became available")

    # --------------------------------------------------
    # Agent utilities
    # --------------------------------------------------

    def get_available_agents(self):
        """
        Only return agents that are actually safe to message.
        """
        return [
            a["name"]
            for a in self.agents
            if a.get("socket_connected") and a.get("in_game")
        ]

    # --------------------------------------------------
    # Messaging
    # --------------------------------------------------

    def send_transcript(self, speaker, text, target_agent=None):
        agents = self.get_available_agents()
        if not agents:
            print("[MindServer] ⚠️ No connected agents to send to")
            return

        agent = target_agent or agents[0]

        payload = {
            # ✅ REQUIRED by agent
            "from": speaker,
            "message": text,

            # ✅ Optional metadata (safe)
            "type": "transcript",
        }

        self.sio.emit(
            "send-message",
            {
                "agent": agent,
                "data": payload,
            }
        )

        print(f"[MindServer] 📤 Sent -> {agent}: {payload}")


    # --------------------------------------------------
    # Cleanup
    # --------------------------------------------------

    def disconnect(self):
        if self.sio.connected:
            self.sio.disconnect()
