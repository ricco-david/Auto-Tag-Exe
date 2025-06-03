from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDateEdit, QTimeEdit, QMessageBox, QTextEdit, QRadioButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, QDate, QTime, QThread, pyqtSignal
import schedule
import time
from PyQt6.QtCore import QThreadPool, QSemaphore
from classes import *
import uuid


class SchedulerThread(QThread):
    task_started = pyqtSignal(str)
    task_finished = pyqtSignal(str)
    task_finished_errors = pyqtSignal(str)
    log_signal = pyqtSignal(str)
    total_processed = pyqtSignal(str, str)

    def __init__(self, scheduled_jobs):
        super().__init__()
        self.scheduled_jobs = scheduled_jobs

    def run(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    # def execute_task(self, page_id, access_token, tag_id_name):
    #     self.task_started.emit(page_id)
    #     self.log_signal.emit(f"[INFO] Task started for Page ID: {page_id}, Tag: {tag_id_name}")
    #     try:
    #         time.sleep(2)  # Simulated task
    #         self.log_signal.emit(f"[INFO] Task completed successfully for Page ID: {page_id}")
    #     except Exception as e:
    #         self.log_signal.emit(f"[ERROR] Error executing task for Page ID {page_id}: {str(e)}")
    #     self.task_finished.emit(page_id)


class SchedulerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Message Scheduler - v5.0.2")
        self.setGeometry(100, 100, 800, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.create_input_form()
        self.create_schedule_table()
        self.create_log_terminal()

        self.schedule_radio.setEnabled(False)  # Temporarily disable scheduling

        self.scheduled_jobs = {}

        self.scheduler_thread = SchedulerThread(self.scheduled_jobs)
        self.scheduler_thread.task_started.connect(self.on_task_started)
        self.scheduler_thread.task_finished.connect(self.on_task_finished)
        self.scheduler_thread.task_finished_errors.connect(self.on_task_finished_with_errors)
        self.scheduler_thread.log_signal.connect(self.append_log)
        self.scheduler_thread.total_processed.connect(self.update_total_processed)
        self.scheduler_thread.start()

        self.thread_pool = QThreadPool()
        self.max_concurrent_tasks = 10  # Set the maximum number of concurrent tasks
        self.task_semaphore = QSemaphore(self.max_concurrent_tasks)

    def create_input_form(self):
        form_layout = QVBoxLayout()

        self.page_id_input = self.create_input_field("Page ID:", form_layout)
        self.access_token_input = self.create_input_field("Access Token:", form_layout)
        
        # Replace Tag ID with Custom Message
        self.custom_message_input = self.create_text_area("Custom Message:", form_layout)
        
        # Add Phone Numbers field
        self.phone_numbers_input = self.create_input_field("Phone Numbers (comma-separated):", form_layout)
        self.phone_numbers_input.setPlaceholderText("e.g., +1234567890, +0987654321, +1122334455")

        # Date Range: Since Date & Until Date
        self.since_date_input = QDateEdit()
        self.since_date_input.setCalendarPopup(True)
        self.since_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(QLabel("Since Date:"))
        form_layout.addWidget(self.since_date_input)

        self.until_date_input = QDateEdit()
        self.until_date_input.setCalendarPopup(True)
        self.until_date_input.setDate(QDate.currentDate())
        form_layout.addWidget(QLabel("Until Date:"))
        form_layout.addWidget(self.until_date_input)

        # Radio buttons for execution mode
        radio_layout = QHBoxLayout()
        self.run_now_radio = QRadioButton("Run Immediately")
        self.schedule_radio = QRadioButton("Schedule") 
        self.run_now_radio.setChecked(True)
        radio_layout.addWidget(QLabel("Execution Mode:"))
        radio_layout.addWidget(self.run_now_radio)
        radio_layout.addWidget(self.schedule_radio)  # Temporarily disabled
        form_layout.addLayout(radio_layout)

        self.run_now_radio.toggled.connect(self.toggle_schedule_fields)

        # Schedule fields
        self.schedule_date_label = QLabel("Schedule Date:")
        self.schedule_date_input = QDateEdit()
        self.schedule_date_input.setCalendarPopup(True)
        self.schedule_date_input.setDate(QDate.currentDate())

        self.schedule_time_label = QLabel("Schedule Time:")
        self.schedule_time_input = QTimeEdit()
        self.schedule_time_input.setTime(QTime.currentTime())

        form_layout.addWidget(self.schedule_date_label)
        form_layout.addWidget(self.schedule_date_input)
        form_layout.addWidget(self.schedule_time_label)
        form_layout.addWidget(self.schedule_time_input)

        # Submit button
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_form)
        form_layout.addWidget(self.submit_button)

        self.layout.addLayout(form_layout)

        # Initial state for schedule fields
        self.toggle_schedule_fields()

    def toggle_schedule_fields(self):
        show = self.schedule_radio.isChecked()
        self.schedule_date_label.setVisible(show)
        self.schedule_date_input.setVisible(show)
        self.schedule_time_label.setVisible(show)
        self.schedule_time_input.setVisible(show)

    def create_schedule_table(self):
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(8)
        self.schedule_table.setHorizontalHeaderLabels(["Process ID", "Page ID", "Message Preview", "Phone Count", "Since", "Until", "Status", "Total Processed"])
        self.layout.addWidget(self.schedule_table)

    def create_log_terminal(self):
        self.log_terminal = QTextEdit()
        self.log_terminal.setReadOnly(True)
        self.log_terminal.setStyleSheet("background-color: black; color: lime; font-family: monospace;")
        self.layout.addWidget(QLabel("Terminal Log:"))
        self.layout.addWidget(self.log_terminal)

    def create_input_field(self, label_text, layout):
        label = QLabel(label_text)
        input_field = QLineEdit()
        input_field.setPlaceholderText(f"Enter {label_text.lower()}")
        layout.addWidget(label)
        layout.addWidget(input_field)
        return input_field

    def create_text_area(self, label_text, layout):
        label = QLabel(label_text)
        text_area = QTextEdit()
        text_area.setPlaceholderText(f"Enter your {label_text.lower()}")
        text_area.setMaximumHeight(100)  # Limit height to keep form compact
        layout.addWidget(label)
        layout.addWidget(text_area)
        return text_area

    def parse_phone_numbers(self, phone_string):
        """Convert comma-separated phone numbers string to array"""
        if not phone_string.strip():
            return []
        
        # Split by comma and clean up each number
        phone_numbers = [phone.strip() for phone in phone_string.split(',')]
        # Filter out empty strings
        phone_numbers = [phone for phone in phone_numbers if phone]
        
        return phone_numbers

    def submit_form(self):
        page_id = self.page_id_input.text()
        access_token = self.access_token_input.text()
        custom_message = self.custom_message_input.toPlainText()
        phone_numbers_string = self.phone_numbers_input.text()
        since_date = self.since_date_input.date().toString("yyyy-MM-dd")
        until_date = self.until_date_input.date().toString("yyyy-MM-dd")

        if not all([page_id, access_token, custom_message, phone_numbers_string]):
            QMessageBox.warning(self, "Input Error", "All fields are required!")
            return

        # Convert phone numbers string to array
        phone_numbers_array = self.parse_phone_numbers(phone_numbers_string)
        
        if not phone_numbers_array:
            QMessageBox.warning(self, "Input Error", "Please enter at least one valid phone number!")
            return

        # Log the parsed phone numbers for verification
        self.append_log(f"[INFO] Parsed {len(phone_numbers_array)} phone numbers: {phone_numbers_array}")

        if self.run_now_radio.isChecked():
            self.run_task_now(page_id, access_token, custom_message, phone_numbers_array, since_date, until_date)
            schedule_time_display = "Now"
        else:
            schedule_date = self.schedule_date_input.date().toString("yyyy-MM-dd")
            schedule_time = self.schedule_time_input.time().toString("HH:mm")
            schedule_datetime = f"{schedule_date} {schedule_time}"

            job = schedule.every().day.at(schedule_time).do(
                self.run_task_now, page_id, access_token, custom_message, phone_numbers_array, since_date, until_date
            )
            self.scheduled_jobs[page_id] = job
            schedule_time_display = schedule_datetime
            self.append_log(f"[INFO] Scheduled task for Page ID: {page_id} at {schedule_time}")

        # QMessageBox.information(self, "Success", "Task submitted successfully!")

    def on_task_started(self, task_id):
        self.update_task_status(task_id, "Running")

    def on_task_finished(self, task_id):
        self.update_task_status(task_id, "Completed")

    def on_task_finished_with_errors(self, task_id):
        self.update_task_status(task_id, "Failed")

    def update_task_status(self, task_id, status):
        for row in range(self.schedule_table.rowCount()):
            if self.schedule_table.item(row, 0) and self.schedule_table.item(row, 0).text() == task_id:
                self.schedule_table.setItem(row, 6, QTableWidgetItem(status))
                break
    
    def update_total_processed(self, task_id, total_processed):
        for row in range(self.schedule_table.rowCount()):
            if self.schedule_table.item(row, 0) and self.schedule_table.item(row, 0).text() == task_id:
                self.schedule_table.setItem(row, 7, QTableWidgetItem(total_processed))
                break

    def append_log(self, message):
        timestamp = time.strftime("[%H:%M:%S]")
        self.log_terminal.append(f"{timestamp} {message}")

    def run_task_now(self, page_id, access_token, custom_message, phone_numbers_array, since_date, until_date):
        task_id = str(uuid.uuid4())  # ✅ generate unique process ID
        worker = TaskWorker(task_id, page_id, access_token, custom_message, phone_numbers_array, since_date, until_date, self.task_semaphore, self.scheduler_thread)
        self.thread_pool.start(worker)
        
        # Create message preview (first 30 characters)
        message_preview = custom_message[:30] + "..." if len(custom_message) > 30 else custom_message
        phone_count = len(phone_numbers_array)

        row_position = self.schedule_table.rowCount()
        self.schedule_table.insertRow(row_position)
        self.schedule_table.setItem(row_position, 0, QTableWidgetItem(task_id))
        self.schedule_table.setItem(row_position, 1, QTableWidgetItem(page_id))
        self.schedule_table.setItem(row_position, 2, QTableWidgetItem(message_preview))
        self.schedule_table.setItem(row_position, 3, QTableWidgetItem(str(phone_count)))
        self.schedule_table.setItem(row_position, 4, QTableWidgetItem(since_date))
        self.schedule_table.setItem(row_position, 5, QTableWidgetItem(until_date))
        self.schedule_table.setItem(row_position, 6, QTableWidgetItem("Queued"))
        self.schedule_table.setItem(row_position, 7, QTableWidgetItem("0"))


def main_app():
    app = QApplication([])
    window = SchedulerApp()
    window.show()
    app.exec()


if __name__ == "__main__":
    main_app()
