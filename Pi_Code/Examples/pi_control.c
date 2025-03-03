#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <pigpio.h>
#include <unistd.h>


/////////////////////////////////////////////////////////////////////////////////////////////////////////
// Defines and globals
/////////////////////////////////////////////////////////////////////////////////////////////////////////
#define BUTTON_PIN 21  // GPIO21
#define DEBOUNCE_TIME 200000  // Debounce time in microseconds
#define FOLDER "/home/admin/Pictures"  // Folder to save pictures

/////////////////////////////////////////////////////////////////////////////////////////////////////////
// Functions
/////////////////////////////////////////////////////////////////////////////////////////////////////////

/*
    This function captures an image and saves it to the FOLDER directory.
*/
void capture_image() {
    time_t t;
    struct tm *tm_info;
    char filename[100];
    
    // Get current time for filename
    time(&t);
    tm_info = localtime(&t);
    strftime(filename, 100, FOLDER "/image_%Y%m%d_%H%M%S.jpg", tm_info);
    
    // Use raspistill instead of libcamera-still
    char command[200];
    snprintf(command, sizeof(command), 
             "rpicam-still --output %s", filename);
    
    system(command);
    printf("Captured %s\n", filename);
}
/////////////////////////////////////////////////////////////////////////////////////////////////////////
// Main
/////////////////////////////////////////////////////////////////////////////////////////////////////////
int main() {
/////////////////////////////////////////////////////////////////////////////////////////////////////////
// one time inits
/////////////////////////////////////////////////////////////////////////////////////////////////////////
    // Kill any existing pigpiod process and remove pid file
    system("sudo killall pigpiod 2>/dev/null");
    system("sudo rm -f /var/run/pigpio.pid");
    
    // Initialize pigpio
    if (gpioInitialise() < 0) {
        printf("pigpio initialization failed\n");
        return 1;
    }

    // Set up the button pin with pull-up
    gpioSetMode(BUTTON_PIN, PI_INPUT);
    gpioSetPullUpDown(BUTTON_PIN, PI_PUD_UP);

    printf("Camera ready! Press button to take picture...\n");

    uint32_t last_press_time = 0;

/////////////////////////////////////////////////////////////////////////////////////////////////////////
// Main Loop
/////////////////////////////////////////////////////////////////////////////////////////////////////////
    while (1) {
        // Read button state (0 when pressed because of pull-up)
        if (gpioRead(BUTTON_PIN) == 0) {
            uint32_t current_time = gpioTick();
            
            // Simple debouncing
            if (current_time - last_press_time > DEBOUNCE_TIME) {
                capture_image();
                last_press_time = current_time;
            }
        }
        
        time_sleep(0.05); // 50ms delay
    }

    gpioTerminate();
    return 0;
}

