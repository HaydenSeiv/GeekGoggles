import os
import sys
import signal
from PyOBEX.server import Server
from PyOBEX.common import OBEXError
import bluetooth

class FileReceiver(Server):
    def __init__(self, address="", port=None):
        super(FileReceiver, self).__init__(address, port)
        self.save_dir = os.path.expanduser("~/bluetooth_received")
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

# Set up server
server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_sock.bind(("", bluetooth.PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]
print(f"Listening on RFCOMM channel {port}")

# Set up service advertising
uuid = "1105"  # OBEX Object Push service UUID
bluetooth.advertise_service(
    server_sock, "OBEX File Transfer",
    service_id=uuid,
    service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
    profiles=[bluetooth.SERIAL_PORT_PROFILE]
)

def signal_handler(sig, frame):
    print("Shutting down server...")
    server_sock.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print("Waiting for connection...")
try:
    while True:
        client_sock, client_info = server_sock.accept()
        print(f"Accepted connection from {client_info}")
        
        file_server = FileReceiver()
        file_server.connect(client_sock)
        
        # Process requests until client disconnects
        try:
            file_server.serve()
        except OBEXError as e:
            print(f"OBEX error: {e}")
        finally:
            file_server.disconnect()
            client_sock.close()
            print("Ready for next connection...")
            
except KeyboardInterrupt:
    print("Shutting down server...")
    server_sock.close()