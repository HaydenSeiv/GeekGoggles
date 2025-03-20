import pvporcupine
import struct
import pyaudio
import threading
import math
import time
import pvrhino

class VoiceGeek:
    def __init__(self, mode_switcher_callback=None, db_check_interval=30, db_alert_callback=None, db_threshold=90):
        # Store callback function to switch modes
        self.mode_switcher_callback = mode_switcher_callback
        self.db_check_interval = db_check_interval
        self.db_alert_callback = db_alert_callback
        self.db_threshold = db_threshold
        
        # Initialize Porcupine
        self.porcupine = None
        self.pa = None
        self.audio_stream = None
        self.voice_thread = None
        self.running = False
        
        # Setup wake word detection
        self.setup_wake_word()

        # set up voice to intent
        self.setup_voice_to_intent()


    def setup_voice_to_intent(self):
        # PicoVoice access code. should probably obfuscate
        access_key = 'M8I9Z/xtWRJC4Woocn3rOJtl+vmoD1Yx6a/ZEZcNbsd/r1SRK3/aTw=='
        contect_path = 'rhino-voice-to-intent/GeekGoggleIntent_en_raspberry-pi_v3_0_0.rhn'

        rhino = pvrhino.create(
            access_key='${ACCESS_KEY}',
            context_path='${CONTEXT_FILE_PATH}'
        )
        

    def setup_wake_word(self):
        """Initialize Porcupine wake word detection"""
        try:
            # PicoVoice access code. should probably obfuscate
            access_key = 'M8I9Z/xtWRJC4Woocn3rOJtl+vmoD1Yx6a/ZEZcNbsd/r1SRK3/aTw=='
            
            #path to PPN file for wake word
            keyword_path = 'Hello-Geek_en_raspberry-pi_v3_0_0.ppn'
            
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[keyword_path]
            )
            
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            
            # Start voice detection in a separate thread
            self.running = True
            self.voice_thread = threading.Thread(target=self.voice_detection_loop, daemon=True)
            self.voice_thread.start()
            
        except Exception as e:
            print(f"Failed to initialize wake word detection: {e}")
            self.porcupine = None

    def voice_detection_loop(self):
        """Continuous loop to detect wake word"""
        try:
            last_db_check = time.time()
            db_check_interval = self.db_check_interval  # seconds
            
            while self.running:
                pcm = struct.unpack_from("h" * self.porcupine.frame_length,
                                       self.audio_stream.read(self.porcupine.frame_length))
                
                # Process wake word detection
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    print("Wake word detected!")
                    # Here you can add logic to handle voice commands
                    ##self.handle_voice_command()
                
                # Check decibel level periodically using the same audio data
                current_time = time.time()
                if current_time - last_db_check >= db_check_interval:
                    db_level = self.calculate_decibel_level(pcm)
                    print(f"Current decibel level: {db_level:.2f} dB")
                    
                    # Check if decibel level exceeds threshold
                    if db_level > self.db_threshold and self.db_alert_callback:
                        print(f"High noise level detected: {db_level:.2f} dB")
                        self.db_alert_callback(f"WARNING: HIGH NOISE LEVEL ({db_level:.1f} dB)\nPLEASE WEAR EAR PROTECTION")
                    
                    last_db_check = current_time
                    
        except Exception as e:
            print(f"Error in voice detection: {e}")

    def calculate_decibel_level(self, audio_data):
        """Calculate decibel level from audio data
        
        Args:
            audio_data: Audio data as unpacked integers
            
        Returns:
            float: The decibel level in dB
        """
        try:
            # Calculate RMS (Root Mean Square)
            rms = sum([x**2 for x in audio_data]) / len(audio_data)
            rms = rms**0.5
            
            # Convert RMS to decibels
            if rms > 0:
                db = 20 * math.log10(rms) + 30
            else:
                db = 0
            
            return db
            
        except Exception as e:
            print(f"Error calculating decibel level: {e}")
            return 0

    def handle_voice_command(self):
        """Handle voice commands after wake word detection"""
        print("Processing voice command...")
        
        # Call the mode switcher callback from GeekModes
        if self.mode_switcher_callback:
            print("Switching mode via voice command")
            self.mode_switcher_callback()
        else:
            print("No mode switcher callback registered")

        #############################################################
        ####Example of using voice commands to do mode such as switch modes
        ### would need more callback for each command
        # """Handle voice commands after wake word detection"""
        # print("Listening for command...")
        
        # # Create a recognizer
        # recognizer = sr.Recognizer()
        
        # try:
        #     # Use the same microphone that's already open
        #     with sr.Microphone() as source:
        #         recognizer.adjust_for_ambient_noise(source)
        #         audio = recognizer.listen(source, timeout=3)
                
        #     # Recognize speech using Google Speech Recognition
        #     command_text = recognizer.recognize_google(audio).lower()
        #     print(f"Recognized: {command_text}")
            
        #     # Process different commands
        #     if "switch mode" in command_text or "next mode" in command_text:
        #         if "switch_mode" in self.callbacks:
        #             self.callbacks["switch_mode"]()
        #     elif "take picture" in command_text or "capture" in command_text:
        #         if "take_picture" in self.callbacks:
        #             self.callbacks["take_picture"]()
        #     # Add more command recognition as needed
        #     else:
        #         print("Command not recognized")
                
        # except sr.WaitTimeoutError:
        #     print("Timeout waiting for command")
        # except sr.UnknownValueError:
        #     print("Could not understand audio")
        # except sr.RequestError as e:
        #     print(f"Could not request results; {e}")
        # except Exception as e:
        #     print(f"Error processing command: {e}")
        ############################################################

    def cleanup(self):
        """Explicitly cleanup resources"""
        self.running = False
        if self.voice_thread and self.voice_thread.is_alive():
            self.voice_thread.join(timeout=1.0)
        if self.audio_stream is not None:
            self.audio_stream.close()
        if self.pa is not None:
            self.pa.terminate()
        if self.porcupine is not None:
            self.porcupine.delete()

    def __del__(self):
        """Attempt cleanup during garbage collection"""
        self.cleanup()
        
