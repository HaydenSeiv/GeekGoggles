import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QHBoxLayout, QWidget, QPushButton, QFileDialog, QDesktopWidget)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QImage, QFont
import datetime



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
        
        # Set up each widget with its own layout
        self.setup_info_widget()
        self.setup_media_widget()
        self.setup_text_widget()
        
        # Add all widgets to main layout (initially hidden)
        self.main_layout.addWidget(self.info_widget)
        self.main_layout.addWidget(self.media_widget)
        self.main_layout.addWidget(self.text_widget)
        self.main_layout.addWidget(self.camera_widget)
        
        # Hide all widgets initially
        self.info_widget.hide()
        self.media_widget.hide()
        self.text_widget.hide()
        self.camera_widget.hide()
        
        # Current display mode (1=info, 2=media, 3=text)
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
        """Set up the info display widget (time, temperature, humidity)"""
        layout = QVBoxLayout(self.info_widget)
        
        # Create time label (large and centered)
        self.time_label = QLabel("Time: Loading...")
        self.time_label.setStyleSheet("font-size: 48pt; font-weight: bold; color: #ffffff;")
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        
        # Add some spacing
        layout.addSpacing(40)
        
        # Create temperature and humidity labels
        self.temp_label = QLabel("Temperature: Loading...")
        self.temp_label.setStyleSheet("font-size: 48pt; color: #ffffff;")
        self.temp_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.temp_label)
        
        self.humidity_label = QLabel("Humidity: Loading...")
        self.humidity_label.setStyleSheet("font-size: 48pt; color: #ffffff;")
        self.humidity_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.humidity_label)
        
        # Add stretch to push everything to the top
        layout.addStretch(1)

    def setup_media_widget(self):
        """Set up the media display widget (images and PDFs)"""
        layout = QVBoxLayout(self.media_widget)
        
        #Create title label
        self.title_label = QLabel("Press Button to Display Next File")
        self.title_label.setStyleSheet("font-size: 48pt; color: #ffffff;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # Create a label for displaying images and PDFs
        self.content_label = QLabel()
        self.content_label.setAlignment(Qt.AlignCenter)
        self.content_label.setStyleSheet("background-color: black; border: 1px solid #cccccc;")
        self.content_label.setMinimumHeight(100)  # Set minimum height for content
        layout.addWidget(self.content_label, 1)  # The '1' gives this widget more space

    def setup_text_widget(self):
        """Set up the text display widget"""
        layout = QVBoxLayout(self.text_widget)
        
        # Create a label for displaying custom text
        self.text_display = QLabel("Custom Text Mode")
        self.text_display.setStyleSheet("font-size: 36pt; padding: 40px; background-color: #f8f8f8;")
        self.text_display.setAlignment(Qt.AlignCenter)
        self.text_display.setWordWrap(True)
        layout.addWidget(self.text_display)

    def set_mode(self, mode):
        """Switch between different display modes
        
        Args:
            mode (int): 1=info, 2=media, 3=text
        """
        # Hide all widgets first
        self.info_widget.hide()
        self.media_widget.hide()
        self.text_widget.hide()
        
        # Show the selected widget
        if mode == 1:  # Info mode
            self.info_widget.show()
            self.update_time()  # Update time immediately
        elif mode == 2:  # Media mode
            self.media_widget.show()
        elif mode == 3:  # Text mode
            self.text_widget.show()
        
        self.current_mode = mode
        print(f"UI switched to mode {mode}")

    def update_time(self):
        """Update the time label with the current time"""
        if self.current_mode == 1:  # Only update if in info mode
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            self.time_label.setText(f"{current_time}\n{current_date}")

    def update_temperature(self, temp):
        """Update the temperature display with the given value"""
        self.temp_label.setText(f"Temperature: {temp}°C")

    def update_humidity(self, hum):
        """Update the humidity display with the given value"""
        self.humidity_label.setText(f"Humidity: {hum}%")

    def display_image(self, image_path):
        """Display an image and switch to media mode"""
        # Switch to media mode
        self.set_mode(2)
        
        # Load and display the image
        pixmap = QPixmap(image_path)
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
        
        # try:
        #     # Open the PDF file using PyMuPDF
        #     doc = pymupdf.open(pdf_path)

        #     # Check if the PDF has the requested page
        #     if doc.page_count > page:
        #         # Get the specified page
        #         page_obj = doc.load_page(page)

        #         # Render the page to a pixmap (image)
        #         pix = page_obj.get_pixmap(matrix=pymupdf.Matrix(2, 2))

        #         # Convert the pixmap to a QImage
        #         if pix.alpha:
        #             img = QImage(pix.samples, pix.width, pix.height,
        #                         pix.stride, QImage.Format_RGBA8888)
        #         else:
        #             img = QImage(pix.samples, pix.width, pix.height,
        #                         pix.stride, QImage.Format_RGB888)

        #         # Convert QImage to QPixmap
        #         pixmap = QPixmap.fromImage(img)

        #         # Scale the pixmap to fit the label
        #         pixmap = self.scale_pixmap(pixmap)

        #         # Store the pixmap to prevent garbage collection
        #         self.current_pixmap = pixmap

        #         # Set the pixmap to the content label
        #         self.content_label.setPixmap(pixmap)

        #         # Close the document to free resources
        #         doc.close()
        #     else:
        #         # Show error if PDF doesn't have the requested page
        #         self.content_label.setText(f"Error: PDF doesn't have page {page+1}")

        # except Exception as e:
        #     # Show error message if PDF couldn't be loaded
        #     self.content_label.setText(f"Error loading PDF: {str(e)}")

    def display_text(self, text, title=""):
        """Display custom text and switch to text mode"""
        # Switch to text mode
        self.set_mode(3)
        
        # Format the text with title if provided
        display_text = f"<h1>{title}</h1>\n\n{text}" if title else text
        
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