"""
Auto Message Scheduler - Main Application
PyQt6 GUI for scheduling and managing message sending tasks
"""

import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDateEdit, QTimeEdit, QMessageBox, QTextEdit, QRadioButton, 
    QHBoxLayout, QGroupBox, QFormLayout, QSplitter, QCheckBox,
    QProgressBar
)
from PyQt6.QtCore import Qt, QDate, QTime, QThread, pyqtSignal, QRunnable, QObject
from PyQt6.QtGui import QFont, QIcon
import schedule
import time
from PyQt6.QtCore import QThreadPool, QSemaphore
import uuid
import re
import json
from datetime import datetime, timedelta
from worker.auto_message_api import get_page_access_token, get_page_conversations, process_all_pages, get_all_page_ids


class TaskWorkerSignals(QObject):
    """Signals for TaskWorker since QRunnable doesn't inherit from QObject"""
    started = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str, str)
    progress = pyqtSignal(str, int)
    log = pyqtSignal(str)


class TaskWorker(QRunnable):
    """Worker class for executing message sending tasks"""
    def __init__(self, task_id, page_id, access_token, custom_message, 
                 phone_numbers, since_date, until_date, semaphore):
        super().__init__()
        self.task_id = task_id
        self.page_id = page_id
        self.access_token = access_token
        self.custom_message = custom_message
        self.phone_numbers = phone_numbers
        self.since_date = since_date
        self.until_date = until_date
        self.semaphore = semaphore
        self.signals = TaskWorkerSignals()
        self.process_all_pages = False  # Flag to indicate if processing all pages

    def run(self):
        """Execute the task"""
        self.semaphore.acquire()
        try:
            self.signals.started.emit(self.task_id)
            
            if self.process_all_pages:
                self.signals.log.emit(f"[INFO] Starting task {self.task_id} for ALL pages")
                
                # Create a custom print function that filters messages
                def custom_print(*args, **kwargs):
                    message = " ".join(str(arg) for arg in args)
                    # Remove extra newlines and spaces
                    message = message.strip()
                    # Only show specific messages
                    if any(key in message for key in [
                        "Processing Page:",
                        "Processing batch",
                        "MATCH FOUND!",
                        "Matched:"
                    ]):
                        self.signals.log.emit(message)
                
                # Replace the built-in print function
                import builtins
                original_print = builtins.print
                builtins.print = custom_print
                
                try:
                    process_all_pages(
                        self.access_token,
                        target_phones=self.phone_numbers,
                        auto_reply_message=self.custom_message,
                        since_input=f"{self.since_date} 00:00:00",
                        until_input=f"{self.until_date} 23:59:59"
                    )
                finally:
                    # Restore the original print function
                    builtins.print = original_print
            else:
                self.signals.log.emit(f"[INFO] Starting task {self.task_id} for Page ID: {self.page_id}")
                
                # Step 1: Get page access token
                self.signals.log.emit(f"[INFO] Getting page access token for Page ID: {self.page_id}")
                page_access_token = get_page_access_token(self.access_token, self.page_id)
                
                if not page_access_token:
                    raise Exception("Failed to get page access token")
                
                self.signals.log.emit(f"[SUCCESS] Page access token retrieved successfully")
                
                # Step 2: Process conversations and send messages
                self.signals.log.emit(f"[INFO] Processing conversations from {self.since_date} to {self.until_date}")
                
                # Format dates for the API
                since_input = f"{self.since_date} 00:00:00"
                until_input = f"{self.until_date} 23:59:59"
                
                # Create a custom print function that filters messages
                def custom_print(*args, **kwargs):
                    message = " ".join(str(arg) for arg in args)
                    # Remove extra newlines and spaces
                    message = message.strip()
                    # Only show specific messages
                    if any(key in message for key in [
                        "Processing Page:",
                        "Processing batch",
                        "MATCH FOUND!",
                        "Matched:"
                    ]):
                        self.signals.log.emit(message)
                
                # Replace the built-in print function
                import builtins
                original_print = builtins.print
                builtins.print = custom_print
                
                try:
                    # Get conversations and process phone numbers
                    conversations = get_page_conversations(
                        self.page_id,
                        page_access_token,
                        self.access_token,
                        since_input=since_input,
                        until_input=until_input,
                        target_phones=self.phone_numbers,
                        auto_reply_message=self.custom_message
                    )
                finally:
                    # Restore the original print function
                    builtins.print = original_print
                
                if conversations:
                    self.signals.log.emit(f"[SUCCESS] Processed {len(conversations)} conversations")
                else:
                    self.signals.log.emit("[WARNING] No conversations found in the specified date range")
            
            self.signals.finished.emit(self.task_id)
            
        except Exception as e:
            self.signals.error.emit(self.task_id, str(e))
            self.signals.log.emit(f"[ERROR] Task {self.task_id} failed: {str(e)}")
        finally:
            self.semaphore.release()


