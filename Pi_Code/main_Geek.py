import modes_geek
import bme_geek
import signal
import sys
import os
import traceback


##########################################################################
###Constants###

##########################################################################
###GLOBAL VARIABLES###

geek_goggles = None

def clear_docs_folder():
    """Delete all items in the docs folder"""
    docs_path = os.path.join(os.path.dirname(__file__), 'docs')
    if os.path.exists(docs_path):
        for item in os.listdir(docs_path):
            item_path = os.path.join(docs_path, item)
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)
            except Exception as e:
                print(f"Error deleting {item_path}: {e}")
        print("Docs folder cleared successfully")
    else:
        print("Docs folder not found")
        
def clear_recordings_folder():
    """Delete all items in the recordings folder"""
    recordings_path = os.path.join(os.path.dirname(__file__), 'recordings')
    if os.path.exists(recordings_path):
        for item in os.listdir(recordings_path):
            item_path = os.path.join(recordings_path, item)
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)
            except Exception as e:
                print(f"Error deleting {item_path}: {e}")
        print("Recordings folder cleared successfully")
    else:
        print("Recordings folder not found")

##########################################################################
def signal_handler(sig, frame):
    """Handle Ctrl+C and other termination signals gracefully"""
    print("\nProgram is shutting down...")
    if geek_goggles:
        geek_goggles.cleanup()
    sys.exit(0)

def debug_audio_devices():
    with open("/home/admin/audio_debug.log", "w") as f:
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            f.write(f"Total devices: {p.get_device_count()}\n")
            
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                f.write(f"Device {i}: {info['name']}\n")
                f.write(f"  Inputs: {info['maxInputChannels']}\n")
                f.write(f"  Default: {i == p.get_default_input_device_info()['index']}\n")
            
            default = p.get_default_input_device_info()
            f.write(f"Default input device: {default['index']} - {default['name']}\n")
            
        except Exception as e:
            f.write(f"Error: {str(e)}\n")

# Main program
if __name__ == "__main__":
    # Set DISPLAY environment variable if not already set
    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"
        print("Setting DISPLAY=:0 for the application")
    
    # Clear docs folder at startup
    clear_docs_folder()
    clear_recordings_folder()
    # Set up signal handler for clean termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    bme_geek.start_bme680_init()
    
    geek_goggles = modes_geek.GeekModes()

    debug_audio_devices()
    
    try:
        geek_goggles.run()
    except Exception as e:
        print(f"Error in main program: {e}. Type: {type(e)}")
        traceback.print_exc()
    finally:
        # Ensure cleanup happens even if an exception occurs
        if geek_goggles:
            geek_goggles.cleanup()
        sys.exit(app.exec_())