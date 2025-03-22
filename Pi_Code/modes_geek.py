from enum import Enum, auto
import time
import RPi.GPIO as GPIO
from datetime import datetime
import bme_geek
import Examples.camera_geek as camera_geek
from voice_geek import VoiceGeek
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from UI_Geek import InfoDisplay
import sys
import os
import asyncio
import websockets
import json
import base64
import threading
import logging


##########################################################################
###Constants###
#Buttons - GPIO pin number
switch_mode_btn = 17 # pin 11 
action_btn = 21 # pin 40

##########################################################################
###GLOBAL VARIABLES###

##########################################################################

# Define the possible states as an Enum
class Mode(Enum):
    BASIC = auto()    # Display BME680 info and time
    RECORD = auto()   # Take pictures with button press
    DISPLAY = auto()  # Show images/PDFs
    SENSOR = auto()   # Display sensor data
    TEXT = auto()    # Display text

#Main state machine allowing switching between modes. Will have to add states as the need arises
class GeekModes:
    def __init__(self):
        # Initialize with default state
        self.current_state = Mode.BASIC
        
        # Set up button pins
        self.MODE_BUTTON_PIN = switch_mode_btn  # GPIO pin for mode switching
        self.ACTION_BUTTON_PIN = action_btn  # GPIO pin for actions within modes
        
        # Configure GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.MODE_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.ACTION_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)    
                
        # Debounce time
        self.last_button_press = 0
        self.DEBOUNCE_TIME = 0.2
        
        # track mode button state
        self.mode_button_pressed = False     
        
        # track action button state
        self.action_button_pressed = False
        
        # Track displayed items in display mode
        self.current_display_index = 0
        self.display_items = []  # array to hold document paths
        
        # Track displayed text files in text mode
        self.current_text_index = 0
        self.text_items = []  # array to hold text file paths
        
        # track the last time data was printed
        self.last_print_time = 0
        
        # Initialize UI components as None
        self.ui_app = QApplication(sys.argv)  # Create once for the whole application
        self.ui_window = None
        
        # Create a Qt timer for processing Qt events
        self.qt_timer = QTimer()
        self.qt_timer.timeout.connect(self.process_qt_events)
        self.qt_timer.start(10)  # Process Qt events every 10ms
        
        # Initialize the UI
        self.start_ui()
        
        # Initialize voice recognition
        self.voice_assistant = VoiceGeek(
            mode_switcher_callback=self.switch_to_next_mode,
            db_check_interval=30,  # Check decibel levels every 30 seconds
            db_alert_callback=self.ui_window.show_alert,  # This should work now with the thread-safe implementation
            db_threshold=60  # Alert when noise exceeds 90 dB
        )
        
        # # Initialize WebSocket client
        self.websocket = None
        self.websocket_connected = False
        self.server_url = "ws://172.16.102.1:8765"  # Replace with server IP
        
        # # Start WebSocket client in a separate thread
        self.websocket_thread = threading.Thread(target=self.start_websocket_client)
        self.websocket_thread.daemon = True
        self.websocket_thread.start()

    def switch_to_next_mode(self):
        """Switch to the next mode in the cycle"""
        if self.current_state == Mode.BASIC:
            self.current_state = Mode.RECORD
            print("Switched to RECORD mode")
            if self.ui_window:
                self.ui_window.set_mode(3)  # Set UI to info mode
        elif self.current_state == Mode.RECORD:
            self.current_state = Mode.DISPLAY
            print("Switched to DISPLAY mode")
            if self.ui_window:
                self.ui_window.set_mode(2)  # Set UI to media mode
        elif self.current_state == Mode.DISPLAY:
            self.current_state = Mode.SENSOR
            print("Switched to SENSOR mode")
            if self.ui_window:
                self.ui_window.set_mode(4)  # Set UI to sensor mode
        elif self.current_state == Mode.SENSOR:
            self.current_state = Mode.TEXT
            print("Switched to TEXT mode")
            if self.ui_window:
                self.ui_window.set_mode(5)  # Set UI to text mode
        elif self.current_state == Mode.TEXT:
            self.current_state = Mode.BASIC
            print("Switched to BASIC mode")
            if self.ui_window:
                self.ui_window.set_mode(1)  # Set UI back to info mode

        # Initialize the new state
        self.on_state_enter()
    
    def on_state_enter(self):
        """Initialize things when entering a state"""
        if self.current_state == Mode.BASIC:
            # Initialize basic mode display
            print("Initializing basic mode display...")
        elif self.current_state == Mode.RECORD:
            # Initialize camera for recording
            print("Camera ready for capturing...")
        elif self.current_state == Mode.DISPLAY:
            # Load display items
            self.load_display_items()
            print(f"Display mode ready with {len(self.display_items)} items")
        elif self.current_state == Mode.SENSOR:
            # Initialize sensor mode display
            print("Initializing sensor mode display...")
        elif self.current_state == Mode.TEXT:
            # Initialize text mode display
            self.load_text_files()
            print(f"Text mode ready with {len(self.text_items)} text files")

    def load_display_items(self):
        """Load items to display in DISPLAY mode"""
        # Path to your docs folder
        docs_folder = "docs"
        
        # Supported file extensions
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        pdf_extensions = ('.pdf',)
        supported_extensions = image_extensions + pdf_extensions
        
        # Clear existing items
        self.display_items = []
        
        # Scan the directory for supported files
        if os.path.exists(docs_folder):
            for file in os.listdir(docs_folder):
                file_path = os.path.join(docs_folder, file)
                if os.path.isfile(file_path) and file.lower().endswith(supported_extensions):
                    self.display_items.append(file_path)
            
            print(f"Found {len(self.display_items)} displayable items in docs folder")
        else:
            print(f"Warning: Docs folder not found at {docs_folder}")
        
        # Reset the display index
        self.current_display_index = 0 if self.display_items else -1
    
    def load_text_files(self):
        """Load text files to display in TEXT mode"""
        # Path to your text folder
        text_folder = "text"
        
        # Supported file extensions
        text_extensions = ('.txt',)
        
        # Clear existing text items
        self.text_items = []
        
        # Scan the directory for text files
        if os.path.exists(text_folder):
            for file in os.listdir(text_folder):
                file_path = os.path.join(text_folder, file)
                if os.path.isfile(file_path) and file.lower().endswith(text_extensions):
                    self.text_items.append(file_path)
            
            print(f"Found {len(self.text_items)} text files in text folder")
        else:
            print(f"Warning: Text folder not found at {text_folder}")
        
        # Reset the text index
        self.current_text_index = 0 if self.text_items else -1
    
    def handle_basic_mode(self):
        """Handle actions in basic mode"""
        current_time = time.time()
        self.ui_window.update_time()
        
            # Make sure UI is in info mode
        if self.ui_window and self.ui_window.current_mode != 1:
            self.ui_window.set_mode(1)        
       
        # Small sleep to prevent CPU hogging
        time.sleep(0.1)
    
    def handle_record_mode(self):
        """Handle actions in record mode"""
        # Check if action button is pressed
        action_button_state = GPIO.input(self.ACTION_BUTTON_PIN)
        
        # Make sure UI is in record mode
        if self.ui_window and self.ui_window.current_mode != 3:
            self.ui_window.set_mode(3)
        
        # Button is pressed and wasn't already pressed
        if action_button_state == False and not self.action_button_pressed:
            current_time = time.time()
            if current_time - self.last_button_press > self.DEBOUNCE_TIME:
                self.last_button_press = current_time
                self.action_button_pressed = True
                print("RECORD MODE: Taking a picture!")
                self.ui_window.capture_image()
        
        # Button is released
        elif action_button_state == True and self.action_button_pressed:
            self.action_button_pressed = False
        
        # Other continuous tasks for record mode
        #print("RECORD MODE: Ready to capture...")
        time.sleep(0.1)
    
    def handle_display_mode(self):
        """Handle actions in display mode"""
        # Make sure UI is in media mode
        if self.ui_window and self.ui_window.current_mode != 2:
            self.ui_window.set_mode(2)
            
        #self.display_items[0]

        # Check if action button is pressed to cycle through items
        if GPIO.input(self.ACTION_BUTTON_PIN) == False:
            current_time = time.time()
            if current_time - self.last_button_press > self.DEBOUNCE_TIME:
                self.last_button_press = current_time
                
                # Move to next display item
                self.current_display_index = (self.current_display_index + 1) % len(self.display_items)
                print(f"DISPLAY MODE: Showing {self.display_items[self.current_display_index]}")
                

                # Load the current item into the UI
                current_item = self.display_items[self.current_display_index]
                print(f"the current item is: {current_item}")

                if current_item.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    self.ui_window.display_image(current_item)
                elif current_item.lower().endswith('.pdf'):
                    self.ui_window.content_label.setText(f"Loading PDF: {current_item}")
                    # TODO: call load_pdf method here   
        
        
        # Other continuous tasks for display mode
        time.sleep(0.1)
    
    def handle_sensor_mode(self):
        """Handle actions in sensor mode"""
        current_time = time.time()
        # Make sure UI is in sensor mode
        if self.ui_window and self.ui_window.current_mode != 4:
            self.ui_window.set_mode(4)
        
                # Only print every 1 seconds
        if current_time - self.last_print_time >= 1:
            self.last_print_time = current_time
            data = bme_geek.air_sensor_data()
            if data == None:
                print("Sensor still initializing...")
            else:
                #when calling for sensor data too often it doesnt seem to work, only do one call at a time, or add delay
                #bme_geek.print_air_sensor(bme_geek.bme680_sensor)
                #temp = bme_geek.get_temp(bme_geek.bme680_sensor)
                #hum = bme_geek.get_humidity(bme_geek.bme680_sensor)
                
                temp,hum = bme_geek.get_data(bme_geek.bme680_sensor)

                #print(f"Inside handle_sesnsor_mode in main: temp = {temp}, hum = {hum}")
                if temp is not None:
                    self.ui_window.update_temperature(temp)
                if hum is not None:
                    self.ui_window.update_humidity(hum)
                #self.ui_window.update_humidity(bme_geek.get_humidity(bme_geek.bme680_sensor))
                #self.ui_window.update_air_quality(bme_geek.get_air_quality(bme_geek.bme680_sensor))
                
        
        # Small sleep to prevent CPU hogging
        time.sleep(0.1)    
        
    def handle_text_mode(self):
        """Handle actions in text mode"""
        current_time = time.time()
        
        # Make sure UI is in text mode
        if self.ui_window and self.ui_window.current_mode != 5:
            self.ui_window.set_mode(5)
            # Store the time we entered text mode
            self.text_mode_entry_time = time.time()
            # Set initial state for recording
            if not hasattr(self, 'text_recording_triggered'):
                self.text_recording_triggered = False
                self.text_recording_complete = False
            
        # Check if there are any text files to display
        if not hasattr(self, 'text_items') or not self.text_items:
            self.ui_window.display_text("No text files found in the text folder.")
            
        # Trigger recording 3 seconds after entering text mode
        if (hasattr(self, 'text_mode_entry_time') and 
            not self.text_recording_triggered and 
            time.time() - self.text_mode_entry_time > 3):
            
            self.text_recording_triggered = True
            self.ui_window.display_text("Recording voice note... Please speak now.")
            
            # Record audio
            audio_data = self.voice_assistant.record_audio(duration=5)
            
            if audio_data:
                # Convert speech to text
                transcript = self.voice_assistant.voice_to_text(audio_data)
                
                # Save as text file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"text/voice_note_{timestamp}.txt"
                
                # Create text directory if it doesn't exist
                if not os.path.exists("text"):
                    os.makedirs("text")
                
                with open(filename, 'w') as f:
                    f.write(transcript)
                
                print(f"Voice note saved as {filename}")
                self.ui_window.display_text(f"Voice note saved:\n\n{transcript}")
                
                # Reload text files
                self.load_text_files()
            else:
                self.ui_window.display_text("Failed to record voice note.")
            
            self.text_recording_complete = True
            
        # Check if action button is pressed to cycle through items
        if GPIO.input(self.ACTION_BUTTON_PIN) == False:
            current_time = time.time()
            if current_time - self.last_button_press > self.DEBOUNCE_TIME:
                self.last_button_press = current_time
                
                # Move to next text file
                self.current_text_index = (self.current_text_index + 1) % len(self.text_items)
                current_file = self.text_items[self.current_text_index]
                print(f"TEXT MODE: Showing {current_file}")
                
                # Read and display the text file
                try:
                    with open(current_file, 'r') as file:
                        text_content = file.read()
                    self.ui_window.display_text(text_content)
                except Exception as e:
                    print(f"Error reading text file {current_file}: {e}")
                    self.ui_window.display_text(f"Error reading file: {e}")
        
        # Small sleep to prevent CPU hogging
        time.sleep(0.1)

