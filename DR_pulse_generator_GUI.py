"""
DR_pulse_generator - this script will generate chirp and DR pulses and will eventually have a GUI.

First step is to build in generalizations and tidy code (started from code Erika Riffe wrote based on 
a MathCAD script I put together, which was itself inherited from my work in Brooks Pate's lab). Once
that's done, I'll build up the framework for the window.

For now I think I'll hold it to just doing one DR pulse, which will be a simplification over Erika's code.
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial
import numpy
import matplotlib
import sys
matplotlib.use("Qt5Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
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
        #self.sample_rate_label = QtWidgets.QLabel(Dialog) # Going to assume it's a 10 GS/s arb; user can change script if working with more advanced AWG.
        #self.sample_rate_label.setObjectName("sample_rate_label")
        #self.gridLayout.addWidget(self.sample_rate_label, 0, 0, 1, 1)
        #self.sample_rate_input = QtWidgets.QLineEdit(Dialog)
        #self.sample_rate_input.setObjectName("sample_rate_input")
        #self.sample_rate_input.setToolTip("This is the sampling rate of the arb in GS/s.")
        #self.sample_rate_input.setText("10") # Default value
        #self.gridLayout.addWidget(self.sample_rate_input, 0, 1, 1, 1)
        #self.band_select_label = QtWidgets.QLabel(Dialog) # Label mostly contributes to visual clutter here, I think - combobox entries should be informative enough.
        #self.band_select_label.setObjectName("band_select_label")
        #self.gridLayout.addWidget(self.band_select_label, 0, 2, 1, 1)
        self.band_select = QtWidgets.QComboBox(Dialog)
        self.band_select.setObjectName("band_select") # Do we have to add a function to deal with it if someone changes the value? No, we only read from this right before using the data, so it should just work.
        self.band_select.setToolTip("This is the band for which the pulse is being generated.")
        self.band_select.addItems(["Low (8.7-13.5 GHz)", "Medium (13.5-18.3 GHz)", "High (18.0-26.5 GHz)"])
        self.band_select.setCurrentIndex(2) # high band as default
        self.band_select.activated.connect(self.band_change)
        self.gridLayout.addWidget(self.band_select, 0, 0, 1, 2)
        self.use_defaults_cb = QtWidgets.QCheckBox(Dialog)
        self.use_defaults_cb.setObjectName("use_defaults_cb")
        self.use_defaults_cb.setToolTip("If checked, use the default chirp and trigger settings for your band.")
        self.use_defaults_cb.setText("Use defaults")
        self.use_defaults_cb.stateChanged.connect(self.use_defaults)
        self.gridLayout.addWidget(self.use_defaults_cb, 0, 2, 1, 1)
        self.use_DR_cb = QtWidgets.QCheckBox(Dialog)
        self.use_DR_cb.setObjectName("use_DR_cb")
        self.use_DR_cb.setToolTip("If checked, generate a DR pulse in addition to the chirp.")
        self.use_DR_cb.setText("Add DR pulse")
        self.use_DR_cb.setChecked(True) # Have it checked by default
        self.use_DR_cb.stateChanged.connect(self.use_DR)
        self.gridLayout.addWidget(self.use_DR_cb, 0, 3, 1, 1)
        self.font_plus_button = QtWidgets.QPushButton(Dialog)
        self.font_plus_button.setObjectName = "font_plus_button"
        self.font_plus_button.clicked.connect(partial(self.font_plus,Dialog))
        self.gridLayout.addWidget(self.font_plus_button, 0, 4, 1, 1)
        self.font_minus_button = QtWidgets.QPushButton(Dialog)
        self.font_minus_button.setObjectName = "font_minus_button"
        self.font_minus_button.clicked.connect(partial(self.font_minus,Dialog))
        self.gridLayout.addWidget(self.font_minus_button, 0, 5, 1, 1)

        self.gridLayout.addWidget(QHLine(), 1, 0, 1, 6)

        self.chirp_start_label = QtWidgets.QLabel(Dialog)
        self.chirp_start_label.setObjectName("chirp_start_label")
        self.gridLayout.addWidget(self.chirp_start_label, 2, 0, 1, 1)
        self.chirp_stop_label = QtWidgets.QLabel(Dialog)
        self.chirp_stop_label.setObjectName("chirp_stop_label")
        self.gridLayout.addWidget(self.chirp_stop_label, 2, 1, 1, 1)
        self.chirp_delay_label = QtWidgets.QLabel(Dialog) # chirp_start is already used for frequency, but also need to specify time
        self.chirp_delay_label.setObjectName("chirp_delay_label")
        self.gridLayout.addWidget(self.chirp_delay_label, 2, 2, 1, 1)
        self.chirp_duration_label = QtWidgets.QLabel(Dialog)
        self.chirp_duration_label.setObjectName("chirp_duration_label")
        self.gridLayout.addWidget(self.chirp_duration_label, 2, 3, 1, 1)

        self.chirp_start_input = QtWidgets.QLineEdit(Dialog)
        self.chirp_start_input.setObjectName("chirp_start_input")
        self.chirp_start_input.setToolTip("This is the start frequency of the chirp (before mixing with PDRO) in MHz.")
        self.chirp_start_input.setText("350") # default for highband; we should later implement a checkbox and detect when the band is changed
        self.gridLayout.addWidget(self.chirp_start_input, 3, 0, 1, 1)
        self.chirp_stop_input = QtWidgets.QLineEdit(Dialog)
        self.chirp_stop_input.setObjectName("chirp_stop_input")
        self.chirp_stop_input.setToolTip("This is the stop frequency of the chirp (before mixing with PDRO) in MHz.")
        self.chirp_stop_input.setText("4600") # default for highband; make better later
        self.gridLayout.addWidget(self.chirp_stop_input, 3, 1, 1, 1)
        self.chirp_delay_input = QtWidgets.QLineEdit(Dialog)
        self.chirp_delay_input.setObjectName("chirp_delay_input")
        self.chirp_delay_input.setToolTip("This is the starting time of the chirp in microseconds.")
        self.chirp_delay_input.setText("0.6") # default value
        self.gridLayout.addWidget(self.chirp_delay_input, 3, 2, 1, 1)
        self.chirp_duration_input = QtWidgets.QLineEdit(Dialog)
        self.chirp_duration_input.setObjectName("chirp_duration_input")
        self.chirp_duration_input.setToolTip("This is the duration of the chirp in microseconds.")
        self.chirp_duration_input.setText("0.25") # default value
        self.gridLayout.addWidget(self.chirp_duration_input, 3, 3, 1, 1)

        self.gridLayout.addWidget(QHLine(), 4, 0, 1, 6)

        self.sinc_cent_freq_label = QtWidgets.QLabel(Dialog)
        self.sinc_cent_freq_label.setObjectName("sinc_cent_freq_label")
        self.gridLayout.addWidget(self.sinc_cent_freq_label, 5, 0, 1, 1)
        self.sinc_bandwidth_label = QtWidgets.QLabel(Dialog)
        self.sinc_bandwidth_label.setObjectName("sinc_bandwidth_label")
        self.gridLayout.addWidget(self.sinc_bandwidth_label, 5, 1, 1, 1)
        self.sinc_cent_time_label = QtWidgets.QLabel(Dialog)
        self.sinc_cent_time_label.setObjectName("sinc_cent_time_label")
        self.gridLayout.addWidget(self.sinc_cent_time_label, 5, 2, 1, 1)
        self.sinc_duration_label = QtWidgets.QLabel(Dialog)
        self.sinc_duration_label.setObjectName("sinc_duration_label")
        self.gridLayout.addWidget(self.sinc_duration_label, 5, 3, 1, 1)
        self.sinc_amplitude_label = QtWidgets.QLabel(Dialog)
        self.sinc_amplitude_label.setObjectName("sinc_amplitude_label")
        self.gridLayout.addWidget(self.sinc_amplitude_label, 5, 4, 1, 1)

        self.sinc_cent_freq_input = QtWidgets.QLineEdit(Dialog)
        self.sinc_cent_freq_input.setObjectName("sinc_cent_freq_input")
        self.sinc_cent_freq_input.setToolTip("This is the center frequency of the sinc pulse (that the molecules will see) in MHz.")
        self.sinc_cent_freq_input.setText("25124.872") # Default, should change when band is changed
        self.gridLayout.addWidget(self.sinc_cent_freq_input, 6, 0, 1, 1)
        self.sinc_bandwidth_input = QtWidgets.QLineEdit(Dialog)
        self.sinc_bandwidth_input.setObjectName("sinc_bandwidth_input")
        self.sinc_bandwidth_input.setToolTip("This is the theoretical bandwidth (FWHM) of the sinc pulse in MHz. The real bandwidth may be larger if the sinc duration is too short.")
        self.sinc_bandwidth_input.setText("5") # Default value
        self.gridLayout.addWidget(self.sinc_bandwidth_input, 6, 1, 1, 1)
        self.sinc_cent_time_input = QtWidgets.QLineEdit(Dialog) # Need to adjust these names since it's now the start time
        self.sinc_cent_time_input.setObjectName("sinc_cent_time_input")
        self.sinc_cent_time_input.setToolTip("This is the time corresponding to the start time of the sinc pulse in microseconds.") # Really should make this a start and duration later.
        self.sinc_cent_time_input.setText("0.9") # Default value
        self.gridLayout.addWidget(self.sinc_cent_time_input, 6, 2, 1, 1)
        self.sinc_duration_input = QtWidgets.QLineEdit(Dialog)
        self.sinc_duration_input.setObjectName("sinc_duration_input")
        self.sinc_duration_input.setToolTip("This is the total duration of the sinc pulse in microseconds; it sets a lower limit on the real bandwidth.")
        self.sinc_duration_input.setText("0.5") # Default value
        self.gridLayout.addWidget(self.sinc_duration_input, 6, 3, 1, 1)
        self.sinc_amplitude_input = QtWidgets.QLineEdit(Dialog)
        self.sinc_amplitude_input.setObjectName("self_sinc_amplitude_input")
        self.sinc_amplitude_input.setToolTip("This is the amplitude of the sinc pulse, ranging from 0 to 1.")
        self.sinc_amplitude_input.setText("1") # Default value
        self.gridLayout.addWidget(self.sinc_amplitude_input, 6, 4, 1, 1)

        self.gridLayout.addWidget(QHLine(), 7, 0, 1, 6)

        self.marker_on_label = QtWidgets.QLabel(Dialog)
        self.marker_on_label.setObjectName("marker_on_label")
        self.gridLayout.addWidget(self.marker_on_label, 8, 0, 1, 1)
        self.marker_on_input = QtWidgets.QLineEdit(Dialog)
        self.marker_on_input.setObjectName("marker_on_input")
        self.marker_on_input.setToolTip("This is the time in microseconds when the trigger pulse from the arb turns on.")
        self.marker_on_input.setText("0.4") # Default value
        self.gridLayout.addWidget(self.marker_on_input, 8, 1, 1, 1)
        self.marker_off_label = QtWidgets.QLabel(Dialog)
        self.marker_off_label.setObjectName("marker_off_label")
        self.gridLayout.addWidget(self.marker_off_label, 8, 2, 1, 1)
        self.marker_off_input = QtWidgets.QLineEdit(Dialog)
        self.marker_off_input.setObjectName("marker_off_input")
        self.marker_off_input.setToolTip("This is the time in microseconds when the trigger pulse from the arb turns off.")
        self.marker_off_input.setText("1.7") # Default value
        self.gridLayout.addWidget(self.marker_off_input, 8, 3, 1, 1)
        self.waveform_time_label = QtWidgets.QLabel(Dialog)
        self.waveform_time_label.setObjectName("waveform_time_label")
        self.gridLayout.addWidget(self.waveform_time_label, 8, 4, 1, 1)
        self.waveform_time_input = QtWidgets.QLineEdit(Dialog)
        self.waveform_time_input.setObjectName("waveform_time_input")
        self.waveform_time_input.setToolTip("This is the total time in microseconds of the waveform, including FID collection time.")
        self.waveform_time_input.setText("11") # Default value
        self.gridLayout.addWidget(self.waveform_time_input, 8, 5, 1, 1)

        self.file_export_label = QtWidgets.QLabel(Dialog)
        self.file_export_label.setObjectName("file_export_label")
        self.gridLayout.addWidget(self.file_export_label, 9, 0, 1, 1)
        self.file_export_input = QtWidgets.QLineEdit(Dialog)
        self.file_export_input.setObjectName("file_export_input")
        self.file_export_input.setToolTip("Name of the file that the pulse will be saved to.")
        self.gridLayout.addWidget(self.file_export_input, 9, 1, 1, 3)
        self.browse_export_button = QtWidgets.QPushButton(Dialog)
        self.browse_export_button.setObjectName("browse_export_button")
        self.browse_export_button.clicked.connect(self.browse_export)
        self.gridLayout.addWidget(self.browse_export_button, 9, 4, 1, 1)

        self.gridLayout.addWidget(QHLine(), 10, 0, 1, 6)

        self.generate_pulse_button = QtWidgets.QPushButton(Dialog)
        self.generate_pulse_button.setObjectName("generate_pulse_button")
        self.generate_pulse_button.clicked.connect(self.generate_pulse)
        self.gridLayout.addWidget(self.generate_pulse_button, 11, 0, 1, 4)
        self.generate_pulse_button.setEnabled(False)
        self.exit_button = QtWidgets.QPushButton(Dialog)
        self.exit_button.setObjectName("exit_button")
        self.exit_button.clicked.connect(app.quit)
        self.gridLayout.addWidget(self.exit_button, 11, 4, 1, 2)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Chirped + DR Pulse Generation"))
        #self.sample_rate_label.setText(_translate("Dialog", "Sample Rate (GS/s)"))
        self.font_plus_button.setText(_translate("Dialog", "Increase Font"))
        self.font_minus_button.setText(_translate("Dialog", "Decrease Font"))
        self.chirp_start_label.setText(_translate("Dialog", "Chirp Start (MHz)"))
        self.chirp_stop_label.setText(_translate("Dialog", "Chirp Stop (MHz)"))
        self.chirp_delay_label.setText(_translate("Dialog", "Chirp Start Time (us)"))
        self.chirp_duration_label.setText(_translate("Dialog", "Chirp Duration (us)"))
        self.sinc_cent_freq_label.setText(_translate("Dialog", "DR Freq (MHz)"))
        self.sinc_bandwidth_label.setText(_translate("Dialog", "DR Width (MHz)"))
        self.sinc_cent_time_label.setText(_translate("Dialog", "DR Start Time (us)"))
        self.sinc_duration_label.setText(_translate("Dialog", "DR Duration (us)"))
        self.sinc_amplitude_label.setText(_translate("Dialog", "DR Amplitude (0-1)"))
        self.marker_on_label.setText(_translate("Dialog", "Trigger start (us)"))
        self.marker_off_label.setText(_translate("Dialog", "Trigger stop (us)"))
        self.waveform_time_label.setText(_translate("Dialog", "Total Time (us)"))
        self.file_export_label.setText(_translate("Dialog", "Output File Name"))
        self.browse_export_button.setText(_translate("Dialog", "Browse"))
        self.generate_pulse_button.setText(_translate("Dialog", "Generate Pulse!"))
        self.exit_button.setText(_translate("Dialog", "Exit"))

    def font_plus(self,Dialog):
        font = Dialog.font()
        curr_size = font.pointSize()
        new_size = curr_size + 3
        font.setPointSize(new_size)
        Dialog.setFont(font)

    def font_minus(self,Dialog):
        font = Dialog.font()
        curr_size = font.pointSize()
        new_size = curr_size - 3
        font.setPointSize(new_size)
        Dialog.setFont(font)

    def use_defaults(self):
        defaults_decision = self.use_defaults_cb.isChecked()

        if defaults_decision == False:
            self.chirp_start_input.setEnabled(True)
            self.chirp_stop_input.setEnabled(True)
            self.chirp_delay_input.setEnabled(True)
            self.chirp_duration_input.setEnabled(True)
            self.marker_on_input.setEnabled(True)
            self.marker_off_input.setEnabled(True)
            self.waveform_time_input.setEnabled(True)

        if defaults_decision == True:
            self.chirp_delay_input.setText("0.6")
            self.chirp_duration_input.setText("0.25")
            self.marker_on_input.setText("0.4")
            self.marker_off_input.setText("1.7")
            self.waveform_time_input.setText("11")
            self.chirp_delay_input.setEnabled(False)
            self.chirp_duration_input.setEnabled(False)
            self.marker_on_input.setEnabled(False)
            self.marker_off_input.setEnabled(False)
            self.waveform_time_input.setEnabled(False)

            band = self.band_select.currentText()
            if (band=="High (18.0-26.5 GHz)"):
                self.chirp_start_input.setText("350")
                self.chirp_stop_input.setText("4600")
            else:
                self.chirp_start_input.setText("100")
                self.chirp_stop_input.setText("4900")

            self.chirp_start_input.setEnabled(False)
            self.chirp_stop_input.setEnabled(False)

    def use_DR(self):
        DR_decision = self.use_DR_cb.isChecked()

        if DR_decision == False:
            self.sinc_cent_freq_input.setText("")
            self.sinc_bandwidth_input.setText("")
            self.sinc_cent_time_input.setText("")
            self.sinc_duration_input.setText("")
            self.sinc_amplitude_input.setText("")
            self.sinc_cent_freq_input.setEnabled(False)
            self.sinc_bandwidth_input.setEnabled(False)
            self.sinc_cent_time_input.setEnabled(False)
            self.sinc_duration_input.setEnabled(False)
            self.sinc_amplitude_input.setEnabled(False)

        if DR_decision == True:
            self.sinc_cent_freq_input.setEnabled(True)
            self.sinc_bandwidth_input.setEnabled(True)
            self.sinc_cent_time_input.setEnabled(True)
            self.sinc_duration_input.setEnabled(True)
            self.sinc_amplitude_input.setEnabled(True)

            if self.sinc_bandwidth_input.text() == "":
                self.sinc_bandwidth_input.setText("5")
            if self.sinc_cent_time_input.text() == "":
                self.sinc_cent_time_input.setText("0.9")
            if self.sinc_duration_input.text() == "":
                self.sinc_duration_input.setText("0.5")
            if self.sinc_amplitude_input.text() == "":
                self.sinc_amplitude_input.setText("1")
            band = self.band_select.currentText()
            temp_sinc_text = self.sinc_cent_freq_input.text()

            if temp_sinc_text != "":
                try:
                    temp_sinc_float = float(temp_sinc_text)
                except:
                    self.error_message = "DR center frequency should be a float!"
                    self.raise_error()
                    self.sinc_cent_freq_input.setFocus()
                    return 0

            if (band == "High (18.0-26.5 GHz)"):
                if (temp_sinc_text == ""):
                    self.sinc_cent_freq_input.setText("25124.872") # Favorite methanol transitions <3
                elif (temp_sinc_float < 18000.0) or (temp_sinc_float > 26500.0):
                    self.sinc_cent_freq_input.setText("25124.872")

            elif (band == "Medium (13.5-18.3 GHz)"):
                if (temp_sinc_text == ""):
                    self.sinc_cent_freq_input.setText("16395.740")
                elif (temp_sinc_float < 13500.0) or (temp_sinc_float > 18300.0):
                    self.sinc_cent_freq_input.setText("16395.740")

            elif (band == "Low (8.7-13.5 GHz)"):
                if (temp_sinc_text == ""):
                    self.sinc_cent_freq_input.setText("12178.593")
                elif (temp_sinc_float < 8700.0) or (temp_sinc_float > 13500.0):
                    self.sinc_cent_freq_input.setText("12178.593")


    def band_change(self):
        self.use_defaults()
        self.use_DR()


    def browse_export(self):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName()
        if fileName:
            self.file_export_input.setText(fileName)
            self.generate_pulse_button.setEnabled(True)
            self.generate_pulse_button.setFocus()

    def raise_error(self):
        self.error_dialog = QtWidgets.QMessageBox()
        self.error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        self.error_dialog.setWindowTitle("Something's Wrong!")
        self.error_dialog.setText(self.error_message)
        self.error_dialog.show()

    def generate_pulse(self): # It will eventually do the thing, by which I mean it will probably eventually pass the thing off to a worker thread.

        #try:
        #    sample_rate = float(self.sample_rate_input.text())
        #except:
        #    self.error_message = "Sample rate should be a float!"
        #    self.raise_error()
        #    return 0

        sample_rate = 10.0
        DR_decision = self.use_DR_cb.isChecked()

        try:
            Chirp_Duration = float(self.chirp_duration_input.text())
        except:
            self.error_message = "Chirp duration should be a float!"
            self.raise_error()
            self.chirp_duration_input.setFocus()
            return 0

        try:
            Overall_Chirp_Start = float(self.chirp_start_input.text())
        except:
            self.error_message = "Chirp starting frequency should be a float!"
            self.raise_error()
            self.chirp_start_input.setFocus()
            return 0

        try:
            Overall_Chirp_Stop = float(self.chirp_stop_input.text())
        except:
            self.error_message = "Chirp stop frequency should be a float!"
            self.raise_error()
            self.chirp_stop_input.setFocus()
            return 0

        try:
            Chirp_Delay = float(self.chirp_delay_input.text())
        except:
            self.error_message = "Chirp starting time should be a float!"
            self.raise_error()
            self.chirp_delay_input.setFocus()
            return 0

        try:
            Ch1_on = float(self.marker_on_input.text())
        except:
            self.error_message = "Trigger start should be a float!"
            self.raise_error()
            self.marker_on_input.setFocus()
            return 0

        try:
            Ch1_off = float(self.marker_off_input.text())
        except:
            self.error_message = "Trigger stop should be a float!"
            self.raise_error()
            self.marker_off_input.setFocus()
            return 0

        try:
            total_waveform_time = float(self.waveform_time_input.text())
        except:
            self.error_message = "Total waveform time should be a float!"
            self.raise_error()
            self.waveform_time_input.setFocus()
            return 0

        if (Ch1_on > total_waveform_time) or (Ch1_off > total_waveform_time):
            self.error_message = "Trigger start and stop times should be less than the total waveform time!"
            self.raise_error()
            self.marker_on_input.setFocus()
            return 0

        if self.file_export_input.text() == '':
            self.error_message = "There's not a valid file to save the pulse to!"
            self.raise_error()
            self.browse_export_button.setFocus()
            self.generate_pulse_button.setEnabled(False)
            return 0

        chirp_name = self.file_export_input.text()
        band = self.band_select.currentText()
        Width = Overall_Chirp_Stop - Overall_Chirp_Start

        if DR_decision:
            try:
                Sinc_Cent_Freq = float(self.sinc_cent_freq_input.text())
            except:
                self.error_message = "DR frequency should be a float!"
                self.raise_error()
                self.sinc_cent_freq_input.setFocus()
                return 0

            try:
                Sinc_Bandwidth = float(self.sinc_bandwidth_input.text())
            except:
                self.error_message = "DR width should be a float!"
                self.raise_error()
                self.sinc_bandwidth_input.setFocus()
                return 0

            try:
                sinc_start = float(self.sinc_cent_time_input.text())
            except:
                self.error_message = "DR start time should be a float!"
                self.raise_error()
                self.sinc_cent_time_input.setFocus()
                return 0

            try:
                Sinc_Window = float(self.sinc_duration_input.text())
            except:
                self.error_message = "DR duration should be a float!"
                self.raise_error()
                self.sinc_duration_input.setFocus()
                return 0

            try:
                Sinc_Amp = float(self.sinc_amplitude_input.text())
            except:
                self.error_message = "DR amplitude should be a float!"
                self.raise_error()
                self.sinc_amplitude_input.setFocus()
                return 0

            if (Sinc_Amp < 0) or (Sinc_Amp > 1):
                self.error_message = "DR amplitude should be between 0 and 1!"
                self.raise_error()
                self.sinc_amplitude_input.setFocus()
                return 0

            gap = sinc_start + (Sinc_Window/2)

            if (band == "Low (8.7-13.5 GHz)"):
                if (Sinc_Cent_Freq < 8700.0) or (Sinc_Cent_Freq > 13500.0):
                    self.error_message = "DR frequency is not in lower band range (8700 - 13500 MHz)!"
                    self.raise_error()
                    self.sinc_cent_freq_input.setFocus()
                    return 0
                PDRO = 13600
                Sinc_Freq = PDRO - Sinc_Cent_Freq
            elif (band == "Medium (13.5-18.3 GHz)"):
                if (Sinc_Cent_Freq < 13500.0) or (Sinc_Cent_Freq > 18300.0):
                    self.error_message = "DR frequency is not in mid band range (13500 - 18300 MHz)!"
                    self.raise_error()
                    self.sinc_cent_freq_input.setFocus()
                    return 0
                PDRO = 18400
                Sinc_Freq = PDRO - Sinc_Cent_Freq
            elif (band == "High (18.0-26.5 GHz)"):
                if (Sinc_Cent_Freq < 18000.0) or (Sinc_Cent_Freq > 26500.0):
                    self.error_message = "DR frequency is not in high band range (18000 - 26500 MHz)!"
                    self.raise_error()
                    self.sinc_cent_freq_input.setFocus()
                    return 0
                PDRO = 13600
                Sinc_Freq = PDRO - (Sinc_Cent_Freq/2)

        waveform_points = int(numpy.ceil((total_waveform_time*10**-6)*(sample_rate*(10**9))))

        global marker
        global pulse
        global sinc
        global sinc_exists
        global pulse_no_sinc

        if DR_decision == False:
            sinc_exists = False
        else:
            sinc_exists = True

        marker = marker1(Ch1_on,sample_rate,Ch1_off,waveform_points)
        pulse_no_sinc = chirp_waveform(Chirp_Delay,sample_rate,Overall_Chirp_Start,Width,Chirp_Duration,waveform_points)

        if (sinc_exists == False): # just a chirp, no DR pulse
            pulse = pulse_no_sinc
        else:
            sinc = sinc_waveform(gap,Sinc_Freq,Sinc_Amp,Sinc_Window,sample_rate,Sinc_Bandwidth,waveform_points)
            pulse = numpy.add(pulse_no_sinc,sinc)

        awg_data=numpy.column_stack((pulse,marker,marker))

        self.plotter()

        numpy.savetxt(chirp_name,awg_data,fmt="%.15f\t%i\t%i")#"%.15f\t%i\t%i"
        #print "Completed!"
        self.exit_button.setFocus()


    def plotter(self):
        rcParams.update({'figure.autolayout': True}) # Magic from here: https://stackoverflow.com/questions/6774086/why-is-my-xlabel-cut-off-in-my-matplotlib-plot
        self.plot = Actual_Plot()
        self.plot.show()

class Actual_Plot(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.title = 'Arb and Trigger Pulse'
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
        ax.plot(marker)
        ax.plot(pulse_no_sinc)

        if sinc_exists:
            ax.plot(sinc)

        scale_x = 1e4 # rescaling x-axis using trick from here: https://stackoverflow.com/questions/10171618/changing-plot-scale-by-a-factor-in-matplotlib
        ticks_x = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/scale_x))
        ax.xaxis.set_major_formatter(ticks_x)

        ax.set_title('Arb and Trigger Pulse')
        ax.set_xlabel('Time (microseconds)')
        ax.set_ylabel('FID Amplitude (arb. units)')
        self.draw()


def chirp_pulse(t,v,Width,Chirp_Duration):
    out_chirp = (numpy.sin((2*numpy.pi*(v*10**6)*t)+2*numpy.pi*(Width*10**6)*(t**2/(2*Chirp_Duration*10**-6))))
    return out_chirp

def one_chirp(f,Width,Chirp_Duration,sample_rate):
    N = int((Chirp_Duration*10**-6)*(sample_rate*10**9))
    out = numpy.zeros(N)
    for i in range(N):
        t = float(i)/(sample_rate*10**9)
        out[i] = (chirp_pulse(t,f,Width,Chirp_Duration))
    return out

def chirp_waveform(Chirp_Delay,sample_rate,Overall_Chirp_Start,Width,Chirp_Duration,waveform_points):
    N_delay = int(numpy.floor((Chirp_Delay*10**-6)*(sample_rate*10**9)))
    first_zeros = numpy.zeros(N_delay) # beginning zeros
    f = Overall_Chirp_Start # start chirp frequency
    temp_chirp = one_chirp(f,Width,Chirp_Duration,sample_rate) # chirp
    total_zeros_chirp = first_zeros.size + temp_chirp.size
    last_zeros_chirp = numpy.zeros(waveform_points-(total_zeros_chirp))
    chirp_wave = numpy.concatenate((first_zeros,temp_chirp,last_zeros_chirp))
    return chirp_wave

def sinc_pulse(t,f,Sinc_Bandwidth): # t is time within a sinc pulse, with sinc centered on t = 0
    sinc_out = numpy.sinc((Sinc_Bandwidth*10**6)*(t)/numpy.pi)*numpy.cos(2*numpy.pi*(f*10**6)*t) # first part is sinc envelope, second is carrier frequency
    return sinc_out

def one_sinc(f,Sinc_Window,sample_rate,Sinc_Bandwidth):
    N = int((Sinc_Window*10**-6)*(sample_rate*10**9))
    out = numpy.zeros(N)
    for i in range(N):
       t = float(i)/(sample_rate*10**9)-(Sinc_Window/2)*10**-6
       out[i] = (sinc_pulse(t,f,Sinc_Bandwidth))
    return out

def sinc_waveform(d,f,DR_Amp,Sinc_Window,sample_rate,Sinc_Bandwidth,waveform_points):
    N_on = int(numpy.floor(((d-(Sinc_Window/2))*10**-6)*sample_rate*10**9)) # d = sinc_delay
    first_zeros = numpy.zeros(N_on)
    temp_sinc = one_sinc(f,Sinc_Window,sample_rate,Sinc_Bandwidth)*DR_Amp # sinc
    last_zeros = numpy.zeros(waveform_points-(first_zeros.size + temp_sinc.size))
    sinc_wave = numpy.concatenate((first_zeros, temp_sinc, last_zeros))
    return sinc_wave

def marker1(Ch1_on,sample_rate,Ch1_off,waveform_points):
    N_on = int(numpy.floor((Ch1_on*10**-6)*(sample_rate*10**9)))
    N_off = int(numpy.ceil((Ch1_off*10**-6)*(sample_rate*10**9)))
    first_zeros = numpy.zeros(N_on-1)
    ones = numpy.ones(N_off - first_zeros.size)
    last_zeros = numpy.zeros(waveform_points - ones.size - first_zeros.size)
    out_marker = numpy.concatenate((first_zeros,ones,last_zeros))
    return out_marker

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog_First_Window()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec_())