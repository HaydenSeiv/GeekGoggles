from enum import Enum, auto
import time
import subprocess
import RPi.GPIO as GPIO
import bme680
import threading
from datetime import datetime

##########################################################################
###Constants###

#Folder to save images
FOLDER_PIC = "/home/admin/Pictures"  # Folder to save pictures

##########################################################################
###GLOBAL VARIABLES###

###BME680 Variables###
# Global variable to track initialization status
bme680_ready = False
bme680_sensor = None

# baseline values for BME680
#gas baseline is set in bme680_init() during burn-in process
gas_baseline = 0

# Set the humidity baseline to 30%, roughly my home humidity.
hum_baseline = 30.0

# This sets the balance between humidity and gas reading in the
# calculation of air_quality_score (25:75, humidity:gas)
hum_weighting = 0.25



##########################################################################
# Define the possible states as an Enum
class State(Enum):
    BASIC = auto()    # Display BME680 info and time
    RECORD = auto()   # Take pictures with button press
    DISPLAY = auto()  # Show images/PDFs

class StateMachine:
    def __init__(self):
        # Initialize with default state
        self.current_state = State.BASIC
        
        # Set up button pins
        self.MODE_BUTTON_PIN = 17  # GPIO pin for mode switching
        self.ACTION_BUTTON_PIN = 21  # GPIO pin for actions within modes
        
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
        if self.current_state == State.BASIC:
            self.current_state = State.RECORD
            print("Switched to RECORD mode")
        elif self.current_state == State.RECORD:
            self.current_state = State.DISPLAY
            print("Switched to DISPLAY mode")
        elif self.current_state == State.DISPLAY:
            self.current_state = State.BASIC
            print("Switched to BASIC mode")
        
        # Initialize the new state
        self.on_state_enter()
    
    def on_state_enter(self):
        """Initialize things when entering a state"""
        if self.current_state == State.BASIC:
            # Initialize basic mode display
            print("Initializing basic mode display...")
        elif self.current_state == State.RECORD:
            # Initialize camera for recording
            print("Camera ready for capturing...")
        elif self.current_state == State.DISPLAY:
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
            data = air_sensor_data()
            if data == None:
                print("Sensor still initializing...")
            else:
                print_air_sensor(bme680_sensor)
        
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
                capture_image()
        
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
                if self.current_state == State.BASIC:
                    self.handle_basic_mode()
                elif self.current_state == State.RECORD:
                    self.handle_record_mode()
                elif self.current_state == State.DISPLAY:
                    self.handle_display_mode()
                
                time.sleep(0.05)  # Small delay to prevent CPU hogging
                
        except KeyboardInterrupt:
            print("Program terminated by user")
        finally:
            GPIO.cleanup()

def capture_image():
    """
    This function captures an image and saves it to the FOLDER directory.
    """
    # Get current time for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{FOLDER_PIC}/image_{timestamp}.jpg"
    
    # Use rpicam-still command
    command = f"rpicam-still --output {filename}"
    
    subprocess.run(command, shell=True)
    print(f"Captured {filename}")
    
def bme680_init_thread():
    """
    This function initializes the BME680 sensor and starts the burn-in process.
    """
    #Grab global variables
    global bme680_ready, bme680_sensor, bme680_ready, hum_baseline, gas_baseline, hum_weighting
    
    #try to locate the sensor
    try:
        bme680_sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError):
        bme680_sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

    # These oversampling settings can be tweaked to
    # change the balance between accuracy and noise in
    # the data.
    bme680_sensor.set_humidity_oversample(bme680.OS_2X)
    bme680_sensor.set_pressure_oversample(bme680.OS_4X)
    bme680_sensor.set_temperature_oversample(bme680.OS_8X)
    bme680_sensor.set_filter(bme680.FILTER_SIZE_3)
    bme680_sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

    bme680_sensor.set_gas_heater_temperature(320)
    bme680_sensor.set_gas_heater_duration(150)
    bme680_sensor.select_gas_heater_profile(0)

    # start_time and curr_time ensure that the
    # burn_in_time (in seconds) is kept track of.
    start_time = time.time()
    curr_time = time.time()
    burn_in_time = 60
    
    burn_in_data = []

    try:
        # Collect gas resistance burn-in values, then use the average
        # of the last 50 values to set the upper limit for calculating
        # gas_baseline.
        print('Collecting gas resistance burn-in data for 5 mins\n')
        while curr_time - start_time < burn_in_time:
            curr_time = time.time()
            if bme680_sensor.get_sensor_data() and bme680_sensor.data.heat_stable:
                gas = bme680_sensor.data.gas_resistance
                burn_in_data.append(gas)
                print('Gas: {0} Ohms'.format(gas))
                time.sleep(1)

        gas_baseline = sum(burn_in_data[-50:]) / 50.0
        
        bme680_ready = True
        print('Gas baseline: {0} Ohms, humidity baseline: {1:.2f} %RH\n'.format(
            gas_baseline,
            hum_baseline))
    except Exception as e:
        print(f"Error in bme680_init: {e}")
        return None
    
# Start the initialization in a separate thread
def start_bme680_init():
    init_thread = threading.Thread(target=bme680_init_thread)
    init_thread.daemon = True  # Thread will exit when main program exits
    init_thread.start()
    return init_thread

def air_sensor_data():
    """
    This function reads the air sensor data
    """
    
    if bme680_ready and bme680_sensor.get_sensor_data() and bme680_sensor.data.heat_stable:
        data = bme680_sensor.get_sensor_data()
        return data
    else:
        data = None
        return data
def print_air_sensor(sensor):
    """
    This function prints the air sensor data
    """
    global gas_baseline, hum_baseline, hum_weighting
    
    if sensor.get_sensor_data() and sensor.data.heat_stable:
        gas = sensor.data.gas_resistance
        gas_offset = gas_baseline - gas

        hum = sensor.data.humidity
        hum_offset = hum - hum_baseline

        # Calculate hum_score as the distance from the hum_baseline.
        if hum_offset > 0:
            hum_score = (100 - hum_baseline - hum_offset)
            hum_score /= (100 - hum_baseline)
            hum_score *= (hum_weighting * 100)

        else:
            hum_score = (hum_baseline + hum_offset)
            hum_score /= hum_baseline
            hum_score *= (hum_weighting * 100)

        # Calculate gas_score as the distance from the gas_baseline.
        if gas_offset > 0:
            gas_score = (gas / gas_baseline)
            gas_score *= (100 - (hum_weighting * 100))

        else:
            gas_score = 100 - (hum_weighting * 100)

        # Calculate air_quality_score.
        air_quality_score = hum_score + gas_score

        print('Gas: {0:.2f} Ohms,humidity: {1:.2f} %RH,air quality: {2:.2f}'.format(
            gas,
            hum,
            air_quality_score))

# Main program
if __name__ == "__main__":
    start_bme680_init()
    state_machine = StateMachine()
    state_machine.run()
