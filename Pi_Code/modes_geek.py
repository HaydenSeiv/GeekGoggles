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
import wave
import struct
import paho.mqtt.client as mqtt


##########################################################################
###Constants###
#Buttons - GPIO pin number
switch_mode_btn = 17 # pin 11 
action_btn = 16 # pin 36
server_url = "192.168.188.11"


##########################################################################
###GLOBAL VARIABLES###

##########################################################################

# Define the possible states as an Enum
class Mode(Enum):
    BASIC = auto()    # Display BME680 info and time
    RECORD = auto()   # Take pictures with button press
    DISPLAY = auto()  # Show images/PDFs
    SENSOR = auto()   # Display sensor data
    TEXT = auto()     # Display text
    TOOL = auto()     # Display tool reeading

#Main state machine allowing switching between modes. Will have to add states as the need arises
class GeekModes:
    display_items = []  # array to hold document paths
    def __init__(self):
        # Initialize with default state
        self.current_state = Mode.BASIC
        
        print(f"Configuring Buttons")
        # Set up button pins
        self.MODE_BUTTON_PIN = switch_mode_btn  # GPIO pin for mode switching
        self.ACTION_BUTTON_PIN = action_btn  # GPIO pin for actions within modes
       
        # Configure GPIO - buttons are active low (enternal pull ups)
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

        #current project info:
        self.proj_id = None
        self.user_id = None
        self.proj_name = None
        
        
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
        
        # Start air quality monitoring thread
        self.air_quality_thread = bme_geek.start_air_quality_monitoring(self.ui_window)
        
        # Initialize voice recognition
        self.voice_assistant = VoiceGeek(
            mode_switcher_callback=self.switch_to_next_mode,
            db_check_interval=30,  # Check decibel levels every 30 seconds
            db_alert_callback=self.ui_window.show_alert,
            db_threshold=90,  # Alert when noise exceeds 90 dB
            note_callback=self.handle_note_recording,
            mode_chooser_callback=self.choose_specific_mode,
            cycle_item_callback=self.cycle_display_item,
            take_pic_callback=self.take_pic_callback
        )
        
        # # Initialize WebSocket client
        self.websocket = None
        self.websocket_connected = False
        self.server_url = "wss://" + server_url + ":7007/ws"  # Replace with server IP
        
        # # Start WebSocket client in a separate thread
        self.websocket_thread = threading.Thread(target=self.start_websocket_client)
        self.websocket_thread.daemon = True
        self.websocket_thread.start()

        # Create an MQTT client instance
        self.mqtt_client = mqtt.Client()

        #dataa var to read
        self.tool_reading = "No Reading"

        # Assign callback functions
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Connect to the broker (modify these parameters according to your broker)
        broker_address = server_url  # This is a public test broker
        port = 1883
        # If your broker requires authentication, uncomment and modify these lines:
        # client.username_pw_set("your_username", "your_password")

        # Connect to the broker
        try:
            self.mqtt_client.connect(broker_address, port, 60)   
            print(f"MQTT: {self.mqtt_client}") 

            # Start the MQTT loop in a separate thread
            self.mqtt_client.loop_start()
        except:        
            print("No MQTT to connect")
        

    def switch_to_next_mode(self):
        """Switch to the next mode in the cycle"""
        if self.current_state == Mode.BASIC:
            self.current_state = Mode.RECORD
            print("Switched to RECORD mode")
            if self.ui_window:
                self.ui_window.set_mode(3)  # Set UI to Camera/record mode
        elif self.current_state == Mode.RECORD:
            self.current_state = Mode.DISPLAY
            print("Switched to DISPLAY mode")
            if self.ui_window:
                self.ui_window.set_mode(2)  # Set UI to Document display mode
        elif self.current_state == Mode.DISPLAY:
            self.current_state = Mode.SENSOR
            print("Switched to SENSOR mode")
            if self.ui_window:
                self.ui_window.set_mode(4)  # Set UI to sensor mode
        elif self.current_state == Mode.SENSOR:
            self.current_state = Mode.TEXT
            print("Switched to Tool mode")
            if self.ui_window:
                self.ui_window.set_mode(5)  # Set UI to Note/text record mode
        elif self.current_state == Mode.TEXT:
            self.current_state = Mode.TOOL
            print("Switched to TOOL mode")
            if self.ui_window:
                self.ui_window.set_mode(6)  # Set UI to tool mode
        elif self.current_state == Mode.TOOL:
            self.current_state = Mode.BASIC
            print("Switched to BASIC mode")
            if self.ui_window:
                self.ui_window.set_mode(1)  # Set UI back to basic clock mode

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
        elif self.current_state == Mode.TOOL:
            # Initialize tool mode display
            print("Initializing Tool Mode...")


    def load_display_items(self):
        """Load items to display in DISPLAY mode"""
        # Path to your docs folder
        docs_folder = "docs"
        
        # Supported file extensions
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        pdf_extensions = ('.pdf',)
        supported_extensions = image_extensions + pdf_extensions
        
        # Clear existing items
        GeekModes.display_items = []
        
        # Scan the directory for supported files
        if os.path.exists(docs_folder):
            for file in os.listdir(docs_folder):
                file_path = os.path.join(docs_folder, file)
                if os.path.isfile(file_path) and file.lower().endswith(supported_extensions):
                    GeekModes.display_items.append(file_path)
            
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

        # Button is pressed and wasn't already pressed (FALSE when pressed with pull-up)
        if action_button_state == False and not self.action_button_pressed:
            current_time = time.time()
            if current_time - self.last_button_press > self.DEBOUNCE_TIME:
                print("Action button pressed, Taking a picture!")
                self.last_button_press = current_time
                self.action_button_pressed = True  # Set button state to pressed
                self.take_pic_callback()
        
        # Button is released
        elif action_button_state == True and self.action_button_pressed:
            self.action_button_pressed = False
        
        # Other continuous tasks for record mode
        #print("RECORD MODE: Ready to capture...")
        time.sleep(0.1)

    def take_pic_callback(self):
        print("Inside of take_pic_callback in Modes")
        pic_name = self.ui_window.capture_image()
        try:            
            time.sleep(1)  # Wait 500ms for the image to save
            print(f"Sending chunked image: {pic_name}")
            self.run_async_send_pic("new_pic", pic_name)
        except Exception as e:
            print(f"Error sending chunked image: {e}")

    def cycle_display_item(self):
        #print("inside cycle display item")
        print(f"Display items in cycle have {len(GeekModes.display_items)} items")
        # Move to next display item
        if(len(GeekModes.display_items) > 0):
            self.current_display_index = (self.current_display_index + 1) % len(GeekModes.display_items)
            print(f"DISPLAY MODE: Showing {GeekModes.display_items[self.current_display_index]}")
        
            # Load the current item into the UI
            current_item = self.display_items[self.current_display_index]
            print(f"the current item is: {current_item}")

            if current_item.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.ui_window.display_image(current_item)
            elif current_item.lower().endswith('.pdf'):
                self.ui_window.content_label.setText(f"Loading PDF: {current_item}")
                # TODO: call load_pdf method here

    def handle_display_mode(self):
        """Handle actions in display mode"""
        #print("inside handle display mode")
        # Make sure UI is in media mode
        if self.ui_window and self.ui_window.current_mode != 2:
            self.ui_window.set_mode(2)
            
        #self.display_items[0]        

        # Check if action button is pressed to cycle through items
        if GPIO.input(self.ACTION_BUTTON_PIN) == False:
            current_time = time.time()
            if current_time - self.last_button_press > self.DEBOUNCE_TIME:
                self.last_button_press = current_time
                self.cycle_display_item()
        
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
            # Set initial state for recording
            if not hasattr(self, 'text_recording_triggered'):
                self.text_recording_triggered = False
                self.text_recording_complete = False
        
        # Check if there are any text files to display
        # if not hasattr(self, 'text_items') or not self.text_items:
        #     print("Setting text to say record")
        #     self.ui_window.display_text("Say Record Note to record 10s note")
        
        # Text mode UI logic
        # The recording will now be triggered by the voice_assistant when it detects "record_note"
        
        #Check if action button is pressed to cycle through items
        if GPIO.input(self.ACTION_BUTTON_PIN) == False:
            current_time = time.time()
            if current_time - self.last_button_press > self.DEBOUNCE_TIME:
                self.last_button_press = current_time
                
                # Move to next text file
                if self.text_items:
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
    
    def handle_tool_mode(self):
        """Handle actions in sensor mode"""
        #print("Inside of handle tool")
        current_time = time.time()
        # Make sure UI is in sensor mode
        if self.ui_window and self.ui_window.current_mode != 6:
            self.ui_window.set_mode(6)
        
        # Only print every 1 seconds
        if current_time - self.last_print_time >= 1:
            self.last_print_time = current_time
            self.ui_window.update_tool(self.tool_reading)
        
        # Small sleep to prevent CPU hogging
        time.sleep(0.1) 

    def handle_note_recording(self):
        """Callback for when the 'record_note' intent is detected"""
        # Only process if we're in TEXT mode
        if self.current_state != Mode.TEXT:
            print("Ignoring record_note intent - not in TEXT mode")
            return
        
        print("'Record note' intent detected in TEXT mode - starting recording")
        self.text_recording_triggered = True
        
        # Record for 10 seconds, updating the display each second
        duration = 10
        for remaining in range(duration, 0, -1):
            # Update display with countdown (thread-safe)
            self.ui_window.display_text(f"Recording in progress...\nPlease speak now\n\nTime remaining: {remaining} seconds")
            time.sleep(1)
        
        # Record audio
        audio_data, audio_path = self.voice_assistant.record_audio(duration=10)
        
        try:
            print("Sending chunked audio")
            threading.Thread(target=self.run_async_send_audio, args=("new_audio", audio_path)).start()
        except Exception as e:
            print(f"Error sending chunked audio: {e}")       
        
        # Reset display text back to default (thread-safe)
        self.ui_window.display_text("Say record note to Record 10s note")
        
        # Return control to main thread immediately
        self.text_recording_complete = True
        self.text_recording_triggered = False

    def choose_specific_mode(self, mode_name):
        """Switch to a specific mode based on voice command
        
        Args:
            mode_name (str): Name of the mode to switch to (from voice intent slots)
        """
        print(f"Voice command: switching to {mode_name} mode")
        
        # Map the mode names from voice command to Mode enum values
        if mode_name == "tool":
            self.current_state = Mode.TOOL
            if self.ui_window:
                self.ui_window.set_mode(6)
        elif mode_name == "notes":
            self.current_state = Mode.TEXT
            if self.ui_window:
                self.ui_window.set_mode(5)
        elif mode_name == "sensors":
            self.current_state = Mode.SENSOR
            if self.ui_window:
                self.ui_window.set_mode(4)
        elif mode_name == "camera":
            self.current_state = Mode.RECORD
            if self.ui_window:
                self.ui_window.set_mode(3)
        elif mode_name == "documents":
            self.current_state = Mode.DISPLAY
            if self.ui_window:
                self.ui_window.set_mode(2)
        elif mode_name == "time":
            self.current_state = Mode.BASIC
            if self.ui_window:
                self.ui_window.set_mode(1)
        else:
            print(f"Unknown mode: {mode_name}")
            return
            
        # Initialize the new state
        self.on_state_enter()

