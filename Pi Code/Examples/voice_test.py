import pvporcupine
import pyaudio
import struct
import os

# Replace with your actual access key
access_key = 'M8I9Z/xtWRJC4Woocn3rOJtl+vmoD1Yx6a/ZEZcNbsd/r1SRK3/aTw=='# Or hardcode it if you prefer

# Path to your downloaded wake word model (.ppn file)
# Replace with your actual path
wake_word_path = "../Hello-Geek_en_raspberry-pi_v3_0_0.ppn"

def main():
    # Initialize Porcupine with your access key and wake word model
    porcupine = pvporcupine.create(
        access_key=access_key,
        keyword_paths=[wake_word_path]
    )
    
    # Initialize PyAudio
    pa = pyaudio.PyAudio()
    
    # Open audio stream
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )
    
    print("Listening for wake word... (Press Ctrl+C to exit)")
    
    try:
        # Main detection loop
        while True:
            # Read audio frame from the microphone
            pcm = audio_stream.read(porcupine.frame_length)
            # Convert audio data to the format Porcupine expects
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            
            # Process audio frame with Porcupine
            keyword_index = porcupine.process(pcm)
            
            # Check if wake word was detected
            if keyword_index >= 0:
                print("Wake word detected!")
                # You can add additional actions here when wake word is detected
    
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # Clean up resources
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()
        if porcupine is not None:
            porcupine.delete()

if __name__ == "__main__":
    main()
