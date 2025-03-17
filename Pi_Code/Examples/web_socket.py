import asyncio
import websockets
import json
import logging
import base64

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
                
                if command == "josh_test":
                    logger.info("Sending pong response")
                    await websocket.send(json.dumps({
                        "command": "hayden_test",
                        "message": "Server is alive"
                    }))
                if command == "send_cat":
                    image_path = "exam_docs/catPicture.jpg"
                    with open(image_path, "rb") as image_file:
                        image_data = base64.b64encode(image_file.read()).decode('utf-8')
                    logger.info("Sending cat")
                    await websocket.send(json.dumps({
                        "command": "here_is_the_cat",
                        "message": "Here is the cat",
                        "type": "image",
                        "filename": "catPicture.jpg",
                        "data": image_data
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

#joshs IP
# 192.168.232.11

#my ip 
#192.168.232.223