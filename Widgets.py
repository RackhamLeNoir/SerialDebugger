from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from xml.dom import minidom
import xml.etree.ElementTree as et

from functools import partial

from Devices import Serial


class Logger(QPlainTextEdit):
  __instance = None

  @staticmethod
  def getInstance():
    if Logger.__instance == None:
      Logger()
    return Logger.__instance

  def __init__(self):
    super().__init__()
    self.setReadOnly(True)
    if Logger.__instance != None:
      raise Exception("This class is a singleton!")
    else:
      Logger.__instance = self

  def writeMessage(self, message):
    self.appendPlainText(message)

class ItemWidget(QWidget):
  def __init__(self, name):
    super().__init__()
    self.name = name

  def setValue(self, value):
    pass

  def getValue(self):
    pass

  def toXML(self):
    pass

class CharItemWidget(QLineEdit, ItemWidget):
  def __init__(self, name = '', value = '', tooltip=''):
    super().__init__(name)
    self.setValue(value)
    self.setMaxLength(1)
    self.setFixedWidth(15)

  def setValue(self, value):
    if len(value) > 0:
      self.setText(value[0])

  def getValue(self):
    return bytearray(self.text(), 'utf8')

  def toXML(self):
    data = et.Element('param')
    data.set('name', self.name)
    data.set('type', 'char')
    data.set('value', self.text())
    return data

class Uint8ItemWidget(QLineEdit, ItemWidget):
  def __init__(self, name = '', value = 0, tooltip=''):
    super().__init__(name)
    self.setValue(value)
    self.setInputMask('HH')
    self.setFixedWidth(23)

  def setValue(self, value):
    try:
      self.setText(hex(value)[2:].zfill(2))
    except TypeError:
      pass

  def getValue(self):
    return bytearray.fromhex(self.text())

  def toXML(self):
    data = et.Element('param')
    data.set('name', self.name)
    data.set('type', 'uint8')
    data.set('value', str(int(self.text(), 16)))
    return data

class Uint16ItemWidget(QLineEdit, ItemWidget):
  def __init__(self, name = '', value = 0, tooltip=''):
    super().__init__(name)
    self.setValue(value)
    self.setInputMask('HHHH')
    self.setFixedWidth(35)

  def setValue(self, value):
    try:
      self.setText(hex(value)[2:].zfill(4))
    except TypeError:
      pass

  def getValue(self):
    return bytearray.fromhex(self.text())

  def toXML(self):
    data = et.Element('param')
    data.set('name', self.name)
    data.set('type', 'uint16')
    data.set('value', str(int(self.text(), 16)))
    return data

class Params(QWidget):
  def __init__(self):
    super().__init__()
    self.setLayout(QHBoxLayout())
    self.layout().setSpacing(0)
    self.layout().setContentsMargins(0,0,0,0)

  def add(self, widget):
    self.layout().addWidget(widget)

  def getValue(self):
    v = bytearray()
    for p in self.findChildren(ItemWidget):
      v += p.getValue()
    return v

  def toXML(self):
    data = []
    for p in self.findChildren(ItemWidget):
      data.append(p.toXML())
    return data