########################################################################################
### UI METHODS ###
########################################################################################      

    def start_ui(self):
        """Start the UI"""
        if not self.ui_window:
            self.ui_window = InfoDisplay()
            self.ui_window.showFullScreen()  # Explicitly show the window in full screen mode
            self.ui_window.set_mode(1) #start in time mode
    
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
### MQTT METHODS ###
########################################################################################  
    # Callback when the client receives a CONNACK response from the server
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            # Subscribe to a specific topic instead of wildcard
            client.subscribe("#")
            # Publish a test message to verify everything is working
            client.publish("test/topic", "Hello, MQTT!")
        else:
            print(f"Failed to connect, return code {rc}")
        

    # Callback when a message is received from the server
    def on_message(self, client, userdata, msg):
        #print(f"Message received on topic {msg.topic}: {msg.payload.decode()}")
        receive_time_us = time.monotonic_ns() // 1000  # Convert ns to µs
        
        data = json.loads(msg.payload.decode())
        mess_id = data.get('id')
        sent_time_us = data.get('timestamp')
        value = data.get('value')
        #self.tool_reading = msg.payload.decode()
        self.tool_reading = value
        print(f"Message ID: {mess_id}: time difference: {receive_time_us - sent_time_us} µs")
        print(f"Tool Reading: {self.tool_reading}")

 
