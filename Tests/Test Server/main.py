import asyncio
import websockets
import json
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_websocket():
    uri = "ws://192.168.232.223:8765"  # Your Pi's IP

    try:
        logger.info(f"Attempting to connect to {uri}")
        async with websockets.connect(uri) as websocket:
            # Test ping only
            logger.info("Sending ping...")
            await websocket.send(json.dumps({
                "command": "ping"
            }))
            logger.info("Waiting for response...")
            response = await websocket.recv()
            logger.info(f"Received response: {response}")

    except websockets.exceptions.ConnectionClosedError as e:
        logger.error(f"Connection closed unexpectedly: {e}")
    except websockets.exceptions.InvalidStatusCode as e:
        logger.error(f"Failed to connect: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())