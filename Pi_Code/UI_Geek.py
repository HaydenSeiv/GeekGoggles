import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QHBoxLayout, QWidget, QPushButton, QFileDialog, QDesktopWidget)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QImage
import datetime

class InfoDisplay(QMainWindow):
    def __init__(self):
        # Initialize the parent class
        super().__init__()

        # Set up the main window properties
        self.setWindowTitle("Information Display")
        
        # Get the screen size and set the window to fill it
        self.showFullScreen()

        # Create the central widget (required for QMainWindow)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create the main vertical layout for the window
        main_layout = QVBoxLayout(self.central_widget)

        # Create a horizontal layout for time and temperature
        info_layout = QHBoxLayout()
        main_layout.addLayout(info_layout)

        # Create and configure the time label
        self.time_label = QLabel("Time: Loading...")
        self.time_label.setStyleSheet("font-size: 24pt; background-color: #f0f0f0; padding: 10px;")
        self.time_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.time_label)

        # Create and configure the temperature label
        self.temp_label = QLabel("Temperature: Loading...")
        self.temp_label.setStyleSheet("font-size: 24pt; background-color: #f0f0f0; padding: 10px;")
        self.temp_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.temp_label)
        
        # Create and configure the humidity label
        self.humidity_label = QLabel("Humidity: Loading...")
        self.humidity_label.setStyleSheet("font-size: 24pt; background-color: #f0f0f0; padding: 10px;")
        self.humidity_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.humidity_label)

        # Create a label for displaying images and PDFs
        self.content_label = QLabel()
        self.content_label.setAlignment(Qt.AlignCenter)
        self.content_label.setStyleSheet("background-color: white; border: 1px solid #cccccc;")
        self.content_label.setMinimumHeight(400)  # Set minimum height for content
        main_layout.addWidget(self.content_label, 1)  # The '1' gives this widget more space

        # Create a horizontal layout for buttons
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        # Create a button for loading images
        self.load_image_btn = QPushButton("Load Image")
        self.load_image_btn.clicked.connect(self.load_image)  # Connect to the load_image method
        button_layout.addWidget(self.load_image_btn)

        # Create a button for loading PDFs
        self.load_pdf_btn = QPushButton("Load PDF")
        self.load_pdf_btn.clicked.connect(self.load_pdf)  # Connect to the load_pdf method
        button_layout.addWidget(self.load_pdf_btn)

        # Set up a timer to update the time display
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)  # Connect to the update_time method
        self.timer.start(1000)  # Update every 1000ms (1 second)

        # Initialize the time display
        self.update_time()

        # Variable to store the current image to prevent garbage collection
        self.current_pixmap = None

    def set_full_screen_size(self):
        """Set the window size to match the screen dimensions"""
        # Get the screen geometry
        screen = QDesktopWidget().screenGeometry()
        # Set the window geometry to match the screen
        self.setGeometry(0, 0, screen.width(), screen.height())

    def update_time(self):
        """Update the time label with the current time"""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(f"Time: {current_time}")

    def update_temperature(self, temp):
        """Update the temperature display with the given value"""
        self.temp_label.setText(f"Temperature: {temp}°C")

    def update_humidity(self, hum):
        """Update the humidity display with the given value"""
        self.humidity_label.setText(f"Humidity: {hum}%")

    def load_image(self):
        """Open a file dialog to select and display an image"""
        # Show file dialog to select an image file
        file_path, _ = QFileDialog.getOpenFileName(
            self,  # Parent widget
            "Open Image",  # Dialog title
            "",  # Starting directory (empty = current dir)
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"  # File filter
        )

        # If a file was selected (not canceled)
        if file_path:
            # Create a QPixmap from the selected image file
            pixmap = QPixmap(file_path)

            # If the pixmap was loaded successfully
            if not pixmap.isNull():
                # Scale the pixmap to fit the label while maintaining aspect ratio
                pixmap = self.scale_pixmap(pixmap)

                # Store the pixmap to prevent garbage collection
                self.current_pixmap = pixmap

                # Set the pixmap to the content label
                self.content_label.setPixmap(pixmap)
            else:
                # Show error message if image couldn't be loaded
                self.content_label.setText("Error: Could not load image")

    def load_pdf(self):
        """Open a file dialog to select and display the first page of a PDF"""
        # Show file dialog to select a PDF file
        file_path, _ = QFileDialog.getOpenFileName(
            self,  # Parent widget
            "Open PDF",  # Dialog title
            "",  # Starting directory (empty = current dir)
            "PDF Files (*.pdf)"  # File filter
        )

        # TODO: implament a PDF viewer, could not instal pymupdf
        

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
    sys.exit(app.exec_())