class Command(QWidget):
  def __init__(self, name, playEnabled):
    super().__init__()

    self.name = name

    self.setLayout(QHBoxLayout())
    self.layout().setSpacing(0)
    self.layout().setContentsMargins(0,0,0,0)
    self.params = Params()
    self.addparamc = QPushButton('+C')
    self.addparam8 = QPushButton('+8')
    self.addparam16 = QPushButton('+16')
    self.removeButton = QPushButton('🅧')
    self.playButton = QPushButton('▶️')
    self.enablePlay(playEnabled)

    self.layout().addWidget(self.params)
    self.layout().addWidget(self.addparamc)
    self.layout().addWidget(self.addparam8)
    self.layout().addWidget(self.addparam16)
    self.layout().addStretch(1)
    self.layout().addWidget(self.removeButton)
    self.layout().addWidget(self.playButton)

    self.addparamc.clicked.connect(partial(self.addChar, name = '', value=''))
    self.addparam8.clicked.connect(partial(self.addUint8, name = '', value=0))
    self.addparam16.clicked.connect(partial(self.addUint16, name = '', value=0))
    self.removeButton.clicked.connect(self.remove)
    self.playButton.clicked.connect(self.send)

  def enablePlay(self, b):
    self.playButton.setEnabled(b)

  def addChar(self, name = '', value=''):
    w = CharItemWidget(name)
    w.setValue(value)
    self.params.add(w)

  def addUint8(self, name = '', value = 0):
    w = Uint8ItemWidget(name)
    w.setValue(value)
    self.params.add(w)

  def addUint16(self, name = '', value = 0):
    w = Uint16ItemWidget(name)
    w.setValue(value)
    self.params.add(w)

  def toXML(self):
    data = et.Element('command')
    data.set('name', self.name)
    paramsdata = self.params.toXML()
    for p in paramsdata:
      data.append(p)
    return data

  def send(self):
    try:
      buffer = self.params.getValue()
      serial = Serial.getInstance()
      serial.send(buffer)
      logger = Logger.getInstance()
      logger.writeMessage('Send: \'' + str(buffer) + '\' (' + ''.join(format(x, '02x') for x in buffer) + ')')
    except ValueError:
      logger = Logger.getInstance()
      logger.writeMessage('Missing values')

  def remove(self):
    self.setParent(None)
    self.deleteLater()

class ListCommands(QWidget):
  def __init__(self):
    super().__init__()
    self.setLayout(QVBoxLayout())
    self.layout().setSpacing(0)
    self.layout().setContentsMargins(0,0,0,0)
    self.playEnabled = False

  def add(self, name=''):
    newcommand = Command(name, self.playEnabled)
    self.layout().addWidget(newcommand)
    return newcommand

  def enablePlay(self, b):
    self.playEnabled = b
    for c in self.findChildren(Command):
      c.enablePlay(b)

  def open(self):
    fileName, _ = QFileDialog.getOpenFileName(self.parentWidget(),  "Open Protocol", ".", "*.xml")
    logger = Logger.getInstance()
    if fileName != '':
      logger.writeMessage('Open ' + fileName)
      # clear current commands
      for c in self.findChildren(Command):
        self.layout().removeWidget(c)
        c.deleteLater()
      # add commands from file
      try:
        data = minidom.parse(fileName)
        commands = data.getElementsByTagName('command')
        for c in commands:
          cw = self.add()
          try:
            cn = c.attributes['name'].value
          except KeyError:
            cn = ''
          logger.writeMessage('Command ' + cn)
          for p in c.getElementsByTagName('param'):
            try:
              ptype = p.attributes['type'].value
              try:
                pvalue = p.attributes['value'].value
              except KeyError:
                pvalue = ''
              try:
                pname = p.attributes['name'].value
              except:
                pname = ''
              logger.writeMessage('Parameter ' + pname + '(' + ptype +') ' + pvalue)
              if ptype == 'char':
                cw.addChar(pname, pvalue)
              elif ptype == 'uint8':
                cw.addUint8(pname, int(pvalue))
              elif ptype == 'uint16':
                cw.addUint16(pname, int(pvalue))
            except KeyError:
              logger.writeMessage('Error in command ' + cn + ': parameter without type')
            except ValueError:
              logger.writeMessage('Error in command ' + cn + ': missing or not numerical value')
      except FileNotFoundError:
        logger.writeMessage('Unknown file ' + fileName)
      except xml.parsers.expat.ExpatError:
        logger.writeMessage('Unknown file structure ' + fileName)

  def save(self):
    fileName, _ = QFileDialog.getSaveFileName(self.parentWidget(), "Save Protocol", ".", "*.xml") 
    logger = Logger.getInstance()
    if fileName != '':
      logger.writeMessage('Save to ' + fileName)
      data = et.Element('device')
      data.set('name', '')
      inputs = et.SubElement(data, 'inputs')
      for c in self.findChildren(Command):
        inputs.append(c.toXML())

      mydata = et.tostring(data)
      logger.writeMessage(str(mydata))
      myfile = open(fileName, 'wb')
      header = bytearray('<?xml version="1.0" encoding="UTF-8"?>', 'UTF8')
      myfile.write(header)
      myfile.write(mydata)
      myfile.close()

