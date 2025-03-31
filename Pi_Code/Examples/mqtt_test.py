import paho.mqtt.client as mqtt

# Callback when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        # Subscribe to topic (you can change "test/topic" to whatever topic you want)
        client.subscribe("#")
        connected = True
    else:
        print("Failed to connect, return code %d\n", rc)
    

# Callback when a message is received from the server
def on_message(client, userdata, msg):
    print(f"Message received on topic {msg.topic}: {msg.payload.decode()}")

# Create an MQTT client instance
client = mqtt.Client()

# Assign callback functions
client.on_connect = on_connect
client.on_message = on_message

con = False

# Connect to the broker (modify these parameters according to your broker)
broker_address = "broker.hivemq.com"  # This is a public test broker
port = 1883
# If your broker requires authentication, uncomment and modify these lines:
# client.username_pw_set("your_username", "your_password")


# Connect to the broker
client.connect(broker_address, port, 60)


# Start the loop to process network traffic
client.loop_forever()
