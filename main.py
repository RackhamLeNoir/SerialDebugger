import sys
from PyQt5.QtWidgets import *

from MainWindow import *

def main(args):
  app = QApplication(args)
  app.setStyleSheet('''QLineEdit {
      font-family: Courier;
      font-size: 12pt;
      border: none;
      margin: 1px;
      padding: 0px;
      }''')
  mainw = MainWindow()
  mainw.resize(800, 600)
  mainw.show()
  app.aboutToQuit.connect(mainw.cleanUp)

  app.exec_()

if __name__ == "__main__":
  main(sys.argv)
