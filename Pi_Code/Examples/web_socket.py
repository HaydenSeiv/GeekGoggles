import asyncio
import websockets
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def handle_connection(websocket):
    logger.info(f"New connection from {websocket.remote_address}")
    try:
        async for message in websocket:
            logger.info(f"Received message: {message}")
            try:
                data = json.loads(message)
                command = data.get("command")
                logger.info(f"Processing command: {command}")
                
                if command == "ping":
                    logger.info("Sending pong response")
                    await websocket.send(json.dumps({
                        "command": "pong",
                        "message": "Server is alive"
                    }))
                else:
                    logger.warning(f"Unknown command: {command}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                raise  # This will help us see the actual error
    
    except Exception as e:
        logger.error(f"Connection error: {type(e).__name__}: {e}")
    finally:
        logger.info(f"Connection closed for {websocket.remote_address}")

async def main():
    logger.info("Starting WebSocket server on 0.0.0.0:8765")
    try:
        server = await websockets.serve(
            handle_connection,
            "0.0.0.0",
            8765
        )
        await asyncio.Future()  # Run forever
    except Exception as e:
        logger.error(f"Server error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())