def get_audio_sample():
    """Get a sample of audio from the microphone"""
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
    data = stream.read(1024)
    stream.close()
    pa.terminate()
    return data

def check_decibel_level(self):
    """Check the decibel level of the environment
    
    Returns:
        float: The decibel level in dB
    """
    try:
        # Temporarily create a new audio stream to avoid interfering with wake word detection
        temp_pa = pyaudio.PyAudio()
        temp_stream = temp_pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        # Read audio data
        data = temp_stream.read(1024)
        
        # Convert bytes to integers
        audio_data = struct.unpack("h" * 1024, data)
        
        # Calculate RMS (Root Mean Square)
        rms = sum([x**2 for x in audio_data]) / len(audio_data)
        rms = rms**0.5
        
        # Convert RMS to decibels
        # Using a reference value for microphone sensitivity
        # You may need to calibrate this for your specific microphone
        if rms > 0:
            db = 20 * math.log10(rms)
        else:
            db = 0
            
        # Clean up
        temp_stream.close()
        temp_pa.terminate()
        
        return db
        
    except Exception as e:
        print(f"Error checking decibel level: {e}")
        return None

def start_decibel_monitoring(self, interval=30):
    """Start monitoring decibel levels at specified intervals
    
    Args:
        interval (int): Time between measurements in seconds
    """
    import time
    import math
    
    def monitor_loop():
        while self.running:
            db_level = self.check_decibel_level()
            if db_level is not None:
                print(f"Current decibel level: {db_level:.2f} dB")
            time.sleep(interval)
    
    # Start monitoring in a separate thread
    self.db_monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    self.db_monitor_thread.start()
    print(f"Started decibel monitoring every {interval} seconds")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InfoDisplay()
    
    # Initialize VoiceGeek with callbacks
    voice_geek = VoiceGeek(
        mode_switcher_callback=window.set_mode,  # If you want to switch modes by voice
        db_alert_callback=window.show_alert,     # Connect the alert callback
        db_threshold=90                          # Set your desired threshold
    )
    
    sys.exit(app.exec_())
