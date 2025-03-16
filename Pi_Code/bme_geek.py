import bme680
import threading
import time
from datetime import datetime

##########################################################################
###Constants###
#time gas sensor will spend warming up in seconds
burn_in_time = 10

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

#temprature offset as sensor reads a little high, usually about 5 degrees.
temp_offset = 5
##########################################################################

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
        temp = sensor.data.temperature - temp_offset

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

        print('Gas: {0:.2f} Ohms,humidity: {1:.2f} %RH, air quality: {2:.2f}, temp: {3: .2f}C'.format(
            gas,
            hum,
            air_quality_score,
            temp))

def get_temp(sensor):
    """
    this function returns the current temp measurment
    """     
    global temp_offset
    
    #check if sensor is ready and grab temp
    if sensor.get_sensor_data() and sensor.data.heat_stable:        
        temp = sensor.data.temperature - temp_offset  
        print(f" inside of get_temp: -> output temp: {temp}")
        return temp
    
    return None  # Return None instead of 0 when sensor isn't ready

def get_humidity(sensor):
    """
    this function returns the current humidity measurment
    """ 
    hum = 0   

    #print(f"Inside of get hum bool1: {sensor.get_sensor_data()} bool2: {sensor.data.heat_stable}")
        
    #check if sensor is ready and grab temp
    if sensor.get_sensor_data() and sensor.data.heat_stable:
        hum = sensor.data.humidity   
        print(f" inside of get_humidity: -> output hum: {hum}")
        
    return hum
        
def get_air_quality(sensor):
    """
    this function returns the current air quality measurment
    """ 
    global gas_baseline, hum_baseline, hum_weighting
    
    air_quality_score = 0
    gas = 0
    hum = 0
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
        
    return air_quality_score
         


    
