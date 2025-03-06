from enum import Enum, auto
import time
import RPi.GPIO as GPIO
from datetime import datetime
import bme_geek
import camera_geek
from voice_geek import VoiceGeek
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from UI_Geek import InfoDisplay
import sys
import os


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

#Main state machine allowing switching between modes. Will have to add states as the need arises
class GeekModes:
    def __init__(self):
        # Initialize with default state
        self.current_state = Mode.BASIC
        
        # Set up button pins
        self.MODE_BUTTON_PIN = switch_mode_btn  # GPIO pin for mode switching
        self.ACTION_BUTTON_PIN = action_btn  # GPIO pin for actions within modes

        # Initialize voice recognition
        self.voice_assistant = VoiceGeek(mode_switcher_callback=self.switch_to_next_mode)
        
        # Configure GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.MODE_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.ACTION_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)    
                
        # Debounce time
        self.last_button_press = 0
        self.DEBOUNCE_TIME = 0.2
        
        # Add this to track button state
        self.mode_button_pressed = False     
        
        # Add this to track action button state
        self.action_button_pressed = False
        
        # Track displayed items in display mode
        self.current_display_index = 0
        self.display_items = []  # This would be populated with image paths
        
        # Add this to track the last time data was printed
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

    def switch_to_next_mode(self):
        """Switch to the next mode in the cycle"""
        if self.current_state == Mode.BASIC:
            self.current_state = Mode.RECORD
            print("Switched to RECORD mode")
            if self.ui_window:
                self.ui_window.set_mode(1)  # Set UI to info mode
        elif self.current_state == Mode.RECORD:
            self.current_state = Mode.DISPLAY
            print("Switched to DISPLAY mode")
            if self.ui_window:
                self.ui_window.set_mode(2)  # Set UI to media mode
        elif self.current_state == Mode.DISPLAY:
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
    
    def handle_basic_mode(self):
        """Handle actions in basic mode"""
        current_time = time.time()
        self.ui_window.update_time()
        
            # Make sure UI is in info mode
        if self.ui_window and self.ui_window.current_mode != 1:
            self.ui_window.set_mode(1)
        
        # Only print every 5 seconds
        if current_time - self.last_print_time >= 5:
            self.last_print_time = current_time
            data = bme_geek.air_sensor_data()
            if data == None:
                print("Sensor still initializing...")
            else:
                bme_geek.print_air_sensor(bme_geek.bme680_sensor)
                self.ui_window.update_temperature(bme_geek.get_temp(bme_geek.bme680_sensor))
                self.ui_window.update_humidity(bme_geek.get_humidity(bme_geek.bme680_sensor))
                #self.ui_window.update_air_quality(bme_geek.get_air_quality(bme_geek.bme680_sensor))
                
        
        # Small sleep to prevent CPU hogging
        time.sleep(0.1)
    
    def handle_record_mode(self):
        """Handle actions in record mode"""
        # Check if action button is pressed
        action_button_state = GPIO.input(self.ACTION_BUTTON_PIN)
        
        # Make sure UI is in info mode (or whichever mode you want for recording)
        if self.ui_window and self.ui_window.current_mode != 1:
            self.ui_window.set_mode(1)
        
        # Button is pressed and wasn't already pressed
        if action_button_state == False and not self.action_button_pressed:
            current_time = time.time()
            if current_time - self.last_button_press > self.DEBOUNCE_TIME:
                self.last_button_press = current_time
                self.action_button_pressed = True
                print("RECORD MODE: Taking a picture!")
                self.ui_window.update_temperature("Taking picture...")
                self.ui_window.update_humidity("Taking picture...")
                camera_geek.capture_image()
        
        # Button is released
        elif action_button_state == True and self.action_button_pressed:
            self.action_button_pressed = False
        
        # Other continuous tasks for record mode
        print("RECORD MODE: Ready to capture...")
        time.sleep(0.1)
    
    def handle_display_mode(self):
        """Handle actions in display mode"""
        # Make sure UI is in media mode
        if self.ui_window and self.ui_window.current_mode != 2:
            self.ui_window.set_mode(2)
            
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
                    if not pixmap.isNull():
                        scaled_pixmap = self.ui_window.scale_pixmap(pixmap)
                        self.ui_window.current_pixmap = scaled_pixmap
                        self.ui_window.content_label.setPixmap(scaled_pixmap)
                elif current_item.lower().endswith('.pdf'):
                    self.ui_window.content_label.setText(f"Loading PDF: {current_item}")
                    # You could call the load_pdf method here   
        
        
        # Other continuous tasks for display mode
        time.sleep(0.1)
    
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
        # Add any other cleanup code here

    def __del__(self):
        """Destructor to clean up resources"""
        self.cleanup()