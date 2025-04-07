import modes_geek
import bme_geek
import signal
import sys
import os
import traceback
import keyboard  # Import keyboard module for key events


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

##########################################################################
def signal_handler(sig, frame):
    """Handle Ctrl+C and other termination signals gracefully"""
    print("\nProgram is shutting down...")
    if geek_goggles:
        geek_goggles.cleanup()
    sys.exit(0)

def exit_application():
    """Exit function called when ESC key is pressed"""
    print("\nESC key pressed. Program is shutting down...")
    if geek_goggles:
        geek_goggles.cleanup()
    sys.exit(0)

# Main program
if __name__ == "__main__":
    # Set DISPLAY environment variable if not already set
    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"
        print("Setting DISPLAY=:0 for the application")
    
    # Clear docs folder at startup
    clear_docs_folder()
    
    # Set up signal handler for clean termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register keyboard handler for ESC key
    keyboard.on_press_key('esc', lambda _: exit_application())
    print("Press ESC key at any time to exit the application")
    
    bme_geek.start_bme680_init()
    
    geek_goggles = modes_geek.GeekModes()
    
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