import subprocess
from datetime import datetime

##########################################################################
###Constants###

#Folder to save images
FOLDER_PIC = "/home/admin/Pictures"  # Folder to save pictures

##########################################################################
###GLOBAL VARIABLES###

##########################################################################

def capture_image():
    """
    This function captures an image and saves it to the FOLDER directory.
    """
    # Get current time for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{FOLDER_PIC}/image_{timestamp}.jpg"
    
    # Use rpicam-still command
    command = f"rpicam-still --output {filename}"
    
    subprocess.run(command, shell=True)
    print(f"Captured {filename}")