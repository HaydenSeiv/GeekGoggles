from enum import Enum, auto
import time
import RPi.GPIO as GPIO
from datetime import datetime
import bme_geek
import camera_geek
from voice_geek import VoiceGeek

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

    def switch_to_next_mode(self):
        """Switch to the next mode in the cycle"""
        if self.current_state == Mode.BASIC:
            self.current_state = Mode.RECORD
            print("Switched to RECORD mode")
        elif self.current_state == Mode.RECORD:
            self.current_state = Mode.DISPLAY
            print("Switched to DISPLAY mode")
        elif self.current_state == Mode.DISPLAY:
            self.current_state = Mode.BASIC
            print("Switched to BASIC mode")
        
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
        # This would actually scan a directory for images/PDFs
        self.display_items = ["image1.jpg", "image2.jpg", "document.pdf"]
        self.current_display_index = 0
    
    def handle_basic_mode(self):
        """Handle actions in basic mode"""
        current_time = time.time()
        
        # Only print every 5 seconds
        if current_time - self.last_print_time >= 5:
            self.last_print_time = current_time
            data = bme_geek.air_sensor_data()
            if data == None:
                print("Sensor still initializing...")
            else:
                bme_geek.print_air_sensor(bme_geek.bme680_sensor)
        
        # Small sleep to prevent CPU hogging
        time.sleep(0.1)
    
    def handle_record_mode(self):
        """Handle actions in record mode"""
        # Check if action button is pressed
        action_button_state = GPIO.input(self.ACTION_BUTTON_PIN)
        
        # Button is pressed and wasn't already pressed
        if action_button_state == False and not self.action_button_pressed:
            current_time = time.time()
            if current_time - self.last_button_press > self.DEBOUNCE_TIME:
                self.last_button_press = current_time
                self.action_button_pressed = True
                print("RECORD MODE: Taking a picture!")
                camera_geek.capture_image()
        
        # Button is released
        elif action_button_state == True and self.action_button_pressed:
            self.action_button_pressed = False
        
        # Other continuous tasks for record mode
        print("RECORD MODE: Ready to capture...")
        time.sleep(0.1)
    
    def handle_display_mode(self):
        """Handle actions in display mode"""
        # Check if action button is pressed to cycle through items
        if GPIO.input(self.ACTION_BUTTON_PIN) == False:
            current_time = time.time()
            if current_time - self.last_button_press > self.DEBOUNCE_TIME:
                self.last_button_press = current_time
                
                # Move to next display item
                self.current_display_index = (self.current_display_index + 1) % len(self.display_items)
                print(f"DISPLAY MODE: Showing {self.display_items[self.current_display_index]}")
        
        # Other continuous tasks for display mode
        time.sleep(0.1)
    
    def run(self):
        """Main loop to run the state machine"""
        try:
            print(f"Starting in {self.current_state.name} mode")
            self.on_state_enter()
            
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
                
                time.sleep(0.05)  # Small delay to prevent CPU hogging
                
        except KeyboardInterrupt:
            print("Program terminated by user")
        finally:
            GPIO.cleanup()
            self.cleanup()

    def cleanup(self):
        """Clean up resources before exiting"""
        if hasattr(self, 'voice_assistant'):
            self.voice_assistant.cleanup()
        # Add any other cleanup code here

    def __del__(self):
        """Destructor to clean up resources"""
        self.cleanup()