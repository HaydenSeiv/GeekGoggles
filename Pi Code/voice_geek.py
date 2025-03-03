import pvporcupine
import struct
import pyaudio
import threading

class VoiceGeek:
    def __init__(self, mode_switcher_callback=None):
        # Store callback function to switch modes
        self.mode_switcher_callback = mode_switcher_callback
        
        # Initialize Porcupine
        self.porcupine = None
        self.pa = None
        self.audio_stream = None
        self.voice_thread = None
        self.running = False
        
        # Setup wake word detection
        self.setup_wake_word()

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
            while self.running:
                pcm = struct.unpack_from("h" * self.porcupine.frame_length,
                                       self.audio_stream.read(self.porcupine.frame_length))
                
                keyword_index = self.porcupine.process(pcm)
                
                if keyword_index >= 0:
                    print("Wake word detected!")
                    # Here you can add logic to handle voice commands

                    ########
                    #Uncomment below to handle actual stuff with wake word, most likely will instead want to listen to other words
                    ##self.handle_voice_command()
                    
        except Exception as e:
            print(f"Error in voice detection: {e}")

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