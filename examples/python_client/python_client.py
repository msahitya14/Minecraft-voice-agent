"""
Simple Python Socket.IO client for MindServer.
Reads connection details from `settings.py` in the same directory.

Installs: pip install "python-socketio[client]"

This script connects to the MindServer, prints `agents-status` updates and `bot-output` events,
and demonstrates emitting `create-agent` with an acknowledgement callback.
"""
import time
import logging
import socketio
import argparse
import json
from settings import MINDSERVER_HOST, MINDSERVER_PORT, DEFAULT_PROFILE_PATHS, DEFAULT_INIT_MESSAGE

logging.basicConfig(level=logging.INFO)

sio = None
try:
    # python-socketio exposes a Client() class
    if not hasattr(socketio, 'Client'):
        raise AttributeError('installed socketio package does not provide Client')
    sio = socketio.Client(logger=False, engineio_logger=False)
except Exception as e:
    print('\nERROR: The installed "socketio" package does not appear to be the expected python-socketio client.')
    print('Detail:', e)
    print('\nFix: in your virtualenv run:')
    print('  pip uninstall socketio')
    print('  pip install "python-socketio[client]"')
    raise

# latest cached agents-status payload (set by on_agents_status handler)
latest_agents = None

@sio.event
def connect():
    print('Connected to MindServer')

@sio.event
def disconnect():
    print('Disconnected from MindServer')

@sio.on('agents-status')
def on_agents_status(data):
    global latest_agents
    latest_agents = data
    print('agents-status received:')
    for a in data:
        print('  ', a)

@sio.on('bot-output')
def on_bot_output(agent_name, message):
    print(f'bot-output from {agent_name}: {message}')

@sio.on('state-update')
def on_state_update(states):
    print('state-update:')
    for agent, state in states.items():
        print('  ', agent, '->', type(state))

def create_agent_example():
    # Minimal example settings; adjust according to your profiles and settings_spec.json
    settings = {
        "profile": {"name": "admin"},
        "host": "localhost",
        "port": 25565,
        "minecraft_version": "auto",
    }

    def ack(response):
        print('create-agent ack:', response)

    print('Emitting create-agent...')
    sio.emit('create-agent', settings, callback=ack)


def login_agent(agent_name):
    """Claim identity for this socket as an agent name on the MindServer."""
    print(f"Emitting login-agent for '{agent_name}'")
    sio.emit('login-agent', agent_name)


def send_chat_message(target_agent, message_text, extra=None, wait_for_ack=False):
    """Send a chat-like message to target_agent. If wait_for_ack True, use a callback ack."""
    payload = {"message": message_text}
    if extra:
        payload.update(extra)
    if wait_for_ack:
        def ack(resp):
            print('chat-message ack:', resp)
        # python-socketio Client.emit takes (event, data, namespace=None, callback=None)
        # send an explicit object so the server can reliably parse agent and payload
        sio.emit('chat-message', {'agent': target_agent, 'data': payload}, callback=ack)
    else:
        sio.emit('chat-message', {'agent': target_agent, 'data': payload})
    print(f"Sent chat-message -> {target_agent}: {payload}")


def send_direct_message(target_agent, data):
    """Send an arbitrary JSON-serializable payload to the agent via send-message."""
    # send as explicit object so server handler receives them correctly
    sio.emit('send-message', {'agent': target_agent, 'data': data})
    print(f"Sent send-message -> {target_agent}: {data}")


def main():
    parser = argparse.ArgumentParser(description='Python Socket.IO client for MindServer')
    parser.add_argument('--login', help='Claim this socket as an agent name (login-agent)')
    parser.add_argument('--list-agents', action='store_true', help='List currently registered agents and exit')
    parser.add_argument('--chat', nargs=2, metavar=('TARGET','MESSAGE'), help='Send chat-message to TARGET with MESSAGE')
    parser.add_argument('--direct', nargs=2, metavar=('TARGET','JSON_PAYLOAD'), help='Send send-message to TARGET with JSON_PAYLOAD (string)')
    parser.add_argument('--create-agent', action='store_true', help='Emit create-agent with example settings')
    parser.add_argument('--interactive', action='store_true', help='Keep client running to receive events (default: short-lived)')
    args = parser.parse_args()

    base_url = f'http://{MINDSERVER_HOST}:{MINDSERVER_PORT}'
    print('Connecting to', base_url)
    try:
        sio.connect(base_url)
    except Exception as e:
        print('Failed to connect:', e)
        return

    # Ask server to send state updates for agents
    sio.emit('listen-to-agents')

    # Wait briefly for initial agents-status to arrive (populates latest_agents)
    def wait_for_agents(timeout=5.0):
        import time as _time
        waited = 0.0
        interval = 0.1
        while waited < timeout:
            if latest_agents is not None:
                return latest_agents
            _time.sleep(interval)
            waited += interval
        return None

    # Optional: create an example agent
    if args.create_agent:
        create_agent_example()

    # Optional: login as agent (claim identity)
    if args.login:
        login_agent(args.login)

    # If --list-agents was requested, show agents and exit
    if args.list_agents:
        agents = wait_for_agents()
        if agents is None:
            print('No agents-status received from server (timeout)')
        else:
            print('\nRegistered agents:')
            for a in agents:
                print(' -', a['name'], '(in_game=' + str(a.get('in_game')) + ', socket_connected=' + str(a.get('socket_connected')) + ')')
        sio.disconnect()
        return

    # Optional: send chat
    if args.chat:
        target, message = args.chat
        # validate target exists in latest_agents if available
        agents = wait_for_agents()
        if agents is not None and not any(a['name'] == target for a in agents):
            print(f"Warning: target agent '{target}' not found in agents-status")
        send_chat_message(target, message)

    # Optional: send direct JSON payload
    if args.direct:
        target, json_payload = args.direct
        # validate target exists in latest_agents if available
        agents = wait_for_agents()
        if agents is not None and not any(a['name'] == target for a in agents):
            print(f"Warning: target agent '{target}' not found in agents-status")
        try:
            payload = json.loads(json_payload)
        except Exception:
            print('Failed to parse JSON payload for --direct; sending as raw string')
            payload = {"message": json_payload}
        send_direct_message(target, payload)

    try:
        if args.interactive:
            print('Interactive mode -- press Ctrl+C to exit')
            while True:
                time.sleep(1)
        else:
            # short wait to allow server to process and for us to see responses
            time.sleep(2)
    except KeyboardInterrupt:
        print('\nInterrupted by user')
    finally:
        sio.disconnect()

if __name__ == '__main__':
    main()