########################################################################################
### WEBSOCKET METHODS ###
########################################################################################
            
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
            # Create a custom SSL context that doesn't verify certificates
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Connect with the custom SSL context
            self.websocket = await websockets.connect(
                self.server_url, 
                ssl=ssl_context
            )
            self.websocket_connected = True
            print(f"Connected to WebSocket server at {self.server_url}")
            
            # # Send initial connection message
            # await self.send_websocket_message({
            #     "command": "connected",
            #     "message": "geek_goggles",
            #     "fileData": "XYZ"
            # })
            
            # Start listening for messages
            await self.listen_for_messages()
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            self.websocket_connected = False
    
    async def listen_for_messages(self):
        """Listen for incoming WebSocket messages"""
        
        try:
            async for message in self.websocket:
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
                            await self.websocket.send(json.dumps({
                                "command": "hayden_test",
                                "message": "Server is alive"
                            }))
                        case "send_cat":
                            image_path = "docs/catPicture.jpg"
                            print("Sending cat")
                            await self.send_chunked_image("here_is_the_cat", image_path)
                        
                        case "login_info":
                            print("Sending Connected")
                            self.proj_id = data.get("proj_id")
                            self.proj_name = data.get("proj_name")
                            self.user_id = data.get("user_id")
                            # Send initial connection message
                            await self.send_websocket_message({
                                "command": "connected",
                                "message": "geek_goggles",
                                "fileData": "XYZ",
                                "user_id": f"{self.user_id}",
                                "proj_id": f"{self.proj_id}",
                                "proj_name": f"{self.proj_name}"
                            })


                        case "on_load_file_transfer":
                            file_type = data.get("fileType")
                            if(file_type == "image/jpeg" or file_type == "image/png"):
                                await self.handle_received_image(data)
                            else:
                                print("Unkown image type receive in on load transfer")
                        
                        case "new_image_upload":
                            file_type = data.get("fileType")
                            file_name = data.get("fileName")
                            if(file_type == "image/jpeg"):
                                await self.handle_received_image(data)
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
                                await self.websocket.send(json.dumps({
                                    "command": "dog_received",
                                    "message": f"Dog image saved as {filename}"
                                }))
                            except Exception as e:
                                print(f"Error saving dog image: {e}")
                                await self.websocket.send(json.dumps({
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
            self.websocket_connected = False
    
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
            save_path = f"docs/{filename}.jpeg"
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
    
    def chunk_data(self, data, chunk_size=3072):  # Using 3KB chunks to stay well under the 4KB limit
        return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    
    async def send_chunked_image(self, command, image_path):
        try:
            # Read and encode the image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Split into chunks
            chunks = self.chunk_data(image_data)
            total_chunks = len(chunks)

            print(f"sending {image_path} with command {command}")

            # Send start message
            await self.websocket.send(json.dumps({
                "command": f"{command}_start",
                "fileName": os.path.basename(image_path),
                "totalChunks": total_chunks,
                "fileType": "image/jpeg"
            }))

            # Send each chunk
            for i, chunk in enumerate(chunks):
                await self.websocket.send(json.dumps({
                    "command": f"{command}_chunk",
                    "chunkIndex": i,
                    "fileName": os.path.basename(image_path),
                    "totalChunks": total_chunks,
                    "fileData": chunk,
                    "fileType": "image/jpeg"
                }))
                await asyncio.sleep(0.01)  # Small delay to prevent flooding

            # Send end message
            await self.websocket.send(json.dumps({
                "command": f"{command}_end",
                "fileName": os.path.basename(image_path),
                "fileType": "image/jpeg"
            }))
            
        except Exception as e:
            print(f"Error sending chunked image: {e}")
            # Send error message
            await self.websocket.send(json.dumps({
                "command": "error",
                "message": f"Failed to send image: {str(e)}"
            }))
    
    async def send_chunked_audio(self, command, audio_path):
        """Send an audio file in chunks over WebSocket
        
        Args:
            command (str): Command identifier for the WebSocket message
            audio_path (str): Path to the audio file to send
        """
        try:
            # Read and encode the audio file
            with open(audio_path, "rb") as audio_file:
                audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
            
            # Split into chunks
            chunks = self.chunk_data(audio_data)
            total_chunks = len(chunks)

            print(f"Sending audio {audio_path} with command {command}")

            # Send start message
            await self.websocket.send(json.dumps({
                "command": f"{command}_start",
                "fileName": os.path.basename(audio_path),
                "totalChunks": total_chunks,
                "fileType": "audio/wav"  # Specify the audio format
            }))

            # Send each chunk
            for i, chunk in enumerate(chunks):
                await self.websocket.send(json.dumps({
                    "command": f"{command}_chunk",
                    "chunkIndex": i,
                    "fileName": os.path.basename(audio_path),
                    "totalChunks": total_chunks,
                    "fileData": chunk
                }))
                await asyncio.sleep(0.01)  # Small delay to prevent flooding

            # Send end message
            await self.websocket.send(json.dumps({
                "command": f"{command}_end",
                "fileName": os.path.basename(audio_path),
                "fileType": "audio/wav"  
            }))
            
            print(f"Successfully sent audio file {audio_path}")
            
        except Exception as e:
            print(f"Error sending chunked audio: {e}")
            # Send error message
            await self.websocket.send(json.dumps({
                "command": "error",
                "message": f"Failed to send audio: {str(e)}"
            }))
    
    def run_async_send_audio(self, command, audio_path):
        """Run async send audio in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.send_chunked_audio(command, audio_path))
        except Exception as e:
            print(f"Error in async send audio: {e}")
        finally:
            loop.close()

    def run_async_send_pic(self, command, pic_path):
        """Run async send audio in a separate thread"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.send_chunked_image(command, pic_path))
        except Exception as e:
            print(f"Error in async send Pic: {e}")
        finally:
            loop.close()
            
    
    
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
                        print("button pressed to switch mode")
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
                elif self.current_state == Mode.TOOL:
                    self.handle_tool_mode()
                

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
        print("starting clean up")
        #send all files back to the server
        #self.send_files_to_server()
        if hasattr(self, 'mqtt_client'):
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        self.close_ui()
        if hasattr(self, 'voice_assistant'):
            self.voice_assistant.cleanup()
       

    def __del__(self):
        """Destructor to clean up resources"""
        self.cleanup()

