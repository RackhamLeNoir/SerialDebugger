
import serial
import sys
import glob

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

class SerialPoll(QObject):
  seriallist = pyqtSignal(list)
  finished = pyqtSignal()

  def __init__(self, parent=None):
    QObject.__init__(self, parent=parent)
    self.running = True

  def __del__(self):
    self.wait()

  def stop(self):
    self.running = False

  def run(self):
    while(self.running):
      ports = Serial.serialPorts()
      self.seriallist.emit(ports)
      QThread.sleep(2)
    self.finished.emit()

class Serial():
  __instance = None

  @staticmethod
  def getInstance():
    if Serial.__instance == None:
      Serial()
    return Serial.__instance

  def __init__(self):
    if Serial.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      Serial.__instance = self
    self.connected = False

  def connect(self, port, baudrate):
    self.disconnect()
    self.port = port
    self.baudrate = baudrate
    self.handle = serial.Serial(self.port, self.baudrate, timeout=1)
    if self.handle:
      self.connected = True

  def disconnect(self):
    if self.connected:
      self.handle.close()
    self.connected = False

  def isConnected(self):
    return self.connected

  def __del__(self):
    self.disconnect()

  def send(self, bytes):
    if self.connected:
      self.handle.write(bytes)

  def readLine(self):
    if self.connected:
      try:
        return self.handle.readline()
      except:
        pass
    return None

  @staticmethod
  def serialPorts():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/ttyUSB*') # ubuntu is /dev/ttyUSB0
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except serial.SerialException as e:
            if e.errno == 13:
                raise e
            pass
        except OSError:
            pass
    return result

class Devices(QComboBox):
  def __init__(self):
    super().__init__()

  def update(self, ports):
    self.clear()
    for port in ports:
      self.addItem(port)
    self.setCurrentText(port)

class Comports(QWidget):
  def __init__(self):
    super().__init__()
    self.setLayout(QVBoxLayout())
    self.layout().setSpacing(0)
    self.layout().setContentsMargins(0,0,0,0)

    self.connectButton = QPushButton('Connect')
    self.connectButton.clicked.connect(self.connect)
    self.refreshButton = QPushButton('Refresh')
    self.refreshButton.clicked.connect(self.update)

    self.layout().addWidget(Devices())
    self.layout().addWidget(self.refreshButton)
    self.layout().addWidget(self.connectButton)

  def connect(self):
    self.connectButton.setText('Disconnect')
    self.connectButton.clicked.connect(self.disconnect)

  def disconnect(self):
    self.connectButton.setText('Connect')
    self.connectButton.clicked.connect(self.connect)
