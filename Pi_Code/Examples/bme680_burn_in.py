import bme680
import time
from datetime import datetime

# Constants
BURN_IN_TIME_HOURS = 24  # Burn in for 24 hours
SAMPLING_INTERVAL = 1    # Take a measurement every second

def main():
    print(f"Starting BME680 burn-in process for {BURN_IN_TIME_HOURS} hours...")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize the sensor
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError):
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
    
    # Configure the sensor
    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
    
    # Configure gas heating
    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)
    
    # Calculate burn-in duration in seconds
    burn_in_seconds = BURN_IN_TIME_HOURS * 60 * 60
    
    # Track start time
    start_time = time.time()
    end_time = start_time + burn_in_seconds
    
    # Collect burn-in data
    burn_in_data = []
    
    try:
        print("Collecting gas resistance burn-in data...")
        print("Press Ctrl+C to stop the process early")
        
        # Display progress header
        print("\nTimestamp | Elapsed | Remaining | Gas Resistance (Ohms) | Temp (C) | Humidity (%)")
        print("-" * 80)
        
        while time.time() < end_time:
            current_time = time.time()
            elapsed_seconds = current_time - start_time
            remaining_seconds = burn_in_seconds - elapsed_seconds
            
            # Only log if the sensor data is available and heat is stable
            if sensor.get_sensor_data() and sensor.data.heat_stable:
                gas = sensor.data.gas_resistance
                temp = sensor.data.temperature
                humidity = sensor.data.humidity
                burn_in_data.append(gas)
                
                # Calculate time values for display
                elapsed_hours = int(elapsed_seconds // 3600)
                elapsed_minutes = int((elapsed_seconds % 3600) // 60)
                elapsed_seconds = int(elapsed_seconds % 60)
                
                remaining_hours = int(remaining_seconds // 3600)
                remaining_minutes = int((remaining_seconds % 3600) // 60)
                
                # Print status with all information
                print(f"{datetime.now().strftime('%H:%M:%S')} | "
                      f"{elapsed_hours:02d}:{elapsed_minutes:02d}:{elapsed_seconds:02d} | "
                      f"{remaining_hours:02d}:{remaining_minutes:02d} | "
                      f"{gas:.2f} | "
                      f"{temp:.2f} | "
                      f"{humidity:.2f}")
            
            # Sleep for the sampling interval
            time.sleep(SAMPLING_INTERVAL)
            
        # Calculate baseline when complete
        if burn_in_data:
            gas_baseline = sum(burn_in_data[-50:]) / 50.0
            print("\nBurn-in complete!")
            print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Gas baseline: {gas_baseline:.2f} Ohms")
            print(f"Suggested value to use in your code: gas_baseline = {gas_baseline:.2f}")
        else:
            print("No valid data collected during burn-in")
            
    except KeyboardInterrupt:
        # Handle early termination
        print("\nBurn-in process interrupted by user")
        if burn_in_data:
            gas_baseline = sum(burn_in_data[-50:]) / 50.0
            elapsed_hours = (time.time() - start_time) / 3600
            print(f"Partial burn-in completed ({elapsed_hours:.2f} hours)")
            print(f"Gas baseline (partial): {gas_baseline:.2f} Ohms")
        else:
            print("No valid data collected before interruption")
    
    except Exception as e:
        print(f"Error during burn-in: {e}")

if __name__ == "__main__":
    main()