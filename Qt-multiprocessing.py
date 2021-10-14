#! /usr/bin/env python3

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import QObject, QThread, pyqtSlot, pyqtSignal
from PyQt5.uic import loadUi
import time
import sys
import numpy as np
from multiprocessing import Process, Queue


class Subprocess(Process):
    """A subprocess that runs a counter.

    The counter communicates with the GUI via a communication thread.
    """

    def __init__(self, uid: int, com_queue: Queue, out_queue: Queue):
        """Constructor of the subprocess. 
        
        # Arguments
        * uid::int - Unique ID of the counter
        * com_queue::Queue(int) - Command queue. 
        * out_queue::Queue(tuple) - Result queue for returning the counter value to the GUI. 
                                    Returns a tuple (uid, counter).
        """

        # Call constructor of the parent object
        super(Subprocess, self).__init__()

        # Set UID
        self.uid = uid

        # Connect the command and result queues
        self.com_queue = com_queue
        self.out_queue = out_queue

        # Make sure the command queue is initially empty
        while not self.com_queue.empty():
            self.com_queue.get()

    def run(self):
        """Code that runs when the subprocess is started. """

        # Reset counter
        i = 0

        while True:
            # Increase counter
            i += 1
            # Return counter value back to communication thread for display in the GUI
            self.out_queue.put((self.uid, i))

            # Check the command queue
            if self.com_queue.empty():
                # Do some work to load the CPU
                for _ in range(10):
                    np.random.rand(1000, 1000)
            else:
                # Stop the counter
                break


class CommunicationWorker(QObject):
    # Signal for starting the communication thread. Required by Qt
    start_communication_signal = pyqtSignal()

    def __init__(self, counterLabel1: QLabel, counterLabel2: QLabel, com_queue1: Queue, com_queue2: Queue, res_queue: Queue):
        """Constructor of the communication thread. 
        
        # Arguments
        * counterLabel1::QLabel - Label for displaying the value of counter 1.
        * counterLabel2::QLabel - Label for displaying the value of counter 2.
        * com_queue1::Queue - Communication queue for stopping counter1.
        * com_queue2::Queue - Communication queue for stopping counter2.
        * res_queue::Queue - Communication queue for getting back the counter values.
        """

        # Call constructor of parent object
        super(CommunicationWorker, self).__init__()

        # Store the GUI elements for displaying the counter states.
        self.counterLabel1 = counterLabel1
        self.counterLabel2 = counterLabel2
        # Store the command queues for both counters
        self.com_queue1 = com_queue1
        self.com_queue1 = com_queue1
        # Store the result queue
        self.res_queue = res_queue

        # Connect start signal for starting the thread
        self.start_communication_signal.connect(self.run_thread)

        # Set state
        self.running = False

    @pyqtSlot()
    def run_thread(self):
        """Code that runs when the subprocess is started. """

        # Start thread
        self.running = True

        while self.running:
            # Check for results
            if not self.res_queue.empty():
                # Get the uid and the counter value
                (uid, i) = self.res_queue.get()
                if uid == 1:
                    self.counterLabel1.setText(str(i))
                elif uid == 2:
                    self.counterLabel2.setText(str(i))
            else:
                # Idle
                time.sleep(0.01)
            
    def stop_thread(self):
        """Function that is called to stop the communication thread. """

        self.running = False


class MainWindow(QMainWindow):
    def __init__(self):
        """Constructor for main window. """
        # Call constructor of parent object
        super(MainWindow, self).__init__()

        # Load gui
        loadUi('gui.ui', self)   

        # Create result queue which is shared by all subprocesses
        self.res_queue = Queue()

        # Create subprocess 1
        self.com_queue1 = Queue()
        self.subprocess1 = None 

        # Create subprocess 2
        self.com_queue2 = Queue()
        self.subprocess2 = None 

        # Create the communication worker
        self.communication_worker = CommunicationWorker(self.counterLabel1, self.counterLabel2, self.com_queue1, self.com_queue2, self.res_queue)

        # Connect signals for starting and stopping the counters
        self.startButton1.clicked.connect(self.start_process_1)
        self.stopButton1.clicked.connect(self.stop_process_1)
        self.startButton2.clicked.connect(self.start_process_2)
        self.stopButton2.clicked.connect(self.stop_process_2)

        # Create a new thread for the communicaiton worker
        self.communication_thread = QThread(self)
        # Move the communicaiton worker to the new thread
        self.communication_worker.moveToThread(self.communication_thread)
        # Start the thread
        self.communication_thread.start()
        # Start the communication worker
        self.communication_worker.start_communication_signal.emit()

    def start_process_1(self):
        """Start counter 1. """

        # Only start the process if it is not already running
        if self.subprocess1 is None:
            self.subprocess1 = Subprocess(1, self.com_queue1, self.res_queue)
            self.subprocess1.start()

    def stop_process_1(self):
        """Stop counter 1. """

        # Only stop the process if it is running
        if self.subprocess1 is not None:
            # Stop the subprocess
            self.com_queue1.put(0)
            # Wait for it to fully terminate
            self.subprocess1.join()
            # Erase it from memory (a finished process cannot be restarted)
            self.subprocess1 = None
            # Reset GUI label. Sleep to make sure the result queue is empty
            time.sleep(0.05)
            self.counterLabel1.setText('Counter 1 not running')

    def start_process_2(self):
        """Start counter 2. """

        # Only start the process if it is not already running
        if self.subprocess2 is None:
            self.subprocess2 = Subprocess(2, self.com_queue2, self.res_queue)
            self.subprocess2.start()

    def stop_process_2(self):
        """Stop counter 2. """

        # Only stop the process if it is running
        if self.subprocess2 is not None:
            # Stop the subprocess
            self.com_queue2.put(0)
            # Wait for it to fully terminate
            self.subprocess2.join()
            # Erase it from memory (a finished process cannot be restarted)
            self.subprocess2 = None
            # Reset GUI label. Sleep to make sure the result queue is empty
            time.sleep(0.05)
            self.counterLabel2.setText('Counter 2 not running')
  
    def closeEvent(self, event):
        """Terminate all processes and threads when the main window is closed. """

        # Stop the counters
        self.stop_process_1()
        self.stop_process_2()
        # Stop the communication worker
        self.communication_worker.stop_thread()
        # Stop the thread we spawned for the communication worker
        self.communication_thread.quit()
        # Wait for it to fully terminate
        self.communication_thread.wait()


if __name__ == '__main__':
    # Initialize app
    app = QApplication(sys.argv)
    # Initialize window
    main = MainWindow()
    # Show window
    main.show()
    # Start app
    sys.exit(app.exec_())  

