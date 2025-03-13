import asyncio
import websockets
import json
import os
import base64
from datetime import datetime

# Directory to store project files
PROJECTS_DIR = "./projects"
os.makedirs(PROJECTS_DIR, exist_ok=True)

connected_clients = set()

async def handle_connection(websocket, path):
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            command = data.get("command")
            if command == "ping":
                await websocket.send(json.dumps({
                    "command": "pong",
                    "message": "Server is alive"
                    }))
            elif command == "sync_project":
                # Receive project data from web app
                await handle_project_sync(websocket, data)
            
            elif command == "upload_file":
                # Handle file upload from web app
                await handle_file_upload(websocket, data)
                
            elif command == "get_updates":
                # Send local updates back to web app
                await send_local_updates(websocket, data)
                
            elif command == "take_picture":
                # Trigger camera to take a picture
                await take_picture(websocket, data)
                
            elif command == "save_note":
                # Save a new note
                await save_note(websocket, data)
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        connected_clients.remove(websocket)

async def handle_project_sync(websocket, data):
    project_id = data.get("project_id")
    project_data = data.get("project_data")
    
    # Create project directory if it doesn't exist
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    os.makedirs(project_dir, exist_ok=True)
    
    # Save project metadata
    with open(os.path.join(project_dir, "metadata.json"), "w") as f:
        json.dump(project_data, f)
    
    await websocket.send(json.dumps({
        "status": "success",
        "message": f"Project {project_id} synced successfully",
        "command": "sync_project_response"
    }))

async def handle_file_upload(websocket, data):
    project_id = data.get("project_id")
    file_name = data.get("file_name")
    file_type = data.get("file_type")
    file_data = data.get("file_data")  # Base64 encoded
    
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    
    # Determine subdirectory based on file type
    if file_type.startswith("image/"):
        subdir = "images"
    elif file_type == "application/pdf":
        subdir = "documents"
    else:
        subdir = "other"
    
    # Create subdirectory
    subdir_path = os.path.join(project_dir, subdir)
    os.makedirs(subdir_path, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(subdir_path, file_name)
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(file_data))
    
    await websocket.send(json.dumps({
        "status": "success",
        "message": f"File {file_name} uploaded successfully",
        "command": "upload_file_response"
    }))

async def take_picture(websocket, data):
    project_id = data.get("project_id")
    
    # In a real implementation, you would interface with the Pi camera
    # For this example, we'll simulate taking a picture
    
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"photo_{timestamp}.jpg"
    
    # In a real implementation:
    # camera.capture(file_path)
    
    # For this example, we'll just create a placeholder
    project_dir = os.path.join(PROJECTS_DIR, project_id, "images")
    os.makedirs(project_dir, exist_ok=True)
    file_path = os.path.join(project_dir, file_name)
    
    # Create an empty file for demonstration
    with open(file_path, "w") as f:
        f.write("Placeholder for camera image")
    
    # Mark this file as needing to be synced
    mark_for_sync(project_id, "images", file_name)
    
    await websocket.send(json.dumps({
        "status": "success",
        "message": "Picture taken",
        "file_name": file_name,
        "command": "take_picture_response"
    }))

async def save_note(websocket, data):
    project_id = data.get("project_id")
    note_content = data.get("content")
    
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"note_{timestamp}.txt"
    
    # Save the note
    project_dir = os.path.join(PROJECTS_DIR, project_id, "notes")
    os.makedirs(project_dir, exist_ok=True)
    file_path = os.path.join(project_dir, file_name)
    
    with open(file_path, "w") as f:
        f.write(note_content)
    
    # Mark this file as needing to be synced
    mark_for_sync(project_id, "notes", file_name)
    
    await websocket.send(json.dumps({
        "status": "success",
        "message": "Note saved",
        "file_name": file_name,
        "command": "save_note_response"
    }))

def mark_for_sync(project_id, file_type, file_name):
    # Keep track of files that need to be synced back to the web app
    sync_file = os.path.join(PROJECTS_DIR, project_id, "sync_needed.json")
    
    sync_data = {}
    if os.path.exists(sync_file):
        with open(sync_file, "r") as f:
            sync_data = json.load(f)
    
    if file_type not in sync_data:
        sync_data[file_type] = []
    
    if file_name not in sync_data[file_type]:
        sync_data[file_type].append(file_name)
    
    with open(sync_file, "w") as f:
        json.dump(sync_data, f)

async def send_local_updates(websocket, data):
    project_id = data.get("project_id")
    sync_file = os.path.join(PROJECTS_DIR, project_id, "sync_needed.json")
    
    if not os.path.exists(sync_file):
        await websocket.send(json.dumps({
            "status": "success",
            "updates": {},
            "command": "get_updates_response"
        }))
        return
    
    with open(sync_file, "r") as f:
        sync_data = json.load(f)
    
    # Prepare response with file data
    response = {
        "status": "success",
        "updates": {},
        "command": "get_updates_response"
    }
    
    for file_type, file_names in sync_data.items():
        response["updates"][file_type] = []
        
        for file_name in file_names:
            file_path = os.path.join(PROJECTS_DIR, project_id, file_type, file_name)
            
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    file_data = base64.b64encode(f.read()).decode("utf-8")
                
                response["updates"][file_type].append({
                    "file_name": file_name,
                    "file_data": file_data
                })
    
    # Clear the sync file after sending updates
    os.remove(sync_file)
    
    await websocket.send(json.dumps(response))

async def main():
    print("Starting WebSocket server on 0.0.0.0:8765")
    async with websockets.serve(handle_connection, "0.0.0.0", 8765):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
