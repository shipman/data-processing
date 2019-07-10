"""
This script takes in a time-domain FID recorded from our spectrometer and fits 
and extracts spurious frequency components from it. It then saves a time-
domain data set which has had the spurs removed.

The graphical interface was built in PyQt5 and implements some logical
control over the process by selectively greying out and then un-greying the
buttons that perform various actions if all of the data isn't there as
needed. There are also several try/except clauses to capture user input
error.

It also implements a progress bar that updates itself with threading. :)
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import math
import matplotlib
import sys
matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import rcParams

class Ui_Dialog_First_Window(object):
    def setupUi(self, Dialog):
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

        self.file_import_label = QtWidgets.QLabel(Dialog)
        self.file_import_label.setObjectName("file_import_label")
        self.gridLayout.addWidget(self.file_import_label, 1, 0, 1, 1)
        self.file_import_input = QtWidgets.QLineEdit(Dialog)
        self.file_import_input.setObjectName("file_import_input")
        self.file_import_input.setToolTip("Name of the data file to be loaded and processed.")
        self.gridLayout.addWidget(self.file_import_input, 1, 1, 1, 3)
        self.browse_import_button = QtWidgets.QPushButton(Dialog)
        self.browse_import_button.setObjectName("browse_import_button")
        self.browse_import_button.clicked.connect(self.browse)
        self.gridLayout.addWidget(self.browse_import_button, 1, 4, 1, 1)
        self.load_button = QtWidgets.QPushButton(Dialog)
        self.load_button.setObjectName("plot_button")
        self.load_button.clicked.connect(self.load_input)
        self.gridLayout.addWidget(self.load_button, 1, 5, 1, 1)
        self.load_button.setEnabled(False)
        self.plot_button = QtWidgets.QPushButton(Dialog)
        self.plot_button.setObjectName("plot_button")
        self.plot_button.clicked.connect(self.plot_input)
        self.gridLayout.addWidget(self.plot_button, 1, 6, 1, 1)
        self.plot_button.setEnabled(False)

        self.file_export_label = QtWidgets.QLabel(Dialog)
        self.file_export_label.setObjectName("file_export_label")
        self.gridLayout.addWidget(self.file_export_label, 2, 0, 1, 1)
        self.file_export_input = QtWidgets.QLineEdit(Dialog)
        self.file_export_input.setObjectName("file_export_input")
        self.file_export_input.setToolTip("Name of the file that data will be saved to.")
        self.gridLayout.addWidget(self.file_export_input, 2, 1, 1, 3)
        self.browse_export_button = QtWidgets.QPushButton(Dialog)
        self.browse_export_button.setObjectName("browse_export_button")
        self.browse_export_button.clicked.connect(self.browse_export)
        self.gridLayout.addWidget(self.browse_export_button, 2, 4, 1, 1)

        self.gate_start_label = QtWidgets.QLabel(Dialog)
        self.gate_start_label.setObjectName("gate_start_label")
        self.gridLayout.addWidget(self.gate_start_label, 3, 0, 1, 1)
        self.gate_start_input = QtWidgets.QLineEdit(Dialog)
        self.gate_start_input.setObjectName("gate_start_input")
        self.gate_start_input.setToolTip("This is the starting point of the data to process, in microseconds.\nIf this value is negative, it will be reset to 0.0 when spur extraction begins.")
        self.gate_start_input.setText("0.0") # Default value, will need to add checks to make sure this is in-bounds
        self.gridLayout.addWidget(self.gate_start_input, 3, 1, 1, 1)
        self.gate_stop_label = QtWidgets.QLabel(Dialog)
        self.gate_stop_label.setObjectName("gate_stop_label")
        self.gridLayout.addWidget(self.gate_stop_label, 3, 3, 1, 1)
        self.gate_stop_input = QtWidgets.QLineEdit(Dialog)
        self.gate_stop_input.setObjectName("gate_stop_input")
        self.gate_stop_input.setToolTip("This is the end point of the data to process, in microseconds.\nIf this value is greater than the FID duration, it will be set to the time corresponding to the last point in the file.")
        self.gate_stop_input.setText("8.0") # Default value, will need to add checks to make sure this is in-bounds
        self.gridLayout.addWidget(self.gate_stop_input, 3, 4, 1, 1)
        self.full_FID_label = QtWidgets.QLabel(Dialog)
        self.full_FID_label.setObjectName("full_FID_label")
        self.gridLayout.addWidget(self.full_FID_label, 3, 5, 1, 1)
        self.full_FID_cb = QtWidgets.QCheckBox(Dialog)
        self.full_FID_cb.setObjectName("full_FID_cb")
        self.full_FID_cb.setToolTip("If checked, use the full FID (ignore the gate start and stop boxes).")
        self.gridLayout.addWidget(self.full_FID_cb, 3, 6, 1, 1)

        self.spur_spacing_label = QtWidgets.QLabel(Dialog)
        self.spur_spacing_label.setObjectName("spur_spacing_label")
        self.gridLayout.addWidget(self.spur_spacing_label, 4, 0, 1, 1)
        self.spur_spacing_input = QtWidgets.QLineEdit(Dialog)
        self.spur_spacing_input.setObjectName("spur_spacing_input")
        self.spur_spacing_input.setToolTip("This is the spacing of spurs to extract, in MHz.")
        self.spur_spacing_input.setText("50.0") # Default value
        self.gridLayout.addWidget(self.spur_spacing_input, 4, 1, 1, 1)
        self.max_spur_label = QtWidgets.QLabel(Dialog)
        self.max_spur_label.setObjectName("max_spur_label")
        self.gridLayout.addWidget(self.max_spur_label, 4, 3, 1, 1)
        self.max_spur_input = QtWidgets.QLineEdit(Dialog)
        self.max_spur_input.setObjectName("max_spur_input")
        self.max_spur_input.setToolTip("This is the maximum spur frequency to remove, in GHz. It should be less than the Nyquist frequency.")
        self.max_spur_input.setText("10.0") # Default value
        self.gridLayout.addWidget(self.max_spur_input, 4, 4, 1, 1)

        self.extract_spurs_button = QtWidgets.QPushButton(Dialog)
        self.extract_spurs_button.setObjectName("extract_spurs_button")
        self.extract_spurs_button.clicked.connect(self.extract)
        self.gridLayout.addWidget(self.extract_spurs_button, 5, 0, 1, 4)
        self.extract_spurs_button.setEnabled(False)
        self.exit_button = QtWidgets.QPushButton(Dialog)
        self.exit_button.setObjectName("exit_button")
        self.exit_button.clicked.connect(app.quit) # Probably should interrupt if haven't saved yet
        self.gridLayout.addWidget(self.exit_button, 5, 4, 1, 2)

        self.progress = QtWidgets.QProgressBar(Dialog)
        self.progress.setObjectName("progress")
        self.gridLayout.addWidget(self.progress,6,0,1,8)
        self.progress.setValue(0)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Spur Extraction"))
        self.sample_rate_label.setText(_translate("Dialog", "Sample Rate (GS/s)"))
        self.file_import_label.setText(_translate("Dialog", "Data File Name"))
        self.browse_import_button.setText(_translate("Dialog", "Browse"))
        self.load_button.setText(_translate("Dialog", "Load Data"))
        self.plot_button.setText(_translate("Dialog", "Plot Data"))
        self.gate_start_label.setText(_translate("Dialog", "Gate Start (us)"))
        self.gate_stop_label.setText(_translate("Dialog", "Gate Stop (us)"))
        self.full_FID_label.setText(_translate("Dialog", "Use Full FID"))
        self.file_export_label.setText(_translate("Dialog", "Output File Name"))
        self.browse_export_button.setText(_translate("Dialog", "Browse"))
        self.spur_spacing_label.setText(_translate("Dialog", "Spur Spacing (MHz)"))
        self.max_spur_label.setText(_translate("Dialog", "Max Spur Frequency (GHz)"))
        self.extract_spurs_button.setText(_translate("Dialog", "Extract Spurs!"))
        self.exit_button.setText(_translate("Dialog", "Exit"))


    def browse(self):
    	fileName, _ = QtWidgets.QFileDialog.getOpenFileName()
    	if fileName:
    		self.file_import_input.setText(fileName)
    		self.load_button.setEnabled(True)

    def browse_export(self):
    	fileName, _ = QtWidgets.QFileDialog.getSaveFileName()
    	if fileName:
    		self.file_export_input.setText(fileName)
    		if self.plot_button.isEnabled():
    			self.extract_spurs_button.setEnabled(True)

    def raise_error(self):
    	self.error_dialog = QtWidgets.QMessageBox()
    	self.error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
    	self.error_dialog.setWindowTitle("Something's Wrong!")
    	self.error_dialog.setText(self.error_message)
    	self.error_dialog.show()

    def load_input(self):
    	try:
    		sample_rate = float(self.sample_rate_input.text())*1e9
    	except:
    		self.error_message = "Sample rate should be a float!"
    		self.raise_error()
    		return 0

    	global FID
    	global xdata

    	FID = []
    	xdata = []
    	row_counter = 0

    	try:
    		data_input_file = open(self.file_import_input.text())
    	except:
    		self.error_message = "That file couldn't be opened. Try again with a different one." # We'll make this be a pop-up error window later
    		self.raise_error()
    		return 0

    	try:
    		for row in data_input_file:
    			temp=row.split()
    			FID.append(float(temp[np.size(temp)-1]))
    			xdata.append((row_counter/sample_rate)*1e6) # to put it in microseconds
    			row_counter += 1
    		if self.full_FID_cb.checkState():
    			self.gate_start_input.setText(str(xdata[0]))
    			self.gate_stop_input.setText(str(xdata[-1]))
    	except:
    		self.error_message = "Data from that file couldn't be properly processed; try again with a different file." # We'll make this be a pop-up error window later
    		self.raise_error()
    		return 0

    	else:
    		self.plot_button.setEnabled(True)
    		if self.file_export_input.text() != '':
    			self.extract_spurs_button.setEnabled(True)

    def plot_input(self):
    	global gate_start
    	global gate_stop

    	if self.full_FID_cb.checkState():
    		self.gate_start_input.setText(str(xdata[0]))
    		self.gate_stop_input.setText(str(xdata[-1]))

    	try:
    		gate_start = float(self.gate_start_input.text())
    	except:
    		self.error_message = "Gate start should be a float!" # make it a window later
    		self.raise_error()
    		return 0

    	try:
    		gate_stop = float(self.gate_stop_input.text())
    	except:
    		self.error_message = "Gate stop should be a float!" # make it a window later
    		self.raise_error()
    		return 0

    	rcParams.update({'figure.autolayout': True}) # Magic from here: https://stackoverflow.com/questions/6774086/why-is-my-xlabel-cut-off-in-my-matplotlib-plot

    	self.plot = Data_Plot()
    	self.plot.show()

    def extract(self):
    	# The old version actually did math and stuff. The new one allocates all of that to a worker thread.

    	if self.full_FID_cb.checkState():
    		self.gate_start_input.setText(str(xdata[0]))
    		self.gate_stop_input.setText(str(xdata[-1]))

    	try:
    		sample_rate = float(self.sample_rate_input.text())*1e9
    	except:
    		self.error_message = "Sample rate should be a float!" # window later
    		self.raise_error()
    		return 0

    	try:
    		gate_start = float(self.gate_start_input.text())
    	except:
    		self.error_message = "Gate start should be a float!" # window later
    		self.raise_error()
    		return 0

    	try:
    		gate_stop = float(self.gate_stop_input.text())
    	except:
    		self.error_message = "Gate stop should be a float!" # window later
    		self.raise_error()
    		return 0

    	try:
    		spur_spacing = float(self.spur_spacing_input.text())*1e6
    	except:
    		self.error_message = "Spur spacing should be a float!" # window later
    		self.raise_error()
    		return 0

    	try:
    		spur_max_limit = float(self.max_spur_input.text())*1e9
    	except:
    		self.error_message = "Max spur frequency should be a float!" # window later
    		self.raise_error()
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
    		return 0

    	if gate_start < 0.0:
    		self.gate_start_input.setText('0.0')
    		gate_start = 0.0

    	if gate_stop > xdata[-1]:
    		self.gate_stop_input.setText(str(xdata[-1]))
    		gate_stop = xdata[-1]

    	thread = self.thread = QtCore.QThread()
    	worker = self.worker = Worker(gate_start, gate_stop, sample_rate, spur_spacing, spur_max_limit,output_file_name) # give it whatever arguments it needs
    	worker.moveToThread(thread)
    	thread.started.connect(worker.run)
    	worker.progress.connect(self.progress_update)
    	worker.finished.connect(worker.deleteLater)
    	thread.finished.connect(thread.deleteLater)
    	worker.finished.connect(thread.quit)
    	thread.start()

    def progress_update(self, value):
    	self.progress.setValue(value)


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
		ax.plot(xdata,FID,'-')
		ax.axvline(x=gate_start,color='r',linestyle='--')
		ax.axvline(x=gate_stop,color='r',linestyle='--')
		ax.set_title('FID + Gates')
		ax.set_xlabel('Time (microseconds)')
		ax.set_ylabel('FID Amplitude (arb. units)')
		self.draw()

class Data_Plot(QtWidgets.QMainWindow):
	def __init__(self):
		QtWidgets.QMainWindow.__init__(self)

		self.title = 'Plot of FID with Gate Boundaries'
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

class Worker(QtCore.QObject): # looks like we need to use threading in order to get progress bars to update!
# Thanks go to this thread: https://gis.stackexchange.com/questions/64831/how-do-i-prevent-qgis-from-being-detected-as-not-responding-when-running-a-hea
	def __init__(self, gate_start, gate_stop, sample_rate, spur_spacing, spur_max_limit, output_file_name, *args, **kwargs):
		QtCore.QObject.__init__(self, *args, **kwargs)
		self.percentage = 0
		self.gate_start = gate_start
		self.gate_stop = gate_stop
		self.sample_rate = sample_rate
		self.spur_spacing = spur_spacing
		self.spur_max_limit = spur_max_limit
		self.output_file_name = output_file_name

	def run(self):
		FID_Cut = Cut_FID(FID, self.gate_start, self.gate_stop, self.sample_rate)

		spurs_list = []
		spur_max_multiple = int(math.floor(self.spur_max_limit/self.spur_spacing))

		for i in range(spur_max_multiple):
			spurs_list.append(self.spur_spacing*(i+1))

		data = FID_Cut

		#outfid = remove_all_spurs(self,spurs_list,FID_Cut,FID_Cut,self.sample_rate)
		for i in range(len(spurs_list)):
			print "Removing spur at %s MHz"%str(spurs_list[i]/1e6)
			(temp_sin,temp_cos) = components(spurs_list[i],FID_Cut,self.sample_rate)
			data = component_removal(spurs_list[i],data,temp_sin,temp_cos,self.sample_rate)
			percentage = int(math.floor(float(i+1)/float(len(spurs_list))*100.0))
			self.calculate_progress(percentage)


		#output_file_name = self.file_export_input.text()
		output_file = open(self.output_file_name, 'w')

		for i in range(len(data)):
			output_file.write(str(data[i]))
			output_file.write('\n')

		print "Complete!"

		self.finished.emit(True)

	def calculate_progress(self,percentage_new):

		if percentage_new > self.percentage:
			self.percentage = percentage_new
			self.progress.emit(self.percentage)

	progress = QtCore.pyqtSignal(int)
	finished = QtCore.pyqtSignal(bool)


# Makes a new list, Cut, that is only the part of the FID within the defined gate
def Cut_FID(FID, Gate_start, Gate_stop, Sample_Rate):
    N1 = int(math.floor(Gate_start*1e-6*Sample_Rate))
    N2 = int(math.floor(Gate_stop*1e-6*Sample_Rate))
    Cut = FID[N1:N2]
    return Cut

def components(freq,data,samples_per_second):
    temp_sin = 0.0
    temp_cos = 0.0
    for i in range(0,len(data)):
        temp_s = np.sin((freq*i*2*math.pi) / samples_per_second)
        temp_c = np.cos((freq*i*2*math.pi) / samples_per_second)
        temp_sin = temp_s*data[i] + temp_sin
        temp_cos = temp_c*data[i] + temp_cos
    return temp_sin,temp_cos

def component_removal(freq,data,sin_comp,cos_comp,samples_per_second):
    outfid = []
    for i in range(len(data)):
        comp = (((sin_comp*np.sin((freq*i*2*math.pi)/samples_per_second))+(cos_comp*np.cos((freq*i*2*math.pi)/samples_per_second)))*2)/len(data)
        outfid.append(data[i]-comp)
    return outfid


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog_First_Window()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())