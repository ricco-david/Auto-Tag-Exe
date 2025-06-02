from PyQt6.QtCore import QRunnable, pyqtSlot
import time
from functions import *

class TaskWorker(QRunnable):
    def __init__(self, task_id, page_id, access_token, tag_id_name, since_date, until_date, semaphore, signals):
        super().__init__()
        self.task_id = task_id
        self.page_id = page_id
        self.access_token = access_token
        self.tag_id_name = tag_id_name
        self.since_date = since_date
        self.until_date = until_date
        self.semaphore = semaphore
        self.signals = signals

    @pyqtSlot()
    def run(self):
        self.semaphore.acquire()
        try:
            self.signals.task_started.emit(self.task_id)
            self.signals.log_signal.emit(f"[INFO] Task started for Process ID: {self.task_id}, Tag: {self.tag_id_name}")
            success = self.this_task()
            if not success:
                self.signals.task_finished_errors.emit(self.task_id)
                
            else:
                self.signals.log_signal.emit(f"[INFO] Task completed successfully for Process ID: {self.task_id}")
                self.signals.task_finished.emit(self.task_id)
        except Exception as e:
            self.signals.log_signal.emit(f"[ERROR] Task error for Process ID {self.task_id}: {str(e)}")
            self.signals.task_finished_errors.emit(self.task_id)
        finally:
            self.semaphore.release()


    def this_task(self):
        return worker(self.task_id, self.page_id, self.access_token, self.tag_id_name, self.since_date, self.until_date, self.signals)
        
        