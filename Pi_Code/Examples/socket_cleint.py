import asyncio
import websockets
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def connect_to_server():
    uri = "ws://192.168.232.11:8765"  # The server's IP and port
    
    try:
        logger.info(f"Attempting to connect to {uri}")
        async with websockets.connect(uri) as websocket:
            # Send a ping message
            ping_message = {
                "command": "hayden_test"
            }
            logger.info("Sending ping message...")
            await websocket.send(json.dumps(ping_message))
            
            # Wait for and print the response
            response = await websocket.recv()
            logger.info(f"Received response: {response}")
            
            # Keep the connection alive and handle messages
            while True:
                message = await websocket.recv()
                logger.info(f"Received message: {message}")
                # Handle the message here
                
    except websockets.exceptions.ConnectionClosedError as e:
        logger.error(f"Connection closed unexpectedly: {e}")
    except websockets.exceptions.InvalidStatusCode as e:
        logger.error(f"Failed to connect: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(connect_to_server())