#include <stdio.h>
#include <pigpio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>

#define BUTTON_PIN 4    // GPIO pin where the button is connected
#define CAMERA_CMD "rpicam-still --output /home/admin/Pictures/photo_%d.jpg"  // Command to take a picture
#define FOLDER "/home/admin/Pictures"  // Folder to save pictures

// Global state variables
static volatile int last_tick = 0;
static const int DEBOUNCE_TIME = 200; // milliseconds

// Function to take a picture when the button is pressed
void take_picture(int pic_number) {
    char command[256];

    printf("Inside the take_picture function\n");

    // Construct the filename with the picture number
    snprintf(command, sizeof(command), "rpicam-still --output %s/photo_%d.jpg", FOLDER, pic_number);

    // Execute the command to take a picture
    system(command);

    printf("Picture taken and saved as photo_%d.jpg\n", pic_number);
}

// Interrupt handler for button press
void button_isr(int gpio, int level, uint32_t tick) {
    static int pic_number = 1;
    
    // Debounce check
    if (level == FALLING_EDGE) {
        // Calculate time since last interrupt
        int diff = tick - last_tick;
        
        // Ignore interrupts that come too quickly after the last one
        if (diff < DEBOUNCE_TIME * 1000) { // Convert to microseconds
            return;
        }
        
        printf("Button pressed! Taking a picture...\n");
        take_picture(pic_number);
        pic_number++;
        
        // Update last trigger time
        last_tick = tick;
    }
}

int main(void) {
    // Check if program is run with sudo
    if (geteuid() != 0) {
        fprintf(stderr, "This program must be run with sudo privileges.\n");
        return -1;
    }

    // // Clean up any existing pigpio resources
    // printf("Killing all pigpiod\n");
    // system("sudo systemctl stop pigpiod");      // Stop the service properly
    // system("sudo rm -f /var/run/pigpio.pid");  // Remove stale PID file if it exists
    // system("sudo rm -f /dev/pigpio");          // Remove stale pipe file if it exists
    // system("sudo killall -9 pigpiod");         // Force kill any remaining processes
    // sleep(2);                                   // Wait for cleanup

    // //check it isint running 
    // system("ps aux | grep pigpiod");
    // sleep(2);   

    // // Start pigpio daemon using nohup to ensure it stays running
    // printf("Running pigpiod daemon\n");
    // system("sudo nohup pigpiod -g > /dev/null 2>&1 & disown");     // Start with nohup and disown
    // sleep(3);  // Give daemon more time to start

    // //check it is running 
    // system("ps aux | grep pigpiod");
    // sleep(2);   

    // Initialize the pigpio library
    if (gpioInitialise() < 0) {
        fprintf(stderr, "pigpio initialization failed.\n");
        fprintf(stderr, "Try manually running these commands:\n");
        fprintf(stderr, "sudo systemctl restart pigpiod\n");
        return -1;
    }
    printf("pigpio initialized successfully\n");

    // First, try to clear any existing ISR on the pin
    int clear_result = gpioSetISRFunc(BUTTON_PIN, FALLING_EDGE, 0, NULL);
    if (clear_result < 0) {
        fprintf(stderr, "Failed to clear existing ISR (error %d). This is normal if no ISR was set.\n", clear_result);
        // Continue anyway, as this error is expected if no ISR was previously set
    }

    // Set up GPIO for button press (input, with pull-up resistor)
    gpioSetMode(BUTTON_PIN, PI_INPUT);
    gpioSetPullUpDown(BUTTON_PIN, PI_PUD_UP);
    printf("GPIO pin %d configured as input with pull-up\n", BUTTON_PIN);

    // Give the system a moment to settle
    usleep(100000);  // 100ms delay

    // Set up an interrupt 
    int result = gpioSetISRFunc(BUTTON_PIN, FALLING_EDGE, 0, button_isr);
    if (result != 0) {
        fprintf(stderr, "Failed to set up ISR. Error code: %d\n", result);
        fprintf(stderr, "This might be because:\n");
        fprintf(stderr, "1. The pigpio daemon isn't running properly\n");
        fprintf(stderr, "2. There are permission issues\n");
        fprintf(stderr, "3. The GPIO pin is in use\n");
        fprintf(stderr, "Try running: sudo systemctl restart pigpiod\n");
        gpioTerminate();
        return -1;
    }
    printf("ISR setup successful\n");

    // Make sure the pictures directory exists
    system("mkdir -p /home/admin/pictures");

    // Add initial state check
    printf("Current button state: %d\n", gpioRead(BUTTON_PIN));

    // Wait for button press
    printf("Waiting for button press...\n");
    while (1) {
        sleep(1);  // Sleep to reduce CPU usage
    }

    // Cleanup
    gpioTerminate();
    return 0;
}
