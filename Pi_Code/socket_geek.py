import sys
import os
import asyncio
import websockets
import json
import base64
import threading
import logging
import wave
import struct
########################################################################################
### WEBSOCKET METHODS ###
########################################################################################
        # # Initialize WebSocket client
global  websocket
websocket = None
global websocket_connected
websocket_connected = False
global server_url
server_url = "wss://192.168.10.11:7007/ws"  # Replace with server IP
        
    # Add WebSocket methods
def start_websocket_client(self):
    """Start the WebSocket client in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(self.connect_websocket())
    except Exception as e:
        print(f"WebSocket client error: {e}")
    finally:
        loop.close()

async def connect_websocket(self):
    """Connect to the WebSocket server"""
    global websocket
    global websocket_connected
    global server_url
    try:
        # Create a custom SSL context that doesn't verify certificates
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Connect with the custom SSL context
        websocket = await websockets.connect(
            server_url, 
            ssl=ssl_context
        )
        websocket_connected = True
        print(f"Connected to WebSocket server at {server_url}")
        
        # Send initial connection message
        await send_websocket_message({
            "command": "connected",
            "message": "geek_goggles",
            "fileData": "XYZ"
        })
        
        # Start listening for messages
        await listen_for_messages()
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        websocket_connected = False

async def listen_for_messages():
    """Listen for incoming WebSocket messages"""
    
    try:
        async for message in websocket:
            print(message)
            try:
                # Decode the message from UTF-8 if it's bytes
                if isinstance(message, bytes):
                    message = message.decode('utf-8')
                data = json.loads(message)
                print(data)
                command = data.get("command")
                print(f"Received WebSocket command: {command}")
                match command:
                    case "josh_test":
                        print("Sending pong response")
                        await websocket.send(json.dumps({
                            "command": "hayden_test",
                            "message": "Server is alive"
                        }))
                    case "send_cat":
                        image_path = "docs/catPicture.jpg"
                        print("Sending cat")
                        await send_chunked_image("here_is_the_cat", image_path)

                    case "on_load_file_transfer":
                        file_type = data.get("fileType")
                        if(file_type == "image/jpeg"):
                            handle_received_image(data)
                        else:
                            print("Unkown image type receive in on load transfer")


                    case "here_is_the_dog":
                        try:
                            print("Inside here is the dog func")
                            # Extract the base64 image data and filename
                            image_data = data.get("fileData")
                            filename = data.get("fileName", "dogPicture.jpg")
                            
                            # Decode the base64 data
                            image_bytes = base64.b64decode(image_data)
                            
                            # Save the image to the exam_docs directory
                            save_path = f"docs/{filename}.jpg"
                            with open(save_path, "wb") as image_file:
                                image_file.write(image_bytes)
                            
                            print(f"Dog image saved to {save_path}")
                            
                            # Send confirmation back to client
                            await websocket.send(json.dumps({
                                "command": "dog_received",
                                "message": f"Dog image saved as {filename}"
                            }))
                        except Exception as e:
                            print(f"Error saving dog image: {e}")
                            await websocket.send(json.dumps({
                                "command": "error",
                                "message": f"Failed to save dog image: {str(e)}"
                            }))
                    case _:
                        print(f"Unknown command: {command}")
                        
            except json.JSONDecodeError:
                    print("Invalid JSON received from server")
            except Exception as e:
                    print(f"Error processing message: {e}")
    except Exception as e:
        print(f"WebSocket listen error: {e}")
        websocket_connected = False

async def handle_received_image(self, data):
    """Handle received image data"""         
    try:           
        # Try to get image data from either 'data' or 'fileData' field
        image_data = data.get("fileData")
        if not image_data:
            raise ValueError("No image data found in message")
            
        # Get filename, defaulting to received_image.jpg if not provided
        filename = data.get("fileName") 
        print(f"The received file name is {filename}")

        # Save the image to docs folder
        save_path = f"docs/{filename}"
        with open(save_path, "wb") as image_file:
            image_file.write(base64.b64decode(image_data))
        
        print(f"Received and saved image to {save_path}")
        
        # # Reload display items if in DISPLAY mode
        # if self.current_state == Mode.DISPLAY:
        #     self.load_display_items()
    except Exception as e:
        print(f"Error handling received image: {e}")

async def send_websocket_message(data):
    """Send a message to the WebSocket server"""
    if not websocket_connected:
        print("WebSocket not connected, can't send message")
        return
    
    try:
        message = json.dumps(data)
        await websocket.send(message)
        print(f"Sent message: {data.get('command', 'unknown')}")
    except Exception as e:
        print(f"Error sending WebSocket message: {e}")
        websocket_connected = False

def send_message_nonblocking(self, data):
    """Non-blocking method to send a WebSocket message"""
    if not websocket_connected:
        print("WebSocket not connected, can't send message")
        return
        
    # Create a new thread to send the message
    thread = threading.Thread(target=run_async_send, args=(data,))
    thread.daemon = True
    thread.start()

def run_async_send(data):
    """Run async send in a separate thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(send_websocket_message(data))
    except Exception as e:
        print(f"Error in async send: {e}")
    finally:
        loop.close()

