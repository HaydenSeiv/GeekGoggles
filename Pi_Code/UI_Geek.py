import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QHBoxLayout, QWidget, QPushButton, QFileDialog, QDesktopWidget, QGraphicsProxyWidget, QGraphicsScene, QGraphicsView)
from PyQt5.QtCore import QTimer, Qt, pyqtSlot, QMetaObject, Q_ARG, QVariant, Q_RETURN_ARG
from PyQt5.QtGui import QPixmap, QImage, QFont, QTransform
import datetime
import cv2
import numpy as np
import time
try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except ImportError:
    print("PiCamera2 not available")
    PICAMERA_AVAILABLE = False

#mirror_display = False

class InfoDisplay(QMainWindow):
    def __init__(self):
        # Initialize the parent class
        super().__init__()

        # Set up the main window properties
        self.setWindowTitle("Information Display")
        
        # Set black background for the main window
        self.setStyleSheet("background-color: black;")
        
        # Get the screen size and set the window to fill it
        self.showFullScreen()

        # Create the central widget (required for QMainWindow)
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: black;")
        self.setCentralWidget(self.central_widget)

        # Mirror mode flag (for reflecting display through a mirror)
        #self.mirror_mode = True
        
        # Create the main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create stacked widgets for different modes
        self.info_widget = QWidget()
        self.info_widget.setStyleSheet("background-color: black;")
        self.media_widget = QWidget()
        self.media_widget.setStyleSheet("background-color: black;")
        self.text_widget = QWidget()
        self.text_widget.setStyleSheet("background-color: black;")
        self.camera_widget = QWidget()
        self.camera_widget.setStyleSheet("background-color: black;")
        self.sensor_widget = QWidget()
        self.sensor_widget.setStyleSheet("background-color: black;")
        self.tool_widget = QWidget()
        self.tool_widget.setStyleSheet("background-color: black;")
        
        # Create alert overlay widget
        self.alert_widget = QWidget(self)
        self.alert_widget.setStyleSheet("background-color: rgba(255, 0, 0, 180);")  # Semi-transparent red
        self.alert_widget.setGeometry(self.rect())
        self.setup_alert_widget()
        self.alert_widget.hide()  # Hide initially
        
        # Set up each widget with its own layout
        self.setup_info_widget()
        self.setup_media_widget()
        self.setup_text_widget()
        self.setup_camera_widget()
        self.setup_sensor_widget()
        self.setup_tool_widget()

        # Add all widgets to main layout (initially hidden)
        self.main_layout.addWidget(self.info_widget)
        self.main_layout.addWidget(self.media_widget)
        self.main_layout.addWidget(self.text_widget)
        self.main_layout.addWidget(self.camera_widget)
        self.main_layout.addWidget(self.sensor_widget)
        self.main_layout.addWidget(self.tool_widget)

        # Hide all widgets initially
        self.info_widget.hide()
        self.media_widget.hide()
        self.text_widget.hide()
        self.camera_widget.hide()
        self.sensor_widget.hide()
        self.tool_widget.hide()
        # Current display mode (1=info, 2=media, 3=camera, 4=sensor, 5=text, 6=tool)
        self.current_mode = 0
        
        # Set up a timer to update the time display
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every 1000ms (1 second)

        # Variable to store the current image to prevent garbage collection
        self.current_pixmap = None
        
        # Set initial mode
        self.set_mode(1)  # Start with info mode

    def setup_info_widget(self):
        """Set up the basic display widget (time)"""
        layout = QVBoxLayout(self.info_widget)
        
        # Create time label (large and centered)
        self.time_label = QLabel("Time: Loading...")
        if mirror_display:
            self.time_label.setStyleSheet("font-size: 72pt; font-weight: bold; color: #ffffff; -qt-transform: scale(-1, 1);")
        else:
            self.time_label.setStyleSheet("font-size: 72pt; font-weight: bold; color: #ffffff;")
        self.time_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.time_label)        


    def setup_media_widget(self):
        """Set up the media display widget (images and PDFs)"""
        layout = QVBoxLayout(self.media_widget)
        
        #Create title label
        self.title_label = QLabel("Press Button to Display Next File")        
        if mirror_display:
            self.title_label.setStyleSheet("font-size: 42pt; color: #ffffff; -qt-transform: scale(-1, 1);")
        else:
            self.title_label.setStyleSheet("font-size: 42pt; color: #ffffff;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # Create a label for displaying images and PDFs
        self.content_label = QLabel()
        self.content_label.setAlignment(Qt.AlignCenter)        
        if mirror_display:
            self.content_label.setStyleSheet("font-size: 42pt; color: #ffffff; -qt-transform: scale(-1, 1);")
        else:
            self.content_label.setStyleSheet("background-color: black; border: 1px solid #cccccc;")
        self.content_label.setMinimumHeight(100)  # Set minimum height for content
        layout.addWidget(self.content_label, 1)  # The '1' gives this widget more space

    def setup_text_widget(self):
        """Set up the text display widget"""
        layout = QVBoxLayout(self.text_widget)
        
        # Create a label for displaying custom text
        self.text_display = QLabel("Say record note to Record 10s note")
        self.text_display.setStyleSheet("font-size: 36pt; padding: 40px; color: white;")
        if mirror_display:
            self.text_display.setStyleSheet("font-size: 36pt; padding: 40px; color: white; -qt-transform: scale(-1, 1);")
        else:
            self.text_display.setStyleSheet("font-size: 36pt; padding: 40px; color: white;")
        self.text_display.setAlignment(Qt.AlignCenter)
        self.text_display.setWordWrap(True)
        layout.addWidget(self.text_display)
    
    def setup_camera_widget(self):
        """Set up the camera display widget"""
        layout = QVBoxLayout(self.camera_widget)

        # Create a label for displaying camera feed
        self.camTitle_label = QLabel("Camera")
        self.camTitle_label.setStyleSheet("font-size: 48pt; color: #ffffff;")
        if mirror_display:
            self.camTitle_label.setStyleSheet("font-size: 48pt; color: #ffffff; -qt-transform: scale(-1, 1);")
        else:
            self.camTitle_label.setStyleSheet("font-size: 48pt; color: #ffffff;")
        self.camTitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.camTitle_label)

        # Create a label for displaying camera feed
        self.display_label = QLabel()
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setStyleSheet("background-color: black; border: 1px solid #cccccc;")
        if mirror_display:
            self.display_label.setStyleSheet("background-color: black; border: 1px solid #cccccc; -qt-transform: scale(-1, 1);")
        else:
            self.display_label.setStyleSheet("background-color: black; border: 1px solid #cccccc;")
        self.display_label.setMinimumHeight(100)  # Set minimum height for content
        layout.addWidget(self.display_label, 1)  # The '1' gives this widget more space
        
        # Initialize camera if available
        self.camera = None
        self.camera_timer = QTimer(self)
        self.camera_timer.timeout.connect(self.update_camera_feed)
        
        # Setup camera when entering camera mode
    
    def setup_sensor_widget(self):
        """Set up the sensor display widget"""
        layout = QVBoxLayout(self.sensor_widget)
        
        # Add stretch to push content down from top
        layout.addStretch(1)
        
        # Create temperature and humidity labels
        self.temp_label = QLabel("Temperature: Loading...")
        self.temp_label.setStyleSheet("font-size: 48pt; color: #ffffff;")
        if mirror_display:
            self.temp_label.setStyleSheet("font-size: 48pt; color: #ffffff; -qt-transform: scale(-1, 1);")
        else:
            self.temp_label.setStyleSheet("font-size: 48pt; color: #ffffff;")
        self.temp_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.temp_label)
        
        self.humidity_label = QLabel("Humidity: Loading...")
        self.humidity_label.setStyleSheet("font-size: 48pt; color: #ffffff;")
        self.humidity_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.humidity_label)
        
        # Add stretch to push everything to the top from the bottom, which actually centers since we also push from top
        layout.addStretch(1)

    def update_temperature(self, temp):
        # Convert temp to float before passing to invokeMethod
        try:
            temp_float = float(temp)
            # Use invokeMethod to ensure this runs in the UI thread
            QMetaObject.invokeMethod(self, "_update_temperature",
                                Qt.QueuedConnection,
                                Q_ARG(float, temp_float))
        except (ValueError, TypeError) as e:
            print(f"Error converting temperature: {e}")

    @pyqtSlot(float)
    def _update_temperature(self, temp):
        """Update the temperature display with the given value"""
        self.temp_label.setText(f"Temperature: {temp:05.2f}°C")

    def update_humidity(self, hum):
        """Update the humidity display with the given value"""
        try:
            hum_float = float(hum)
            QMetaObject.invokeMethod(self, "_update_humidity",
                                Qt.QueuedConnection,
                                Q_ARG(float, hum_float))
        except (ValueError, TypeError) as e:
            print(f"Error converting humidity: {e}")
    
    @pyqtSlot(float)
    def _update_humidity(self, hum):
        """Internal method to update humidity (runs in UI thread)"""
        self.humidity_label.setText(f"Humidity: {hum:05.2f}%")

    def setup_tool_widget(self):
        """Set up the sensor display widget"""
        layout = QVBoxLayout(self.tool_widget)
        
        # Add stretch to push content down from top
        layout.addStretch(1)
        
        # Create temperature and humidity labels
        self.tool_label = QLabel("Tool Reading: Loading...")
        self.tool_label.setStyleSheet("font-size: 48pt; color: #ffffff;")
        self.tool_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.tool_label)        
        
        # Add stretch to push everything to the top from the bottom, which actually centers since we also push from top
        layout.addStretch(1)
    
    def update_tool(self, tool_response):
        # Convert string to QVariant
        QMetaObject.invokeMethod(self, "_update_tool",
                            Qt.QueuedConnection,
                            Q_ARG(QVariant, QVariant(tool_response)))
    
    @pyqtSlot(QVariant)
    def _update_tool(self, tool_response):
        response_str = tool_response.toString() if hasattr(tool_response, 'toString') else str(tool_response)
        #print(f"Inside of Update Tool-> value: {response_str}")
        self.tool_label.setText(f"{response_str}")



    def setup_alert_widget(self):
        """Set up the alert overlay widget"""
        layout = QVBoxLayout(self.alert_widget)
        
        # Create alert message
        self.alert_message = QLabel("Warning!")
        self.alert_message.setStyleSheet("font-size: 42pt; font-weight: bold; color: white; background-color: transparent;")
        self.alert_message.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.alert_message)
        
        # Make sure the alert covers the entire window
        self.alert_widget.setAutoFillBackground(True)
        
        # Create a timer for auto-dismissal (but don't start it yet)
        self.alert_timer = QTimer(self)
        self.alert_timer.setSingleShot(True)  # Timer fires only once
        self.alert_timer.timeout.connect(self.hide_alert)  # Connect to hide_alert method

    # Thread safe way to set the mode
    def set_mode(self, mode):
        """Show the alert overlay with optional custom message"""
        # Use invokeMethod to ensure this runs in the UI thread
        QMetaObject.invokeMethod(self, "_set_mode",
                            Qt.QueuedConnection,
                            Q_ARG(int, int(mode)))

    @pyqtSlot(int)
    def _set_mode(self, mode):
        """Switch between different display modes
        
        Args:
            mode (int): 1=info, 2=media, 3=camera, 4=sensor, 5=text
        """
        # Hide all widgets first
        self.info_widget.hide()
        self.media_widget.hide()
        self.text_widget.hide()
        self.camera_widget.hide()
        self.sensor_widget.hide()
        self.tool_widget.hide()
        
        # Show the selected widget
        if mode == 1:  # Info mode
            self.info_widget.show()
            self.update_time()  # Update time immediately
            # Stop camera if it was running
            self.stop_camera()
        elif mode == 2:  # Media mode
            self.media_widget.show()
            # Stop camera if it was running
            self.stop_camera()
        elif mode == 3:  # Camera mode
            self.camera_widget.show()
            self.start_camera()
        elif mode == 4: #sensor mode
            self.sensor_widget.show()
            # Stop camera if it was running
            self.stop_camera()
        elif mode == 5:  # Text mode
            self.text_widget.show()
            # Stop camera if it was running
            self.stop_camera()
        elif mode == 6: #tool mode
            self.tool_widget.show()
        
        self.current_mode = mode
        print(f"UI switched to mode {mode}")
        
    def start_camera(self):
        """Initialize and start the camera feed"""
        if not PICAMERA_AVAILABLE:
            self.display_label.setText("PiCamera not available")
            print("PiCamera not available")
            return
            
        try:
            if self.camera is None:
                self.camera = Picamera2()
                config = self.camera.create_preview_configuration()
                self.camera.configure(config)
                self.camera.start()
                
            # Start the timer to update camera feed
            self.camera_timer.start(100)  # Update every 100ms
            print("Camera started")
        except Exception as e:
            self.display_label.setText(f"Camera error: {str(e)}")
            print(f"Camera error: {str(e)}")
    
    def stop_camera(self):
        """Stop the camera feed"""
        if self.camera_timer.isActive():
            self.camera_timer.stop()
        
        if self.camera is not None:
            try:
                self.camera.stop()
                self.camera.close()
                self.camera = None
                print("Camera stopped")
            except Exception as e:
                print(f"Error stopping camera: {str(e)}")
    
    @pyqtSlot()
    def update_camera_feed(self):
        """Update the camera feed display"""
        if self.camera is None or not PICAMERA_AVAILABLE:
            print("Camera is None or not PICAMERA_AVAILABLE")
            return
            
        try:
            # Capture frame from camera
            frame = self.camera.capture_array()
            
            # Convert frame to RGB format (from BGR)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Create QImage from the frame
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Convert to QPixmap and display
            pixmap = QPixmap.fromImage(image)
            pixmap = self.scale_pixmap(pixmap)            
            self.display_label.setPixmap(pixmap)
        except Exception as e:
            self.display_label.setText(f"Camera feed error: {str(e)}")
            print(f"Camera feed error: {str(e)}")

    def update_time(self):
        """Update the time label with the current time"""
        if self.current_mode == 1:  # Only update if in info mode
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            #current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            self.time_label.setText(f"{current_time}")

    def display_image(self, image_path):
        """Display an image and switch to media mode"""
        # Use invokeMethod to ensure this runs in the UI thread
        QMetaObject.invokeMethod(self, "_display_image",
                            Qt.QueuedConnection,
                            Q_ARG(QVariant, QVariant(image_path)))

    @pyqtSlot(QVariant)
    def _display_image(self, image_path):
        """Display an image and switch to media mode"""
        path_str = image_path.toString() if hasattr(image_path, 'toString') else str(image_path)
        # Switch to media mode
        self.set_mode(2)
        
        # Load and display the image
        pixmap = QPixmap(path_str)
        if not pixmap.isNull():
            pixmap = self.scale_pixmap(pixmap)
            self.current_pixmap = pixmap
            self.content_label.setPixmap(pixmap)
        else:
            self.content_label.setText("Error: Could not load image")

    def display_pdf(self, pdf_path, page=0):
        """Display a PDF page and switch to media mode"""
        # Switch to media mode
        self.set_mode(2)

        # TODO: Implement PDF display - need to figure out a pdf reader 
       
    def display_text(self, text, title=""):
        """Display custom text and switch to text mode"""
        # Use invokeMethod to ensure this runs in the UI thread
        QMetaObject.invokeMethod(self, "_display_text",
                            Qt.QueuedConnection,
                            Q_ARG(QVariant, QVariant(text)),
                            Q_ARG(QVariant, QVariant(title)))

    @pyqtSlot(QVariant, QVariant)
    def _display_text(self, text, title):
        """Display custom text and switch to text mode"""
        text_str = text.toString() if hasattr(text, 'toString') else str(text)
        title_str = title.toString() if hasattr(title, 'toString') else str(title)
        
        # Switch to text mode
        #self.set_mode(5)
        
        # Format the text with title if provided
        display_text = f"<h1>{title_str}</h1>\n\n{text_str}" if title_str else text_str
        
        # Set the text to display
        self.text_display.setText(display_text)

    def scale_pixmap(self, pixmap):
        """Scale a pixmap to fit the content label while maintaining aspect ratio"""
        # Get the size of the content label
        label_size = self.content_label.size()

        # Scale the pixmap to fit within the label while preserving aspect ratio
        scaled_pixmap = pixmap.scaled(
            label_size,  # Target size
            Qt.KeepAspectRatio,  # Keep aspect ratio
            Qt.SmoothTransformation  # Use smooth scaling algorithm
        )

        return scaled_pixmap

    def capture_image(self):
        """Capture an image and return the filename"""
        print("Inside of UI capture image")

        if not PICAMERA_AVAILABLE or self.camera is None:
            print("Camera not available for capture")
            return "Camera not available"
        
        try:          
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            picname = f"pics/image_{timestamp}.jpg"  

            # Make sure the directory exists
            os.makedirs("pics", exist_ok=True)
            
            # Capture the image
            self.camera.capture_file(picname)
            print(f"Image captured and saved to inside of UI capture_image: {picname}")   
            
            # Get the absolute path
            abs_path = os.path.abspath(picname)
            
            print(f"Inside of UI _capture_image:Returning abs_path: {abs_path}")
            return abs_path
        except Exception as e:
            print(f"Error capturing image: {str(e)}")
            return "Picture Error"        

    def show_alert(self, message=None):
        """Show the alert overlay with optional custom message"""
        # Use invokeMethod to ensure this runs in the UI thread
        QMetaObject.invokeMethod(self, "_show_alert",
                               Qt.QueuedConnection,
                               Q_ARG(QVariant, QVariant(message if message else "")))

    @pyqtSlot(QVariant)
    def _show_alert(self, message):
        """Internal method to actually show the alert (runs in UI thread)"""
        message_str = message.toString() if hasattr(message, 'toString') else str(message)
        if message_str:
            self.alert_message.setText(message_str)
        
        # Make sure the alert widget covers the entire window
        self.alert_widget.setGeometry(self.rect())
        self.alert_widget.raise_()  # Bring to front
        self.alert_widget.show()
        
        # Start the timer to auto-dismiss after 5 seconds (5000 ms)
        self.alert_timer.start(5000)

    def hide_alert(self):
        """Hide the alert overlay"""
        self.alert_widget.hide()
        # Make sure the timer is stopped when manually hiding
        if self.alert_timer.isActive():
            self.alert_timer.stop()

    # Add this to handle window resize events
    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        # Make sure the alert widget covers the entire window when resized
        if hasattr(self, 'alert_widget'):
            self.alert_widget.setGeometry(self.rect())

    # def toggle_mirror_mode(self, enable=None):
    #     """Toggle or set mirroring mode for use with a physical mirror
        
    #     Args:
    #         enable (bool, optional): If provided, explicitly enable or disable. 
    #                                 If None, toggles current state.
    #     """
    #     # Use invokeMethod to ensure this runs in the UI thread
    #     QMetaObject.invokeMethod(self, "_toggle_mirror_mode",
    #                         Qt.QueuedConnection,
    #                         Q_ARG(QVariant, QVariant(enable)))
    
    # @pyqtSlot(QVariant)
    # def _toggle_mirror_mode(self, enable):
    #     """Internal method to toggle mirror mode (runs in UI thread)"""
    #     from PyQt5.QtWidgets import QGraphicsProxyWidget, QGraphicsScene, QGraphicsView
        
    #     enable_val = enable.toBool() if hasattr(enable, 'toBool') and not enable.isNull() else None
        
    #     # Toggle state if enable not specified
    #     if enable_val is None:
    #         self.mirror_mode = not self.mirror_mode
    #     else:
    #         self.mirror_mode = enable_val
        
    #     # Remove any existing central widget
    #     old_central = self.centralWidget()
        
    #     if self.mirror_mode:
    #         # Create a graphics scene and view for mirroring
    #         scene = QGraphicsScene()
    #         view = QGraphicsView(scene)
            
    #         # Add the old central widget to the scene via a proxy
    #         proxy = QGraphicsProxyWidget()
    #         proxy.setWidget(old_central)
    #         scene.addItem(proxy)
            
    #         # Scale the scene to flip it horizontally
    #         view.scale(-1, 1)
            
    #         # Center on the scene
    #         view.centerOn(0, 0)
            
    #         # Remove scrollbars
    #         view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    #         view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
    #         # Set the graphics view as the new central widget
    #         self.setCentralWidget(view)
    #     else:
    #         # Just restore the original central widget
    #         self.setCentralWidget(old_central)
        
    #     print(f"Mirror mode {'enabled' if self.mirror_mode else 'disabled'}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InfoDisplay()
    
    # Example of how to use the different modes:
    # window.update_temperature("24.5")
    # window.update_humidity("45")
    # window.display_image("/path/to/image.jpg")
    # window.display_pdf("/path/to/document.pdf")
    # window.display_text("This is some important information to display.", "Announcement")
    
    sys.exit(app.exec_())