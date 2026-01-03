import sys
import json
import logging
from bridge.message_handler import handle_message

# Configure logging to file since stdout is used for IPC
logging.basicConfig(filename='/tmp/localhost_python.log', level=logging.DEBUG)

def main():
    logging.info("Python Brain started")
    
    # Simple stdin/stdout loop
    for line in sys.stdin:
        try:
            logging.debug(f"Received: {line.strip()}")
            message = json.loads(line)
            response = handle_message(message)
            
            # Send back to Swift
            print(json.dumps(response), flush=True)
            logging.debug(f"Sent: {json.dumps(response)}")
            
        except json.JSONDecodeError:
            logging.error(f"Failed to decode JSON: {line}")
            print(json.dumps({"status": "error", "message": "Invalid JSON"}), flush=True)
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")
            print(json.dumps({"status": "error", "message": str(e)}), flush=True)

if __name__ == "__main__":
    main()
