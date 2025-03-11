import os
import sys
import signal
import threading
from PyOBEX.server import Server
from PyOBEX.client import Client
import bluetooth
import time

class FileSender:
    def __init__(self, target_address, target_port):
        self.target_address = target_address
        self.target_port = target_port
        
    def send_file(self, file_path):       
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        print(f"Attempting to connect to {self.target_address} on port {self.target_port}")
        print("Please check your phone for connection prompts...")
        client = Client(self.target_address, self.target_port)
        
        try:
            # Try to connect with more detailed error handling and retry logic
            max_retries = 3
            retry_count = 0
            connected = False
            
            while retry_count < max_retries and not connected:
                try:
                    print(f"Connection attempt {retry_count + 1}/{max_retries}...")
                    client.connect()
                    connected = True
                    print(f"Connected to {self.target_address}")
                except (bluetooth.btcommon.BluetoothError, ConnectionRefusedError) as e:
                    retry_count += 1
                    print(f"Connection attempt failed: {e}")
                    if retry_count < max_retries:
                        print("Waiting for 5 seconds before retrying...")
                        print("Please check your phone for any connection prompts")
                        time.sleep(5)
                    else:
                        print("Failed to connect after multiple attempts")
                        print("Make sure your phone:")
                        print("1. Has Bluetooth turned on and is discoverable")
                        print("2. Has OBEX service running or file transfer enabled")
                        print("3. Is showing a prompt to accept the connection (check notifications)")
                        return
            
            if not connected:
                return
                
            with open(file_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(file_path)
                # Add file size information for debugging
                print(f"Sending file: {file_name} ({len(file_data)} bytes)")
                client.put(file_name, file_data)
                print(f"Sent file: {file_name}")
                
        except Exception as e:
            print(f"Error sending file: {e}")
            # Add more detailed error information
            import traceback
            traceback.print_exc()
        finally:
            try:
                client.disconnect()
            except:
                pass

def send_file_to_device(device_address, file_path, port=1):
    sender = FileSender(device_address, port)
    sender.send_file(file_path)

class FileReceiver(Server):
    def __init__(self, address="", port=None, save_dir_suffix=""):
        super(FileReceiver, self).__init__(address, port)
        self.save_dir = os.path.expanduser(f"~/bluetooth_received{save_dir_suffix}")
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        print(f"Files will be saved to {self.save_dir}")

    def put(self, request):
        name = request.name
        print(f"Receiving file: {name}")
        
        path = os.path.join(self.save_dir, name)
        with open(path, "wb") as f:
            f.write(request.data)
        
        print(f"Saved file to {path}")
        return super(FileReceiver, self).put(request)

def run_server(server_id):
    # Set up server
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)

    port = server_sock.getsockname()[1]
    print(f"Server {server_id} listening on RFCOMM channel {port}")

    # Set up service advertising
    uuid = f"1105{server_id}"  # Slightly different UUID for each server
    bluetooth.advertise_service(
        server_sock, f"OBEX File Transfer {server_id}",
        service_id=uuid,
        service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
        profiles=[bluetooth.SERIAL_PORT_PROFILE]
    )

    print(f"Server {server_id} waiting for connection...")
    try:
        while True:
            client_sock, client_info = server_sock.accept()
            print(f"Server {server_id} accepted connection from {client_info}")
            
            file_server = FileReceiver(save_dir_suffix=f"_{server_id}")
            file_server.connect(client_sock)
            
            # Process requests until client disconnects
            try:
                file_server.serve()
            except Exception as e:
                print(f"OBEX error on server {server_id}: {e}")
            finally:
                file_server.disconnect()
                client_sock.close()
                print(f"Server {server_id} ready for next connection...")
                
    except Exception as e:
        print(f"Error in server {server_id}: {e}")
    finally:
        server_sock.close()
        
def discover_devices():
    print("Searching for nearby Bluetooth devices...")
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True)
    
    if not nearby_devices:
        print("No devices found")
        return None
    
    print("\nAvailable devices:")
    for idx, (addr, name) in enumerate(nearby_devices, 1):
        print(f"{idx}. {name} ({addr})")
    
    return nearby_devices

def connect_to_device():
    devices = discover_devices()
    if not devices:
        return None, None
    
    while True:
        try:
            choice = int(input("\nEnter the number of the device to connect to (0 to cancel) (99 to rescan): "))
            if choice == 0:
                return None, None
            if choice == 99:
                    devices = discover_devices()
                    if not devices:
                        return None, None
            if 1 <= choice <= len(devices):
                addr, name = devices[choice-1]
                print(f"\nConnecting to {name} ({addr})...")
                return addr, name
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

def find_obex_service(device_addr):
    print(f"Searching for OBEX services on {device_addr}...")
    services = bluetooth.find_service(address=device_addr)
    
    print(f"Found {len(services)} services")
    
    # First look for specific OBEX services
    obex_services = []
    for svc in services:
        service_name = svc.get('name', '')
        service_class = svc.get('service-classes', [])
        if (service_name and ('obex' in service_name.lower() or 'file' in service_name.lower())) or \
           any('obex' in str(cls).lower() for cls in service_class):
            obex_services.append(svc)
            print(f"Found OBEX service: {service_name} on port {svc['port']}")
    
    if obex_services:
        return obex_services[0]['port']
    
    # If no specific OBEX service found, try common ports or any available service
    if services:
        # Try to find any service on common OBEX ports
        common_ports = [1, 9, 10, 12]
        for port in common_ports:
            for svc in services:
                if svc['port'] == port:
                    print(f"Found service on common OBEX port {port}: {svc.get('name', 'Unknown')}")
                    return port
        
        # If still not found, just return the first available service port
        print(f"No specific OBEX service found. Trying first available service: {services[0].get('name', 'Unknown')} on port {services[0]['port']}")
        return services[0]['port']
    
    print("No services found. Make sure your phone supports OBEX file transfer and is discoverable.")
    return None

if __name__ == "__main__":
    device_addr, device_name = connect_to_device()
    if device_addr:
        # First try to find the correct port for OBEX
        port = find_obex_service(device_addr)
        
        if port:
            print(f"Using port {port} for file transfer")
            file_path = input("Enter the path to the file you want to send: [enter to default] ") or "/home/admin/GeekGoggles/Pi_Code/Examples/test.txt"
            send_file_to_device(device_addr, file_path, port)
        else:
            print("Could not find appropriate service on the device.")
            print("Do you want to try with the default port (1) anyway? (y/n)")
            if input().lower() == 'y':
                file_path = input("Enter the path to the file you want to send: [enter to default] ") or "/home/admin/GeekGoggles/Pi_Code/Examples/test.txt"
                send_file_to_device(device_addr, file_path)

# Set up signal handler
def signal_handler(sig, frame):
    print("Shutting down servers...")
    sys.exit(0)

# signal.signal(signal.SIGINT, signal_handler)

# # Start two server threads
# server1_thread = threading.Thread(target=run_server, args=(1,))
# server2_thread = threading.Thread(target=run_server, args=(2,))

# server1_thread.daemon = True
# server2_thread.daemon = True

# server1_thread.start()
# server2_thread.start()

# # Keep the main thread alive
# try:
#     while True:
#         signal.pause()
# except KeyboardInterrupt:
#     print("Shutting down...")   