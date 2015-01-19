from subprocess import Popen, PIPE
from re import split
from PyQt5.QtWidgets import *
import sys
from PyQt5.QtCore import *
from threading import Timer
import operator
import subprocess
from PyQt5 import QtCore, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.tableView = QtWidgets.QTableView(self.centralwidget)
        self.tableView.setObjectName("tableView")
        self.gridLayout.addWidget(self.tableView, 1, 0, 1, 3)
        self.buttonKill = QtWidgets.QPushButton(self.centralwidget)
        self.buttonKill.setObjectName("buttonKill")
        self.gridLayout.addWidget(self.buttonKill, 2, 0, 1, 1)
        self.labelInfo = QtWidgets.QLabel(self.centralwidget)
        self.labelInfo.setText("")
        self.labelInfo.setObjectName("labelInfo")
        self.gridLayout.addWidget(self.labelInfo, 0, 0, 1, 3)
        self.closeButton = QtWidgets.QPushButton(self.centralwidget)
        self.closeButton.setObjectName("closeButton")
        self.gridLayout.addWidget(self.closeButton, 2, 2, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 25))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Task Manager"))
        self.buttonKill.setText(_translate("MainWindow", "Kill Process"))
        self.closeButton.setText(_translate("MainWindow", "Quitter"))

class MainWindow(QMainWindow):
    columns = ["User", "Pid", "Cpu", "Memory", "Commande"]
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setup_table()
        self.updater = Updater()
        self.connect_slots()
        self.updater.start()

    def connect_slots(self):
        self.ui.closeButton.clicked.connect(self.on_close_button)
        self.ui.buttonKill.clicked.connect(self.on_kill_button)
        self.updater.updated.connect(self.on_update)

    def on_close_button(self):
        sys.exit(0)

    def on_kill_button(self):
        for index in self.ui.tableView.selectedIndexes():
            if index.column() == 1:
                subprocess.call(["kill", str(index.data())])

    def setup_table(self):
        self.ui.tableView.verticalHeader().hide()
        self.ui.tableView.verticalHeader().setDefaultSectionSize(24)
        self.ui.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableView.setSortingEnabled(True)

    def on_update(self, procs):
        data = []

        for proc in procs:
            data.append([proc.user, proc.pid, proc.cpu, proc.mem, proc.cmd])

        curmodel = self.ui.tableView.model()
        if curmodel is None:
            model = Model(data, MainWindow.columns)
        else:
            model = curmodel
            model.arraydata = data
            if model.order is not None:
                model.sort(model.column, model.order)

        self.ui.tableView.setModel(model)
        self.ui.tableView.resizeColumnsToContents()

class Model(QAbstractTableModel):
    layoutChanged = pyqtSignal()
    layoutAboutToBeChanged = pyqtSignal()

    def __init__(self, datain=None, headerdata=None, parent=None, *args):
        """ datain: a list of lists
            headerdata: a list of strings
        """
        QAbstractTableModel.__init__(self, parent, *args)
        self.arraydata = datain
        self.headerdata = headerdata
        self.order = None
        self.column = None

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.arraydata[index.row()][index.column()])

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.headerdata[col])
        return QVariant()

    def sort(self, Ncol, order):
        """Sort table by given column number.
        """
        self.layoutAboutToBeChanged.emit()
        self.arraydata = sorted(self.arraydata, key=operator.itemgetter(Ncol))

        if order != Qt.DescendingOrder:
            self.arraydata.reverse()

        self.order = order
        self.column = Ncol

        self.layoutChanged.emit()

class Updater(QThread):
    updated = pyqtSignal(list)

    def __init__(self):
        QThread.__init__(self)

    def run(self):
        self.refresh()

    def refresh(self):
        self.updated.emit(get_proc_list())
        Timer(2, self.refresh).start()

class TableItem(QTableWidgetItem):
    def __init__(self, value):
        QTableWidgetItem.__init__(self, str(value))

    def __lt__(self, other):
        if isinstance(other, TableItem):
            try:
                selfDataValue  = float(self.data(Qt.EditRole))
                otherDataValue = float(other.data(Qt.EditRole))
            except ValueError:
                selfDataValue  = self.data(Qt.EditRole)
                otherDataValue = other.data(Qt.EditRole)

            return selfDataValue < otherDataValue
        else:
            return QTableWidgetItem.__lt__(self, other)

    def __str__(self):
        return self.data(Qt.DisplayRole)

class Process:
    """ Data structure for a processes . The class properties are
    process attributes """
    def __init__(self, proc_info):
        self.user = proc_info[0]
        self.pid = int(proc_info[1])
        self.cpu = float(proc_info[2])
        self.mem = float(proc_info[3])
        self.vsz = proc_info[4]
        self.rss = proc_info[5]
        self.tty = proc_info[6]
        self.stat = proc_info[7]
        self.start = proc_info[8]
        self.time = proc_info[9]
        self.cmd = proc_info[10].replace('\n', '')

    def __str__(self):
        """ Returns a string containing minimalistic info
        about the process : user, pid, and command """
        return '%s %s %s' % (self.user, self.pid, self.cmd)

def get_proc_list():
    """ Return a list [] of Proc objects representing the active
    process list list """
    process_list = []
    sub_proc = Popen(['ps', 'aux'], shell=False, stdout=PIPE)
    #Discard the first line (ps aux header)
    sub_proc.stdout.readline()
    for line in sub_proc.stdout:
        #The separator for splitting is 'variable number of spaces'
        proc_info = split(" *", line)
        process_list.append(Process(proc_info))
    return process_list

if __name__ == "__main__":
    app = QApplication(sys.argv)

    w = MainWindow()
    w.show()

    app.exec_()

