"""Send command to persistent agent via socket."""
import socket
import json
import sys

AGENT_HOST = "localhost"
AGENT_PORT = 5556


def send_command(command: dict) -> dict:
    """Send command to agent and get response."""
    try:
        # Connect to agent
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((AGENT_HOST, AGENT_PORT))
        
        # Send command (JSON + newline)
        cmd_str = json.dumps(command) + "\n"
        sock.sendall(cmd_str.encode())
        
        # Receive response
        response = sock.recv(4096).decode().strip()
        sock.close()
        
        return json.loads(response)
    
    except ConnectionRefusedError:
        return {"status": "error", "message": "Agent not running - start persistent_agent.py first"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_command.py <command_json>")
        print('Example: python send_command.py \'{"action": "login"}\'')
        sys.exit(1)
    
    cmd = json.loads(sys.argv[1])
    result = send_command(cmd)
    print(json.dumps(result, indent=2))