def chunk_data(data, chunk_size=3072):  # Using 3KB chunks to stay well under the 4KB limit
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

async def send_chunked_image(command, image_path):
    try:
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Split into chunks
        chunks = chunk_data(image_data)
        total_chunks = len(chunks)

        print(f"sending {image_path} with command {command}")

        # Send start message
        await websocket.send(json.dumps({
            "command": f"{command}_start",
            "fileName": os.path.basename(image_path),
            "totalChunks": total_chunks,
            "fileType": "image"
        }))

        # Send each chunk
        for i, chunk in enumerate(chunks):
            await websocket.send(json.dumps({
                "command": f"{command}_chunk",
                "chunkIndex": i,
                "totalChunks": total_chunks,
                "fileData": chunk
            }))
            await asyncio.sleep(0.01)  # Small delay to prevent flooding

        # Send end message
        await websocket.send(json.dumps({
            "command": f"{command}_end",
            "fileName": os.path.basename(image_path)
        }))
        
    except Exception as e:
        print(f"Error sending chunked image: {e}")
        # Send error message
        await websocket.send(json.dumps({
            "command": "error",
            "message": f"Failed to send image: {str(e)}"
        }))

        
# def send_files_to_server(self):
#     """Send all files back to the server"""
#     # Create async event loop for sending files
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
    
#     try:
#         # Check if websocket is connected
#         if not self.websocket_connected:
#             print("WebSocket not connected, cannot send files")
#             return

#         # Define directories to check
#         directories = ['docs', 'pics', 'text']
        
#         for directory in directories:
#             if not os.path.exists(directory):
#                 print(f"Directory {directory} does not exist, skipping...")
#                 continue
            
#             print(f"Sending files from {directory}...")
            
#             # Get all files in the directory
#             files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            
#             for file in files:
#                 file_path = os.path.join(directory, file)
#                 try:
#                     # Determine if file is an image or text based on extension
#                     file_ext = os.path.splitext(file)[1].lower()
#                     is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
                    
#                     if is_image:
#                         # Send image file
#                         print(f"Sending image: {file}")
#                         loop.run_until_complete(self.send_chunked_image("backup_file", file_path))
#                     else:
#                         # Send text file
#                         print(f"Sending text file: {file}")
#                         with open(file_path, 'r') as f:
#                             text_content = f.read()
#                             loop.run_until_complete(self.websocket.send(json.dumps({
#                                 "command": "backup_text",
#                                 "filename": file,
#                                 "content": text_content,
#                                 "directory": directory
#                             })))
                    
#                     print(f"Successfully sent {file}")
                    
#                 except Exception as e:
#                     print(f"Error sending file {file}: {e}")
#                     continue
        
#         # Send completion message
#         loop.run_until_complete(self.websocket.send(json.dumps({
#             "command": "backup_complete",
#             "message": "All files have been sent"
#         })))
        
#         print("File backup completed")
        
#     except Exception as e:
#         print(f"Error during file backup: {e}")
#     finally:
#         loop.close()