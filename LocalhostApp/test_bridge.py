#!/usr/bin/env python3
"""
Simple test script for the Swift-Python bridge.
Replace this with your actual implementation once we verify it works.
"""
import sys
import json

def main():
    print("Python bridge started", flush=True)
    
    # Read from stdin line by line
    for line in sys.stdin:
        try:
            # Parse incoming JSON
            message = json.loads(line.strip())
            msg_type = message.get("type")
            payload = message.get("payload", {})
            
            if msg_type == "query":
                text = payload.get("text", "")
                print(f"Received query: {text}", file=sys.stderr, flush=True)
                
                # Generate response
                response = {
                    "status": "success",
                    "response": f"Echo: {text}"
                }
                
                # Send response back to Swift
                print(json.dumps(response), flush=True)
            else:
                error_response = {
                    "status": "error",
                    "message": f"Unknown message type: {msg_type}"
                }
                print(json.dumps(error_response), flush=True)
                
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}", file=sys.stderr, flush=True)
            error_response = {
                "status": "error",
                "message": f"Invalid JSON: {str(e)}"
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr, flush=True)
            error_response = {
                "status": "error",
                "message": str(e)
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    main()