########################################################################################
### UI METHODS ###
########################################################################################      

    def start_ui(self):
        """Start the UI"""
        if not self.ui_window:
            self.ui_window = InfoDisplay()
            self.ui_window.showFullScreen()  # Explicitly show the window in full screen mode
    
    def close_ui(self):
        """Close the UI if it's open"""
        if self.ui_window:
            self.ui_window.close()
            self.ui_window = None
    
    def process_qt_events(self):
        """Process Qt events to keep the UI responsive"""
        if self.ui_app:
            self.ui_app.processEvents()
            
########################################################################################
### WEBSOCKET METHODS ###
########################################################################################
            
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
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.websocket_connected = True
            print(f"Connected to WebSocket server at {self.server_url}")
            
            # Send initial connection message
            await self.send_websocket_message({
                "command": "connect",
                "device": "geek_goggles"
            })
            
            # Start listening for messages
            await self.listen_for_messages()
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            self.websocket_connected = False
    
    async def listen_for_messages(self):
        """Listen for incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    command = data.get("command")
                    print(f"Received WebSocket command: {command}")
                    
                if command == "josh_test":
                    logger.info("Sending pong response")
                    await websocket.send(json.dumps({
                        "command": "hayden_test",
                        "message": "Server is alive"
                    }))
                if command == "send_cat":
                    image_path = "Examples/exam_docs/catPicture.jpg"
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
                if command == "here_is_the_dog":
                    try:
                        # Extract the base64 image data and filename
                        image_data = data.get("data")
                        filename = data.get("filename", "dogPicture.jpg")
                        
                        # Decode the base64 data
                        image_bytes = base64.b64decode(image_data)
                        
                        # Save the image to the exam_docs directory
                        save_path = f"docs/{filename}"
                        with open(save_path, "wb") as image_file:
                            image_file.write(image_bytes)
                        
                        logger.info(f"Dog image saved to {save_path}")
                        
                        # Send confirmation back to client
                        await websocket.send(json.dumps({
                            "command": "dog_received",
                            "message": f"Dog image saved as {filename}"
                        }))
                    except Exception as e:
                        logger.error(f"Error saving dog image: {e}")
                        await websocket.send(json.dumps({
                            "command": "error",
                            "message": f"Failed to save dog image: {str(e)}"
                        }))
                else:
                    logger.warning(f"Unknown command: {command}")
                        
                except json.JSONDecodeError:
                    print("Invalid JSON received from server")
                except Exception as e:
                    print(f"Error processing message: {e}")
        except Exception as e:
            print(f"WebSocket listen error: {e}")
            self.websocket_connected = False
    
    async def handle_received_image(self, data):
        """Handle received image data"""
        try:
            image_data = data.get("data")
            filename = data.get("filename", "received_image.jpg")
            
            # Save the image to docs folder
            save_path = f"docs/{filename}"
            with open(save_path, "wb") as image_file:
                image_file.write(base64.b64decode(image_data))
            
            print(f"Received and saved image to {save_path}")
            
            # Reload display items if in DISPLAY mode
            if self.current_state == Mode.DISPLAY:
                self.load_display_items()
        except Exception as e:
            print(f"Error handling received image: {e}")
    
    async def send_websocket_message(self, data):
        """Send a message to the WebSocket server"""
        if not self.websocket_connected:
            print("WebSocket not connected, can't send message")
            return
        
        try:
            message = json.dumps(data)
            await self.websocket.send(message)
            print(f"Sent message: {data.get('command', 'unknown')}")
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")
            self.websocket_connected = False
    
    def send_message_nonblocking(self, data):
        """Non-blocking method to send a WebSocket message"""
        if not self.websocket_connected:
            print("WebSocket not connected, can't send message")
            return
            
        # Create a new thread to send the message
        thread = threading.Thread(target=self.run_async_send, args=(data,))
        thread.daemon = True
        thread.start()
    
    def run_async_send(self, data):
        """Run async send in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.send_websocket_message(data))
        except Exception as e:
            print(f"Error in async send: {e}")
        finally:
            loop.close()
    
    def send_image_to_server(self, image_path, command="send_image"):
        """Send an image to the server"""
        try:
            # Read the image file
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Create data packet
            data = {
                "command": command,
                "filename": os.path.basename(image_path),
                "type": "image",
                "data": image_data
            }
            
            # Send the image
            self.send_message_nonblocking(data)
            print(f"Sending image {image_path} to server")
        except Exception as e:
            print(f"Error sending image to server: {e}")
    
    
    def run(self):
        """Main loop to run the state machine"""
        try:
            print(f"Starting in {self.current_state.name} mode")
            self.on_state_enter()
            
            # Make sure the UI window is visible
            if self.ui_window:
                self.ui_window.show()
            
            while True:
                # Check for mode button press to change states
                mode_button_state = GPIO.input(self.MODE_BUTTON_PIN)
                
                # Button is pressed (False when pressed due to pull-up)
                if mode_button_state == False and not self.mode_button_pressed:
                    current_time = time.time()
                    if current_time - self.last_button_press > self.DEBOUNCE_TIME:
                        self.last_button_press = current_time
                        self.mode_button_pressed = True
                        self.switch_to_next_mode()
                
                # Button is released
                elif mode_button_state == True and self.mode_button_pressed:
                    self.mode_button_pressed = False
                
                # Handle current state
                if self.current_state == Mode.BASIC:
                    self.handle_basic_mode()
                elif self.current_state == Mode.RECORD:
                    self.handle_record_mode()
                elif self.current_state == Mode.DISPLAY:
                    self.handle_display_mode()
                elif self.current_state == Mode.SENSOR:
                    self.handle_sensor_mode()
                elif self.current_state == Mode.TEXT:
                    self.handle_text_mode()
                

                # Process Qt events to keep the UI responsive
                self.process_qt_events()
                
                time.sleep(0.05)  # Small delay to prevent CPU hogging
                
        except KeyboardInterrupt:
            print("Program terminated by user")
        finally:
            GPIO.cleanup()
            self.cleanup()

    def cleanup(self):
        """Clean up resources before exiting"""
        self.close_ui()
        if hasattr(self, 'voice_assistant'):
            self.voice_assistant.cleanup()
       

    def __del__(self):
        """Destructor to clean up resources"""
        self.cleanup()

