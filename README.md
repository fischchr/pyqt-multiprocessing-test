# pyqt-multiprocessing-test
Multiprocessing example in pyQt5. 
GUI elements cannot be updated from subprocesses directly. 
Instead, an intermediate communication worker (a QThread object) is required which pipes the output of the subprocess to the GUI.
