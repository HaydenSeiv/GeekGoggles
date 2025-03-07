import bluetooth
import os
from PyOBEX.client import Client

def send_file(target_address, file_path):
    # Connect to the device
    client = Client(target_address, 1)  # 1 is the default OBEX port
    client.connect()
    
    # Send the file
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    file_name = os.path.basename(file_path)
    client.put(file_name, file_data)
    
    # Disconnect
    client.disconnect()
    
# Example usage
target_device = "XX:XX:XX:XX:XX:XX"  # Replace with your device's MAC address
file_to_send = "/path/to/your/file.pdf"
send_file(target_device, file_to_send)