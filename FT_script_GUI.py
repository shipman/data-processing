"""
This is a GUI version of the command-line script to FT time-domain data.
Hopefully this will be easier and more intuitive to use.

The starting point for this code is a script written by Erika Riffe, which
itself was based on a translation of a MathCAD script that I (Steve Shipman)
wrote, and *that* script was based on a script that was ultimately written by
Brooks Pate during my post-doc. Yay!
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial
import numpy as np
import math
import matplotlib
import sys
import copy
matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams

class Ui_Dialog_First_Window(object):
    def setupUi(self, Dialog):

        global FID
        global xdata
        global blank_FID
        global blank_xdata
        global gate_start
        global gate_stop
        global plot_switch

        Dialog.setObjectName("Dialog")
        Dialog.resize(275, 145)

        self.gridLayout = QtWidgets.QGridLayout(Dialog)
        self.gridLayout.setObjectName("gridLayout")
        self.sample_rate_label = QtWidgets.QLabel(Dialog)
        self.sample_rate_label.setObjectName("sample_rate_label")
        self.gridLayout.addWidget(self.sample_rate_label, 0, 0, 1, 1)
        self.sample_rate_input = QtWidgets.QLineEdit(Dialog)
        self.sample_rate_input.setObjectName("sample_rate_input")
        self.sample_rate_input.setToolTip("This is the sampling rate of the data in GS/s.")
        self.sample_rate_input.setText("40") # Default value
        self.gridLayout.addWidget(self.sample_rate_input, 0, 1, 1, 1)
        self.band_select_label = QtWidgets.QLabel(Dialog)
        self.band_select_label.setObjectName("band_select_label")
        self.gridLayout.addWidget(self.band_select_label, 0, 2, 1, 1)
        self.band_select = QtWidgets.QComboBox(Dialog)
        self.band_select.setObjectName("band_select") # Do we have to add a function to deal with it if someone changes the value? No, we only read from this right before using the data, so it should just work.
        self.band_select.setToolTip("This is the band in which the data was collected.")
        self.band_select.addItems(["Low (8.7-13.5 GHz)", "Medium (13.5-18.3 GHz)", "High (18.0-26.5 GHz)"])
        self.gridLayout.addWidget(self.band_select, 0, 3, 1, 2)
        self.use_blank_cb = QtWidgets.QCheckBox(Dialog)
        self.use_blank_cb.setObjectName("use_blank_cb")
        self.use_blank_cb.setToolTip("If checked, use the blank (subtract it from the data file before FT).")
        self.use_blank_cb.setText("Subtract Blank")
        self.use_blank_cb.stateChanged.connect(self.are_we_there_yet)
        self.gridLayout.addWidget(self.use_blank_cb, 0, 5, 1, 1)
        self.font_plus_button = QtWidgets.QPushButton(Dialog)
        self.font_plus_button.setObjectName = "font_plus_button"
        self.font_plus_button.clicked.connect(partial(self.font_plus,Dialog))
        self.gridLayout.addWidget(self.font_plus_button, 0, 6, 1, 1)

        self.gate_start_label = QtWidgets.QLabel(Dialog)
        self.gate_start_label.setObjectName("gate_start_label")
        self.gridLayout.addWidget(self.gate_start_label, 1, 0, 1, 1)
        self.gate_start_input = QtWidgets.QLineEdit(Dialog)
        self.gate_start_input.setObjectName("gate_start_input")
        self.gate_start_input.setToolTip("This is the starting point of the data to process, in microseconds.\nIf this value is negative, it will be reset to 0.0 when spur extraction begins.")
        self.gate_start_input.setText("0.0") # Default value, will need to add checks to make sure this is in-bounds
        self.gridLayout.addWidget(self.gate_start_input, 1, 1, 1, 1)
        self.gate_stop_label = QtWidgets.QLabel(Dialog)
        self.gate_stop_label.setObjectName("gate_stop_label")
        self.gridLayout.addWidget(self.gate_stop_label, 1, 3, 1, 1)
        self.gate_stop_input = QtWidgets.QLineEdit(Dialog)
        self.gate_stop_input.setObjectName("gate_stop_input")
        self.gate_stop_input.setToolTip("This is the end point of the data to process, in microseconds.\nIf this value is greater than the FID duration, it will be set to the time corresponding to the last point in the file.")
        self.gate_stop_input.setText("8.0") # Default value, will need to add checks to make sure this is in-bounds
        self.gridLayout.addWidget(self.gate_stop_input, 1, 4, 1, 1)
        self.full_FID_cb = QtWidgets.QCheckBox(Dialog)
        self.full_FID_cb.setObjectName("full_FID_cb")
        self.full_FID_cb.setToolTip("If checked, use the full FID (ignore the gate start and stop boxes).")
        self.full_FID_cb.setText("Use Full FID")
        self.gridLayout.addWidget(self.full_FID_cb, 1, 5, 1, 1)
        self.full_FID_cb.stateChanged.connect(self.are_we_there_yet)
        self.font_minus_button = QtWidgets.QPushButton(Dialog)
        self.font_minus_button.setObjectName = "font_minus_button"
        self.font_minus_button.clicked.connect(partial(self.font_minus,Dialog))
        self.gridLayout.addWidget(self.font_minus_button, 1, 6, 1, 1)

        self.gridLayout.addWidget(QHLine(), 2, 0, 1, 7)

        self.file_import_label = QtWidgets.QLabel(Dialog)
        self.file_import_label.setObjectName("file_import_label")
        self.gridLayout.addWidget(self.file_import_label, 3, 0, 1, 1)
        self.file_import_input = QtWidgets.QLineEdit(Dialog)
        self.file_import_input.setObjectName("file_import_input")
        self.file_import_input.setToolTip("Name of the data file to be loaded and processed.")
        self.gridLayout.addWidget(self.file_import_input, 3, 1, 1, 3)
        self.browse_import_button = QtWidgets.QPushButton(Dialog)
        self.browse_import_button.setObjectName("browse_import_button")
        self.browse_import_button.clicked.connect(self.browse)
        self.gridLayout.addWidget(self.browse_import_button, 3, 4, 1, 1)
        self.load_button = QtWidgets.QPushButton(Dialog)
        self.load_button.setObjectName("load_button")
        self.load_button.clicked.connect(self.load_input)
        self.gridLayout.addWidget(self.load_button, 3, 5, 1, 1)
        self.load_button.setEnabled(False)
        self.plot_button = QtWidgets.QPushButton(Dialog)
        self.plot_button.setObjectName("plot_button")
        self.plot_button.clicked.connect(self.plot_input)
        self.gridLayout.addWidget(self.plot_button, 3, 6, 1, 1)
        self.plot_button.setEnabled(False)

        self.blank_import_label = QtWidgets.QLabel(Dialog)
        self.blank_import_label.setObjectName("blank_import_label")
        self.gridLayout.addWidget(self.blank_import_label, 4, 0, 1, 1)
        self.blank_import_input = QtWidgets.QLineEdit(Dialog)
        self.blank_import_input.setObjectName("blank_import_input")
        self.blank_import_input.setToolTip("Name of the data file (blank) to be loaded and processed.")
        self.gridLayout.addWidget(self.blank_import_input, 4, 1, 1, 3)
        self.blank_import_input.setEnabled(False)
        self.browse_import_blank_button = QtWidgets.QPushButton(Dialog)
        self.browse_import_blank_button.setObjectName("browse_import_blank_button")
        self.browse_import_blank_button.clicked.connect(self.browse_blank)
        self.gridLayout.addWidget(self.browse_import_blank_button, 4, 4, 1, 1)
        self.browse_import_blank_button.setEnabled(False)
        self.load_blank_button = QtWidgets.QPushButton(Dialog)
        self.load_blank_button.setObjectName("load_blank_button")
        self.load_blank_button.clicked.connect(self.load_blank_input) # May instead want to pass a value to a more generic function...
        self.gridLayout.addWidget(self.load_blank_button, 4, 5, 1, 1)
        self.load_blank_button.setEnabled(False)
        self.plot_blank_button = QtWidgets.QPushButton(Dialog)
        self.plot_blank_button.setObjectName("plot_blank_button")
        self.plot_blank_button.clicked.connect(self.plot_blank_input) # May instead want to pass a value to a more generic function...
        self.gridLayout.addWidget(self.plot_blank_button, 4, 6, 1, 1)
        self.plot_blank_button.setEnabled(False)

        self.file_export_label = QtWidgets.QLabel(Dialog)
        self.file_export_label.setObjectName("file_export_label")
        self.gridLayout.addWidget(self.file_export_label, 5, 0, 1, 1)
        self.file_export_input = QtWidgets.QLineEdit(Dialog)
        self.file_export_input.setObjectName("file_export_input")
        self.file_export_input.setToolTip("Name of the file that data will be saved to.")
        self.gridLayout.addWidget(self.file_export_input, 5, 1, 1, 3)
        self.browse_export_button = QtWidgets.QPushButton(Dialog)
        self.browse_export_button.setObjectName("browse_export_button")
        self.browse_export_button.clicked.connect(self.browse_export)
        self.gridLayout.addWidget(self.browse_export_button, 5, 4, 1, 1)

        self.gridLayout.addWidget(QHLine(), 6, 0, 1, 7)

        self.FT_data_button = QtWidgets.QPushButton(Dialog)
        self.FT_data_button.setObjectName("FT_data_button")
        self.FT_data_button.clicked.connect(self.FT)
        self.gridLayout.addWidget(self.FT_data_button, 7, 0, 1, 4)
        self.FT_data_button.setEnabled(False)
        self.exit_button = QtWidgets.QPushButton(Dialog)
        self.exit_button.setObjectName("exit_button")
        self.exit_button.clicked.connect(app.quit) # Probably should interrupt if haven't saved yet
        self.gridLayout.addWidget(self.exit_button, 7, 4, 1, 2)
        self.indicator = QtWidgets.QPushButton(Dialog) # Hacking a push button to be a status indicator
        self.indicator.setObjectName("indicator")
        self.gridLayout.addWidget(self.indicator, 7, 6, 1, 1)
        self.indicator.setEnabled(False)
        self.indicator.setStyleSheet("background-color:rgb(255,255,255); color:rgb(0,0,0); border: none")
        self.indicator.setText("Not Ready")
        self.indicator.clicked.connect(app.quit)
        
        self.status_window = QtWidgets.QTextEdit(Dialog)
        self.status_window.setObjectName("status_window")
        self.gridLayout.addWidget(self.status_window, 8, 0, 5, 7) # make it big!!!!
        self.status_window.setReadOnly(True)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Fourier Transform"))
        self.sample_rate_label.setText(_translate("Dialog", "Sample Rate (GS/s)"))
        self.band_select_label.setText(_translate("Dialog", "Band"))
        self.font_plus_button.setText(_translate("Dialog", "Increase Font"))
        self.font_minus_button.setText(_translate("Dialog", "Decrease Font"))
        self.file_import_label.setText(_translate("Dialog", "Data File Name"))
        self.browse_import_button.setText(_translate("Dialog", "Browse"))
        self.load_button.setText(_translate("Dialog", "Load Data"))
        self.plot_button.setText(_translate("Dialog", "Plot Data"))
        self.blank_import_label.setText(_translate("Dialog", "Blank File Name"))
        self.browse_import_blank_button.setText(_translate("Dialog", "Browse"))
        self.load_blank_button.setText(_translate("Dialog", "Load Blank"))
        self.plot_blank_button.setText(_translate("Dialog", "Plot Blank"))
        self.gate_start_label.setText(_translate("Dialog", "Gate Start (us)"))
        self.gate_stop_label.setText(_translate("Dialog", "Gate Stop (us)"))
        self.file_export_label.setText(_translate("Dialog", "Output File Name"))
        self.browse_export_button.setText(_translate("Dialog", "Browse"))
        self.FT_data_button.setText(_translate("Dialog", "Fourier Transform!"))
        self.exit_button.setText(_translate("Dialog", "Exit"))

    def font_plus(self,Dialog):
        font = Dialog.font()
        curr_size = font.pointSize()
        new_size = curr_size + 3
        font.setPointSize(new_size)
        self.indicator.setFont(font)
        Dialog.setFont(font)

    def font_minus(self,Dialog):
        font = Dialog.font()
        curr_size = font.pointSize()
        new_size = curr_size - 3
        font.setPointSize(new_size)
        self.indicator.setFont(font)
        Dialog.setFont(font)

    def browse(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName()
        if fileName:
            self.file_import_input.setText(fileName)
            self.load_button.setEnabled(True)
            self.load_button.setFocus()
            self.plot_button.setEnabled(False)
            self.are_we_there_yet()

    def browse_blank(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName()
        if fileName:
            self.blank_import_input.setText(fileName)
            self.load_blank_button.setEnabled(True)
            self.load_blank_button.setFocus()
            self.plot_blank_button.setEnabled(False)
            self.are_we_there_yet()

    def browse_export(self):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName()
        if fileName:
            self.file_export_input.setText(fileName)
            self.are_we_there_yet()

# This function applies appropriate logic to decide whether or not to enable the "do the thing" button.
# It also tries to figure out what the next best step is to do and directs the focus there to help guide the user.
    def are_we_there_yet(self):
        use_blank = self.use_blank_cb.isChecked()
        use_full_FID = self.full_FID_cb.isChecked()

        if use_full_FID: # Basic button enabling set up first, based on checkbox responses.
            self.gate_start_input.setEnabled(False)
            self.gate_stop_input.setEnabled(False)
        else:
            self.gate_start_input.setEnabled(True)
            self.gate_stop_input.setEnabled(True)

        if use_blank:
            self.browse_import_blank_button.setEnabled(True)
            self.blank_import_input.setEnabled(True)
        else:
            self.browse_import_blank_button.setEnabled(False)
            self.load_blank_button.setEnabled(False)
            self.plot_blank_button.setEnabled(False)
            self.blank_import_input.setEnabled(False)

        if self.file_import_input.text() == '':
            self.load_button.setEnabled(False)
            self.plot_button.setEnabled(False)

        if self.blank_import_input.text() == '':
            self.load_blank_button.setEnabled(False)
            self.plot_blank_button.setEnabled(False)

        if self.file_import_input.text() == '': # Now the prioritization logic. Getting data file loaded is most important.
            self.browse_import_button.setFocus()
            self.FT_data_button.setEnabled(False)
            self.indicator.setText("Not Ready")
            return False
        elif self.plot_button.isEnabled() == False:
            self.load_button.setEnabled(True)
            self.load_button.setFocus()
            self.FT_data_button.setEnabled(False)
            self.indicator.setText("Not Ready")
            return False

        if self.file_export_input.text() != '':
            have_export_file = True
        else:
            have_export_file = False

        if use_blank: # Then the blank if there is one.
            if self.blank_import_input.text() == '':
                self.browse_import_blank_button.setFocus()
                self.FT_data_button.setEnabled(False)
                self.indicator.setText("Not Ready")
                return False

            if self.plot_blank_button.isEnabled() and self.plot_button.isEnabled() and have_export_file:
                self.FT_data_button.setEnabled(True)
                self.indicator.setText("Ready")
                self.FT_data_button.setFocus()
                return True
            else:
                self.FT_data_button.setEnabled(False)
                self.indicator.setText("Not Ready")
                if self.plot_button.isEnabled() == False:
                    self.load_button.setFocus()
                    return False
                if self.plot_blank_button.isEnabled() == False:
                    self.load_blank_button.setFocus()
                    return False
                if have_export_file == False:
                    self.browse_export_button.setFocus()
                    return False
        else:
            if self.plot_button.isEnabled() and have_export_file:
                self.FT_data_button.setEnabled(True)
                self.indicator.setText("Ready")
                self.FT_data_button.setFocus()
                return True
            else:
                self.FT_data_button.setEnabled(False)
                self.indicator.setText("Not Ready")
                if self.plot_button.isEnabled() == False:
                    self.load_button.setFocus()
                    return False
                if have_export_file == False:
                    self.browse_export_button.setFocus()
                    return False

    def raise_error(self):
        self.are_we_there_yet()
        self.error_dialog = QtWidgets.QMessageBox()
        self.error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_dialog.setWindowTitle("Something's Wrong!")
        self.error_dialog.setText(self.error_message)
        self.error_dialog.show()

    def load_blank_input(self):
        switch = "blank"
        self.loader(switch)

    def load_input(self):
        switch = "data"
        self.loader(switch)

# This will be the generic loader that can be used for either the data or the blank, with a switch that runs specific code as needed.
    def loader(self,which_one):
        global FID
        global xdata
        global blank_FID
        global blank_xdata

        try:
            sample_rate = float(self.sample_rate_input.text())*1e9
        except:
            self.error_message = "Sample rate should be a float!"
            self.raise_error()
            self.sample_rate_input.setFocus()
            return 0

        row_counter = 0
        temp_FID = []
        temp_xdata = []

        if which_one == "data":
            file_to_open = self.file_import_input.text()

        else: # which_one == "blank"
            file_to_open = self.blank_import_input.text()

        try:
            data_input_file = open(file_to_open)
        except:
            self.error_message = "%s couldn't be opened. Try again with a different file."%(file_to_open)
            self.raise_error()
            return 0

        try:
            for row in data_input_file:
                temp=row.split()
                temp_FID.append(float(temp[np.size(temp)-1]))
                temp_xdata.append((row_counter/sample_rate)*1e6) # to put it in microseconds
                row_counter += 1
            if self.full_FID_cb.isChecked():
                self.gate_start_input.setText(str(temp_xdata[0]))
                self.gate_stop_input.setText(str(temp_xdata[-1]))
                self.gate_start_input.setEnabled(False)
                self.gate_stop_input.setEnabled(False)
        except:
            self.error_message = "Data from a file (%s) couldn't be properly processed; try again with a different file."%(file_to_open)
            self.raise_error()
            return 0
        else:
            if which_one == "data":
                FID = copy.copy(temp_FID)
                xdata = copy.copy(temp_xdata)
                self.status_window.append("Data file loaded successfully!")
                self.plot_button.setEnabled(True)
                self.are_we_there_yet()
            else:
                blank_FID = copy.copy(temp_FID)
                blank_xdata = copy.copy(temp_xdata)
                self.status_window.append("Blank file loaded successfully!")
                self.plot_blank_button.setEnabled(True)
                self.are_we_there_yet()

    def plot_blank_input(self):
        switch = "blank"
        self.plotter(switch)

    def plot_input(self):
        switch = "data"
        self.plotter(switch)

    def plotter(self,switch):
        global gate_start
        global gate_stop

        if self.full_FID_cb.isChecked():
            self.gate_start_input.setText(str(xdata[0]))
            self.gate_stop_input.setText(str(xdata[-1]))
            self.gate_start_input.setEnabled(False)
            self.gate_stop_input.setEnabled(False)

        try:
            gate_start = float(self.gate_start_input.text())
        except:
            self.error_message = "Gate start should be a float!" # make it a window later
            self.raise_error()
            self.gate_start_input.setFocus()
            return 0

        try:
            gate_stop = float(self.gate_stop_input.text())
        except:
            self.error_message = "Gate stop should be a float!" # make it a window later
            self.raise_error()
            self.gate_stop_input.setFocus()
            return 0

        rcParams.update({'figure.autolayout': True}) # Magic from here: https://stackoverflow.com/questions/6774086/why-is-my-xlabel-cut-off-in-my-matplotlib-plot

        self.plot = Actual_Plot(which_one=switch)
        self.plot.show()


    def FT(self):
        # Does all the math and stuff here instead of sending to a worker thread. Hopefully that's not bad!
        # OK, looks like we should send the hard things to a worker thread. Sigh.

        global gate_start
        global gate_stop

        final_check = self.are_we_there_yet()

        if final_check == False:
            self.FT_data_button.setEnabled(False)
            return

        if self.full_FID_cb.isChecked():
            self.gate_start_input.setText(str(xdata[0]))
            self.gate_stop_input.setText(str(xdata[-1]))
            self.gate_start_input.setEnabled(False)
            self.gate_stop_input.setEnabled(False)

        use_blank = self.use_blank_cb.isChecked()

        try:
            sample_rate = float(self.sample_rate_input.text())*1e9
        except:
            self.error_message = "Sample rate should be a float!" # window later
            self.raise_error()
            self.sample_rate_input.setFocus()
            return 0

        try:
            gate_start = float(self.gate_start_input.text())
        except:
            self.error_message = "Gate start should be a float!" # window later
            self.raise_error()
            self.gate_start_input.setFocus()
            return 0

        try:
            gate_stop = float(self.gate_stop_input.text())
        except:
            self.error_message = "Gate stop should be a float!" # window later
            self.raise_error()
            self.gate_stop_input.setFocus()
            return 0

        try:
            output_file_name = self.file_export_input.text()
        except:
            self.error_message = "Output file name should be a valid string!"
            self.raise_error()
            return 0

        if gate_start >= gate_stop:
            self.error_message = "Gate start should be smaller than gate stop! Please correct this and try again."
            self.raise_error()
            self.gate_start_input.setFocus()
            return 0

        if gate_start < 0.0:
            self.gate_start_input.setText('0.0')
            gate_start = 0.0

        if gate_stop > xdata[-1]:
            self.gate_stop_input.setText(str(xdata[-1]))
            gate_stop = xdata[-1]


        band = self.band_select.currentText()

        if (band=="Low (8.7-13.5 GHz)"):
            PDRO = 13600
            lower_bound = 8000.0
            upper_bound = 13500.0
        if (band=="Medium (13.5-18.3 GHz)"):
            PDRO = 18400
            lower_bound = 13500.0
            upper_bound = 18000.0
        if (band=="High (18.0-26.5 GHz)"):
            PDRO = 27200
            lower_bound = 18000.0
            upper_bound = 26500.0

        N1 = int(np.floor(gate_start*sample_rate*(10**-6)))
        N2 = int(np.floor(gate_stop*sample_rate*(10**-6)))

        datafile = self.file_import_input.text()

        if use_blank:
            blankfile = self.blank_import_input.text()
        else:
            blankfile = ''

        export_file_name = self.file_export_input.text()

        thread = self.thread = QtCore.QThread()
        worker = self.worker = Worker(datafile, gate_start, gate_stop, sample_rate, use_blank, PDRO, lower_bound, upper_bound, N1, N2, blankfile, export_file_name) # give it whatever arguments it needs
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress_update)
        worker.error.connect(self.error_update)
        worker.indicator.connect(self.indicator_update)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(thread.quit)
        thread.start()

    def progress_update(self,value):
        self.status_window.append(value)

    def error_update(self,value):
        self.error_message = value
        self.raise_error()

    def indicator_update(self,value):

        if value == 0:
            self.indicator.setStyleSheet("background-color:rgb(255,255,255); color:rgb(0,0,0); border: none")
            self.indicator.setText("Ready")

        if value == 1:
            self.indicator.setStyleSheet("background-color:rgb(255,0,0); color:rgb(255,255,255); border: none")
            self.indicator.setText("Running")

        if value == 2:
            self.indicator.setStyleSheet("background-color:rgb(0,0,255); color:rgb(255,255,255); border: none")
            self.indicator.setText("Finished")
            self.indicator.setEnabled(True)
            self.exit_button.setFocus() # Set focus to the exit button since it's done now


class Worker(QtCore.QObject): # looks like we need to use threading in order to get progress bars to update!
# Thanks go to this thread: https://gis.stackexchange.com/questions/64831/how-do-i-prevent-qgis-from-being-detected-as-not-responding-when-running-a-hea
    def __init__(self, datafile, gate_start, gate_stop, sample_rate, use_blank, PDRO, lower_bound, upper_bound, N1, N2, blankfile, export_file_name, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.datafile = datafile
        self.gate_start = gate_start
        self.gate_stop = gate_stop
        self.sample_rate = sample_rate
        self.use_blank = use_blank
        self.PDRO = PDRO
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.N1 = N1
        self.N2 = N2
        self.blankfile = blankfile
        self.export_file_name = export_file_name

    def run(self):
        self.indicator.emit(0)
        np.set_printoptions(formatter={'float_kind':'{:f}'.format})

        self.progress.emit("Cutting FID!")

        data = np.fromfile(self.datafile,sep = " ")
        data_cut = data[self.N1:self.N2]

        if self.use_blank:
            self.progress.emit("Subtracting FID!")
            blank = np.fromfile(self.blankfile, sep = " ")
            blank_cut = blank[self.N1:self.N2]

        if self.use_blank: # Emit an error message to the outside if blank subtraction doesn't work.
            try:
                full_FID = np.subtract(data_cut, blank_cut)
            except:
                self.error.emit("Subtraction of blank from data didn't work! This probably happened because they don't have the same number of rows.")
                return 0
        else:
            full_FID = data_cut

        #CUT_blanks = blank1[N1:N2] # Maybe later add a thing that lets us choose to save an FT of the blank if we want to as well (though it's kind of a pain...)

        self.indicator.emit(1)
        self.progress.emit("Applying window function!")

        Npts = full_FID.size
        Kaiser = np.kaiser(Npts,9.5) # Applies a Kaiser-Bessel windowing function; beta value is currently hard-coded, though this could be changed in the future.
        FID_Kaiser = Correct_FID_Length_Window(full_FID,Kaiser)

        self.progress.emit("Taking FT of data!")

        Spectrum_Kaiser = Freq_Spectrum(FID_Kaiser,self.sample_rate,self.PDRO)

        #NoWindow = np.full(Npts,1) # Maybe later we might decide whether or not to have users choose whether or not to use a window
        #FID_None = Correct_FID_Length_Window(CUT,NoWindow)  
        #Spectrum_None = Freq_Spectrum(FID_None,sample_rate,PDRO)

        low_index = 0
        high_index = 0

        for i in range(len(Spectrum_Kaiser)): # lower_bound and upper_bound are set by the band variable; this prunes output to just relevant frequency ranges for each band
            if (low_index == 0) and (Spectrum_Kaiser[i][0] >= self.lower_bound):
                low_index = i
                continue
            if (high_index == 0) and (Spectrum_Kaiser[i][0] >= self.upper_bound):
                high_index = i
                break

        Spectrum_Kaiser = Spectrum_Kaiser[low_index:high_index]
        self.progress.emit("FT is complete! Now writing to file!")

        np.savetxt(self.export_file_name, Spectrum_Kaiser, delimiter=', ')

        self.progress.emit("Finished!")
        self.indicator.emit(2)
        self.finished.emit(True)

    progress = QtCore.pyqtSignal(str)
    error = QtCore.pyqtSignal(str)
    indicator = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(bool)

class QHLine(QtWidgets.QFrame): # Using this: https://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

class WidgetPlot(QtWidgets.QWidget): # Trying this one: https://stackoverflow.com/questions/48140576/matplotlib-toolbar-in-a-pyqt5-application
    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QtWidgets.QVBoxLayout())
        self.canvas = PlotCanvas(self, width=10, height=8)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=10, height=8, dpi=100):
        fig = Figure(figsize=(width,height), dpi=dpi)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        ax = self.figure.add_subplot(111)
        if plot_switch == "data":
            ax.plot(xdata,FID,'-')
        else:
            ax.plot(blank_xdata,blank_FID,'-')
        ax.axvline(x=gate_start,color='r',linestyle='--')
        ax.axvline(x=gate_stop,color='r',linestyle='--')

        if plot_switch == "data":
            ax.set_title('FID + Gates')
        else:
            ax.set_title('FID (Blank) + Gates')

        ax.set_xlabel('Time (microseconds)')
        ax.set_ylabel('FID Amplitude (arb. units)')
        self.draw()

class Actual_Plot(QtWidgets.QMainWindow):
    def __init__(self, **kwargs):
        QtWidgets.QMainWindow.__init__(self)
        self.__dict__.update(kwargs)

        global plot_switch
        plot_switch = self.which_one

        if self.which_one == "data":
            self.title = 'Plot of FID with Gate Boundaries'
        else:
            self.title = 'Plot of FID (Blank) with Gate Boundaries'

        self.left = 300
        self.top = 300
        self.width = 500
        self.height = 400

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)
        vlay = QtWidgets.QVBoxLayout(widget)
        hlay = QtWidgets.QHBoxLayout()
        vlay.addLayout(hlay)

        m = WidgetPlot(self)
        vlay.addWidget(m)

def Correct_FID_Length_Window(local_FID,Window): #this operation does zero filling and scaling of FID by window function; trying for good balance of resolution and intensity
    Npts = local_FID.size
    Nfid = np.ceil(np.log2(Npts))+4 # This is maybe a bit excessive...
    Nnew = np.power(2,Nfid)
    New_FID = np.multiply(local_FID, Window)
    Nbuffer = int(Nnew - Npts)
    Zerofill = np.zeros(Nbuffer)
    FID_buffer = np.concatenate((New_FID, Zerofill), axis=0)
    return FID_buffer

def Freq_Spectrum(local_FID,sample,PDRO): # Does the actual Fourier transform
    ftcalc = np.fft.fft(local_FID,norm="ortho")
    ftcalc = np.absolute(ftcalc)
    NumFreq = ftcalc.size
    Freq = np.zeros(NumFreq)
    for m in range(NumFreq-1): # Sets up the frequency axis
        Freq[m] = PDRO - ((m*sample)/local_FID.size)*(10**-6)
    Ft = np.column_stack((Freq,ftcalc))
    Ft = np.flip(Ft, 0) # This puts the frequency axis in increasing order
    return Ft


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog_First_Window()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())