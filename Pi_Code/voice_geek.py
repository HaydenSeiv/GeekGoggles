import pvporcupine
import struct
import pyaudio
import threading
import math
import time
import pvrhino
import os
import wave
import datetime


class VoiceGeek:
    def __init__(self, mode_switcher_callback=None, db_check_interval=30, db_alert_callback=None, db_threshold=90, note_callback=None, mode_chooser_callback=None, display_mode=None, cycle_item_callback=None, take_pic_callback=None):
        # Store callback function to switch modes
        self.mode_switcher_callback = mode_switcher_callback
        self.db_check_interval = db_check_interval
        self.db_alert_callback = db_alert_callback
        self.db_threshold = db_threshold
        self.next_item_callback = cycle_item_callback
        self.photo_callback = take_pic_callback
        
        #store the call back to jump to a specific mode
        self.mode_chooser_callback = mode_chooser_callback
        
        # Store the note callback
        self.note_callback = note_callback
        
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

        # Set up next item callback
        #self.next_item_callback = display_mode.cycle_display_item if display_mode else None

    def setup_voice_to_intent(self):
        # PicoVoice access code. should probably obfuscate
        access_key = 'M8I9Z/xtWRJC4Woocn3rOJtl+vmoD1Yx6a/ZEZcNbsd/r1SRK3/aTw=='
        context_path = 'rhino-voice-to-intent/GeekGoggleIntent_en_raspberry-pi_v3_0_0.rhn'

        # Store rhino as instance variable
        self.rhino = pvrhino.create(
            access_key=access_key,
            context_path=context_path
        )
        
        # Get and store model parameters
        self.rhino_frame_length = self.rhino.frame_length
        
        # print confirmation
        print(f"Rhino voice-to-intent initialized with context: {context_path}")

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
        """Continuous loop to detect wake word and then process intents"""
        try:
            last_db_check = time.time()
            db_check_interval = self.db_check_interval  # seconds
            # Add a flag to track if we're in intent recognition mode
            listening_for_intent = False
            intent_timeout = 0
            
            while self.running:
                # Read audio frame
                pcm_data = self.audio_stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm_data)
                
                if not listening_for_intent:
                    # Process wake word detection
                    keyword_index = self.porcupine.process(pcm)
                    
                    if keyword_index >= 0:
                        print("Wake word detected! Listening for commands...")
                        # Switch to intent recognition mode
                        listening_for_intent = True
                        intent_timeout = time.time() + 5  # Give 5 seconds to speak a command
                else:
                    # We're in intent recognition mode
                    # Process the audio through Rhino for intent recognition
                    is_finalized = self.rhino.process(pcm)
                    
                    # Check if Rhino has finalized the inference
                    if is_finalized:
                        inference = self.rhino.get_inference()
                        
                        if inference.is_understood:
                            intent = inference.intent
                            slots = inference.slots
                            print(f"Detected intent: {intent}")
                            print(f"With slots: {slots}")
                            
                            # Execute action based on the detected intent
                            self.execute_intent_action(intent, slots)
                        else:
                            print("Command not understood, try again")
                        
                        # Reset intent recognition
                        listening_for_intent = False
                        # Reset Rhino to prepare for next command
                        self.rhino.reset()
                    
                    # Check if we've timed out waiting for a command
                    if time.time() > intent_timeout:
                        print("Command timeout. Say 'Hello Geek' to start again")
                        listening_for_intent = False
                        # Reset Rhino to prepare for next command
                        self.rhino.reset()
                
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


    def record_audio(self, duration=5):
        """Record audio for the specified duration in seconds
        
        Args:
            duration (int): Recording duration in seconds
            
        Returns:
            tuple: (bytes, str) Raw audio data and path to saved WAV file
        """
        try:
            print(f"Recording audio for {duration} seconds...")
            
            # Setup PyAudio for recording
            pa = pyaudio.PyAudio()
            stream = pa.open(
                rate=16000,  # Matches Leopard's expected sample rate
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=8192
            )
            
            # Record audio
            frames = []
            for i in range(0, int(16000 / 8192 * duration)):
                data = stream.read(8192)
                frames.append(data)
            
            # Stop and close the stream
            stream.stop_stream()
            stream.close()
            pa.terminate()
            
            # Combine all frames into a single audio buffer
            audio_data = b''.join(frames)
            
            # Save to WAV file
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'recordings/recording_{timestamp}.wav'
            
            # Create recordings directory if it doesn't exist
            os.makedirs('recordings', exist_ok=True)
            
            # Write WAV file
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
                wf.setframerate(16000)
                wf.writeframes(audio_data)
            
            print(f"Recording complete! Saved to {filename}")
            
            return audio_data, filename
            
        except Exception as e:
            print(f"Error recording audio: {e}")
            return None, None

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
        if hasattr(self, 'rhino') and self.rhino is not None:
            self.rhino.delete()

    def __del__(self):
        """Attempt cleanup during garbage collection"""
        self.cleanup()
        
    def execute_intent_action(self, intent, slots):
        """Execute actions based on detected intent and slots"""
        try:
            print(f"Executing intent: {intent}")
            
            # Handle different intents
            if intent == "next_mode":
                # Switch to the next mode
                if self.mode_switcher_callback:
                    self.mode_switcher_callback()
                else:
                    print("No mode switcher callback registered")
                    
            elif intent == "display":
                if self.mode_chooser_callback:
                    # Pass the mode name from slots to the callback
                    mode = slots['modes']
                    print(f"Switching to {mode} mode")
                    self.mode_chooser_callback(mode)
                else:
                    print("No mode chooser callback registered")
                    
            elif intent == "take_picture":        
                if hasattr(self, 'photo_callback') and self.photo_callback:
                    self.photo_callback()
                else:
                    print("No photo callback registered")
                    
            elif intent == "record_note":
                if hasattr(self, 'note_callback') and self.note_callback:
                    self.note_callback()
                else:
                    print("No note callback registered")
                    
            elif intent == "next":
                if self.next_item_callback:
                    self.next_item_callback()
                else:
                    print("No next item callback registered")
            elif intent == "power_off":
                print("Initiating system shutdown...")
                try:
                    os.system("sudo poweroff")
                except Exception as e:
                    print(f"Failed to shutdown: {e}")
            
            # Add more intents as needed based on Rhino context file
            
        except Exception as e:
            print(f"Error executing intent action: {e}")

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
        # may need to calibrate this
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
