import modes_geek
import bme_geek
import signal
import sys
import os

##########################################################################
###Constants###

##########################################################################
###GLOBAL VARIABLES###

geek_goggles = None

##########################################################################
def signal_handler(sig, frame):
    """Handle Ctrl+C and other termination signals gracefully"""
    print("\nProgram is shutting down...")
    if geek_goggles:
        geek_goggles.cleanup()
    sys.exit(0)

# Main program
if __name__ == "__main__":
# Set DISPLAY environment variable if not already set
    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"
        print("Setting DISPLAY=:0 for the application")
    
    # Set up signal handler for clean termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    bme_geek.start_bme680_init()
    geek_goggles = modes_geek.GeekModes()
    
    try:
        geek_goggles.run()
    except Exception as e:
        print(f"Error in main program: {e}")
    finally:
        # Ensure cleanup happens even if an exception occurs
        if geek_goggles:
            geek_goggles.cleanup()