class SchedulerThread(QThread):
    """Thread for handling scheduled tasks"""
    def __init__(self, scheduled_jobs):
        super().__init__()
        self.scheduled_jobs = scheduled_jobs

    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)


class SchedulerApp(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Message Scheduler - V1.0.2")
        self.setGeometry(100, 100, 1000, 900)
        
        # Initialize variables
        self.scheduled_jobs = {}
        self.task_progress = {}
        self.max_concurrent_tasks = 5
        self.task_semaphore = QSemaphore(self.max_concurrent_tasks)
        self.thread_pool = QThreadPool()
        
        self.setup_ui()
        self.setup_scheduler_thread()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main splitter for better layout
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.central_widget.setLayout(QVBoxLayout())
        self.central_widget.layout().addWidget(main_splitter)
        
        # Top section: Input form
        form_widget = QWidget()
        main_splitter.addWidget(form_widget)
        self.create_input_form(form_widget)
        
        # Middle section: Schedule table
        table_widget = QWidget()
        main_splitter.addWidget(table_widget)
        self.create_schedule_section(table_widget)
        
        # Bottom section: Log terminal
        log_widget = QWidget()
        main_splitter.addWidget(log_widget)
        self.create_log_section(log_widget)
        
        # Set splitter proportions
        main_splitter.setSizes([300, 300, 300])

    def create_input_form(self, parent):
        """Create the input form section"""
        layout = QVBoxLayout(parent)
        
        # Form group
        form_group = QGroupBox("Task Configuration")
        form_layout = QFormLayout(form_group)
        
        # Process all pages checkbox
        self.process_all_pages_checkbox = QCheckBox("Process All Pages")
        self.process_all_pages_checkbox.setChecked(True)  # Set to True by default
        form_layout.addRow("", self.process_all_pages_checkbox)
        
        self.access_token_input = QLineEdit()
        self.access_token_input.setPlaceholderText("Enter Access Token")
        self.access_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Access Token:", self.access_token_input)
        
        self.custom_message_input = QTextEdit()
        self.custom_message_input.setPlaceholderText("Enter your custom message here...")
        self.custom_message_input.setMaximumHeight(80)
        form_layout.addRow("Custom Message:", self.custom_message_input)
        
        self.phone_numbers_input = QLineEdit()
        self.phone_numbers_input.setPlaceholderText("e.g., +1234567890, +0987654321")
        form_layout.addRow("Phone Numbers:", self.phone_numbers_input)
        
        # Date inputs
        self.since_date_input = QDateEdit()
        self.since_date_input.setCalendarPopup(True)
        self.since_date_input.setDate(QDate.currentDate())
        form_layout.addRow("Since Date:", self.since_date_input)
        
        self.until_date_input = QDateEdit()
        self.until_date_input.setCalendarPopup(True)
        self.until_date_input.setDate(QDate.currentDate())
        form_layout.addRow("Until Date:", self.until_date_input)
        
        layout.addWidget(form_group)
        
        # Execution mode group
        mode_group = QGroupBox("Execution Mode")
        mode_layout = QHBoxLayout(mode_group)
        
        self.run_now_radio = QRadioButton("Run Immediately")
        self.schedule_radio = QRadioButton("Schedule for Later")
        self.run_now_radio.setChecked(True)
        
        mode_layout.addWidget(self.run_now_radio)
        mode_layout.addWidget(self.schedule_radio)
        
        layout.addWidget(mode_group)
        
        # Submit button
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_form)
        layout.addWidget(self.submit_button)

    def create_schedule_section(self, parent):
        """Create the schedule table section"""
        layout = QVBoxLayout(parent)
        
        layout.addWidget(QLabel("Active Tasks:"))
        
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(8)
        headers = ["Process ID", "Page ID", "Message Preview", "Phone Count", 
                  "Since", "Until", "Status", "Progress"]
        self.schedule_table.setHorizontalHeaderLabels(headers)
        
        # Adjust column widths
        header = self.schedule_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(self.schedule_table)

    def create_log_section(self, parent):
        """Create the log terminal section"""
        layout = QVBoxLayout(parent)
        
        layout.addWidget(QLabel("Terminal Log:"))
        
        self.log_terminal = QTextEdit()
        self.log_terminal.setReadOnly(True)
        self.log_terminal.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
                border: 1px solid #333;
            }
        """)
        
        layout.addWidget(self.log_terminal)

    def setup_scheduler_thread(self):
        """Setup the scheduler thread"""
        self.scheduler_thread = SchedulerThread(self.scheduled_jobs)
        self.scheduler_thread.start()

    def validate_phone_numbers(self, phone_string):
        """Validate and parse phone numbers"""
        if not phone_string.strip():
            return []
        
        phone_numbers = [phone.strip() for phone in phone_string.split(',')]
        valid_phones = []
        
        # Basic phone number validation
        phone_pattern = re.compile(r'^\+?[\d\s\-\(\)]+$')
        
        for phone in phone_numbers:
            if phone and phone_pattern.match(phone):
                # Remove spaces and formatting, keep only digits and +
                clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
                if len(clean_phone) >= 10:  # Minimum length check
                    valid_phones.append(clean_phone)
        
        return valid_phones

    def submit_form(self):
        """Handle form submission"""
        # Get form data
        access_token = self.access_token_input.text().strip()
        custom_message = self.custom_message_input.toPlainText().strip()
        phone_numbers_string = self.phone_numbers_input.text().strip()
        since_date = self.since_date_input.date().toString("yyyy-MM-dd")
        until_date = self.until_date_input.date().toString("yyyy-MM-dd")
        
        # Debug print for custom message
        print(f"📝 Custom message in form: {custom_message[:50]}..." if custom_message else "No custom message")
        
        # Validation
        if not all([access_token, custom_message, phone_numbers_string]):
            QMessageBox.warning(self, "Input Error", "All fields are required!")
            return
        
        phone_numbers = self.validate_phone_numbers(phone_numbers_string)
        if not phone_numbers:
            QMessageBox.warning(self, "Input Error", 
                              "Please enter at least one valid phone number!\n"
                              "Format: +1234567890 or use commas to separate multiple numbers.")
            return
        
        if len(custom_message) < 10:
            QMessageBox.warning(self, "Input Error", 
                              "Message should be at least 10 characters long!")
            return
        
        # Run task for all pages
        self.run_task_all_pages(access_token, custom_message, phone_numbers, since_date, until_date)
        
        # Clear form
        self.clear_form()

    def clear_form(self):
        """Clear the input form"""
        self.access_token_input.clear()
        self.custom_message_input.clear()
        self.phone_numbers_input.clear()

    def run_task_now(self, page_id, access_token, custom_message, phone_numbers, since_date, until_date):
        """Execute task immediately"""
        task_id = str(uuid.uuid4())[:8]  # Shorter ID for display
        
        # Create worker
        worker = TaskWorker(task_id, page_id, access_token, custom_message, 
                          phone_numbers, since_date, until_date, self.task_semaphore)
        
        # Connect signals
        worker.signals.started.connect(self.on_task_started)
        worker.signals.finished.connect(self.on_task_finished)
        worker.signals.error.connect(self.on_task_error)
        worker.signals.progress.connect(self.on_task_progress)
        worker.signals.log.connect(self.append_log)
        
        # Start worker
        self.thread_pool.start(worker)
        
        # Add to table
        self.add_task_to_table(task_id, page_id, custom_message, len(phone_numbers), 
                              since_date, until_date)

    def add_task_to_table(self, task_id, page_id, message, phone_count, since_date, until_date):
        """Add a task to the schedule table"""
        row_position = self.schedule_table.rowCount()
        self.schedule_table.insertRow(row_position)
        
        # Create message preview
        message_preview = message[:30] + "..." if len(message) > 30 else message
        
        # Populate row
        items = [
            task_id,
            page_id,
            message_preview,
            str(phone_count),
            since_date,
            until_date,
            "Queued",
            "0%"
        ]
        
        for col, item in enumerate(items):
            self.schedule_table.setItem(row_position, col, QTableWidgetItem(item))
        
        # Initialize progress tracking
        self.task_progress[task_id] = 0

    def on_task_started(self, task_id):
        """Handle task started signal"""
        self.update_task_status(task_id, "Running")
        self.append_log(f"[INFO] Task {task_id} started")

    def on_task_finished(self, task_id):
        """Handle task finished signal"""
        self.update_task_status(task_id, "Completed")
        self.update_task_progress(task_id, 100)

    def on_task_error(self, task_id, error_msg):
        """Handle task error signal"""
        self.update_task_status(task_id, "Failed")
        self.append_log(f"[ERROR] Task {task_id}: {error_msg}")

    def on_task_progress(self, task_id, progress):
        """Handle task progress signal"""
        self.update_task_progress(task_id, progress)

    def update_task_status(self, task_id, status):
        """Update task status in table"""
        for row in range(self.schedule_table.rowCount()):
            if (self.schedule_table.item(row, 0) and 
                self.schedule_table.item(row, 0).text() == task_id):
                self.schedule_table.setItem(row, 6, QTableWidgetItem(status))
                break

    def update_task_progress(self, task_id, progress):
        """Update task progress in table"""
        for row in range(self.schedule_table.rowCount()):
            if (self.schedule_table.item(row, 0) and 
                self.schedule_table.item(row, 0).text() == task_id):
                self.schedule_table.setItem(row, 7, QTableWidgetItem(f"{progress}%"))
                break

    def append_log(self, message):
        """Append message to log terminal"""
        timestamp = time.strftime("[%H:%M:%S]")
        self.log_terminal.append(f"{timestamp} {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.log_terminal.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def run_task_all_pages(self, access_token, custom_message, phone_numbers, since_date, until_date):
        """Execute task for all pages"""
        task_id = str(uuid.uuid4())[:8]  # Shorter ID for display
        
        # Debug print for custom message
        print(f"📝 Custom message in main app: {custom_message[:50]}..." if custom_message else "No custom message")
        
        # Create worker
        worker = TaskWorker(task_id, None, access_token, custom_message, 
                          phone_numbers, since_date, until_date, self.task_semaphore)
        worker.process_all_pages = True  # Flag to indicate processing all pages
        
        # Connect signals
        worker.signals.started.connect(self.on_task_started)
        worker.signals.finished.connect(self.on_task_finished)
        worker.signals.error.connect(self.on_task_error)
        worker.signals.progress.connect(self.on_task_progress)
        worker.signals.log.connect(self.append_log)
        
        # Start worker
        self.thread_pool.start(worker)
        
        # Add to table
        self.add_task_to_table(task_id, "ALL PAGES", custom_message, len(phone_numbers), 
                              since_date, until_date)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = SchedulerApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()