from PyQt5.QtWidgets import *

from functools import partial

from Widgets import *
from Devices import *

class SerialReader(QObject):
  finished = pyqtSignal()
  message = pyqtSignal(str)

  def __init__(self, parent=None):
    QObject.__init__(self, parent=parent)
    self.running = True

  def __del__(self):
    self.wait()

  def stop(self):
    self.running = False

  def run(self):
    serial = Serial.getInstance()
    while(self.running):
      buffer = serial.readLine()
      if buffer != None and len(buffer) > 0:
        self.message.emit('Received: ' + str(buffer))
      QThread.sleep(1)
    self.finished.emit()

class MainWindow(QMainWindow):
  stopserialpoll = pyqtSignal()
  stopserialread = pyqtSignal()

  def __init__(self):
    super().__init__()

    c = QWidget()
    c.setLayout(QVBoxLayout())
    c.layout().setSpacing(0)
    c.layout().setContentsMargins(0,0,0,0)
    self.setCentralWidget(c)

    self.text = Logger()
    self.command = ListCommands()
    self.addCommand = QPushButton('+')
    self.addCommand.clicked.connect(partial(self.command.add, name = ''))

    c.layout().addWidget(self.text)
    c.layout().addWidget(self.command)
    c.layout().addWidget(self.addCommand)

    self.toolbar = QToolBar()
    self.devices = Devices()
    self.toolbar.addWidget(self.devices)
    self.connectButton = QPushButton('Connect')
    self.toolbar.addWidget(self.connectButton)
    self.connectButton.clicked.connect(self.connect)

    self.threadserialpoll = QThread()
    self.serialpoll = SerialPoll()
    self.stopserialpoll.connect(self.serialpoll.stop)
    self.serialpoll.moveToThread(self.threadserialpoll)
    self.threadserialpoll.started.connect(self.serialpoll.run)
    self.serialpoll.seriallist.connect(self.devices.update)
    self.serialpoll.finished.connect(self.threadserialpoll.quit)
    self.serialpoll.finished.connect(self.serialpoll.deleteLater)
    self.threadserialpoll.finished.connect(self.threadserialpoll.deleteLater)
    self.threadserialpoll.start()

    self.threadserialread = QThread()
    self.serialread = SerialReader()
    self.stopserialread.connect(self.serialread.stop)
    self.serialread.moveToThread(self.threadserialread)
    self.threadserialread.started.connect(self.serialread.run)
    self.serialread.message.connect(self.writeMessage)
    self.serialread.finished.connect(self.threadserialread.quit)
    self.serialread.finished.connect(self.serialread.deleteLater)
    self.threadserialread.finished.connect(self.threadserialread.deleteLater)
    self.threadserialread.start()

    self.addToolBar(self.toolbar)

    bar = self.menuBar()
    fileMenu = bar.addMenu( "File" )

    openAction = QAction("Open…", self)
    openAction.setShortcut("Ctrl+O")
    openAction.setToolTip("Open Protocol")
    openAction.setStatusTip("Open Protocol")
    fileMenu.addAction(openAction)
    openAction.triggered.connect(self.command.open)

    saveAction = QAction("Save…", self)
    saveAction.setShortcut("Ctrl+S")
    saveAction.setToolTip("Save Protocol")
    saveAction.setStatusTip("Save Protocol")
    fileMenu.addAction(saveAction)
    saveAction.triggered.connect(self.command.save)

  def cleanUp(self):
    self.stopserialread.emit()
    self.stopserialpoll.emit()

  def writeMessage(self, message):
    logger = Logger.getInstance()
    logger.writeMessage(message)

  def connect(self):
    # close previous connexion
    serial = Serial.getInstance()
    if serial.isConnected():
      self.disconnect()

    self.connectButton.setEnabled(False)

    self.port = self.devices.currentText()
    logger = Logger.getInstance()
    logger.writeMessage('Connecting to ' + self.port)
    serial.connect(self.port, 9600)
    if serial.isConnected():
      logger.writeMessage('Serial port is connected')
      self.command.enablePlay(True)
      self.connectButton.setText('Disconnect')
      self.connectButton.clicked.connect(self.disconnect)
    else:
      logger.writeMessage('Serial port is not connected')
    self.connectButton.setEnabled(True)

  @pyqtSlot()
  def disconnect(self):
    logger = Logger.getInstance()
    logger.writeMessage('Disconnecting ' + self.port)
    serial = Serial.getInstance()
    serial.disconnect()
    self.port = None
    self.command.enablePlay(False)
    logger.writeMessage('Disconnected')
    self.connectButton.setText('Connect')
    self.connectButton.clicked.connect(self.connect)
