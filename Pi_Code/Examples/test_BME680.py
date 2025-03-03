import time
import smbus2
from bme68x import BME68X
from bme68x.constants import *

# Create I2C bus
bus = smbus2.SMBus(1)  # Use 1 for Raspberry Pi (usually), 0 for older versions

# Initialize the BME68X sensor
bme = BME68X(bus, 0x77)  # 0x77 is the default I2C address, use 0x76 if needed

# Configure the sensor
bme.set_conf(CONF_T_P_MODE, BME68X_FORCED_MODE)
bme.set_conf(CONF_HEATER_CONF, 0x00)  # Default heater configuration

# Change this to match the location's pressure (hPa) at sea level
sea_level_pressure = 1000

# Temperature offset (similar to the original code)
temperature_offset = -5

def calculate_altitude(pressure, sea_level):
    """Calculate altitude from pressure using hypsometric formula"""
    return 44330 * (1.0 - pow(pressure / sea_level, 0.1903))

while True:
    # Perform a measurement in forced mode
    bme.set_op_mode(BME68X_FORCED_MODE)
    
    # Wait for the measurement to complete
    time.sleep(0.5)
    
    # Get the data
    data = bme.get_data()
    
    if data:
        temperature = data.temperature + temperature_offset
        gas_resistance = data.gas_resistance
        humidity = data.humidity
        pressure = data.pressure / 100.0  # Convert Pa to hPa
        altitude = calculate_altitude(pressure, sea_level_pressure)
        
        print("\nTemperature: %0.1f C" % temperature)
        print("Gas: %d ohm" % gas_resistance)
        print("Humidity: %0.1f %%" % humidity)
        print("Pressure: %0.3f hPa" % pressure)
        print("Altitude = %0.2f meters" % altitude)
    
    time.sleep(1)