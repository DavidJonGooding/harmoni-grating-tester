"""
Project: Grating Tester
File: gratinggui.py
Author: David Gooding
Version: 1.0
Date: 16/05/2023

This software provides a Graphical User Interface (GUI) for running semi-automated optical transmission experiments.
The GUI allows the user to enter the desired wavelength, x and y translations, establish connections with the equipment,
 and run the experiment.

Dependencies:
- tkinter: Python's standard GUI library
- PIL (Pillow): Python Imaging Library for image display

Usage: Run the script and interact with the GUI to control the experiment setup and perform optical transmission tests
on diffraction gratings.

"""
# gui packages
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import tkinter.filedialog
from PIL import Image, ImageTk
from threading import *

# general packages
import scipy.optimize
import numpy as np
import time
import os
from matplotlib import pyplot as plt
from tqdm import tqdm_notebook as tqdm
import winsound
import csv
import subprocess

# hardware packages
import bendev   # Bentham monochromator
from slave.transport import Socket
from slave.signal_recovery import SR7230    # Lock-in amplifier
from slave.misc import LockInMeasurement
import thorlabs_apt as apt  # Thorlabs stages
import serial   # Newmark stages
# from py_thorlabs_tsp import ThorlabsTsp01B  # Thorlabs temperature and humidity sensor


class ExperimentGUI:
    def connect_laser(self):
        self.output_text.insert(tk.END, "Connecting to laser...\n")
        # Connect to the laser equipment
        # Example: Laser.connect()

        self.output_text.insert(tk.END, "Laser connected.\n\n")
        self.output_text.see(tk.END)
        self.update_indicator_lights("laser")  # Update the indicator light for the laser

    def connect_monochromator(self):
        self.output_text.insert(tk.END, "Connecting to monochromator...\n")
        # Connect to the monochromator equipment
        #with bendev.Device() as dev:
        #    print(dev.query("*IDN?"))
        #    dev.write("SYSTEM:REMOTE")
        #    print(dev.write("SYSTEM:ERR?"))
        #    self.output_text.insert(tk.END, dev.query("*IDN?")+ "\n")
        #    self.output_text.see(tk.END)
        mono = bendev.Device()
        print(mono.query("*IDN?"))
        mono.write("SYSTEM:REMOTE")
        self.output_text.insert(tk.END, mono.query("*IDN?") + "\n")
        # if error, then output error message
        if mono.write("SYSTEM:ERR?") != None:
            self.output_text.insert(tk.END, mono.write("SYSTEM:ERR?") + "\n")
        self.output_text.see(tk.END)
        self.output_text.insert(tk.END, "Monochromator connected.\n\n")
        self.output_text.see(tk.END)
        self.update_indicator_lights("monochromator")  # Update the indicator light for the monochromator

    def connect_x_translation(self):
        self.output_text.insert(tk.END, "Connecting to X translation stage...\n")
        # Connect to the X translation stage equipment
        ser_x = serial.Serial('COM4', baudrate=9600, timeout=0)
        print(ser_x.isOpen())
        self.output_text.insert(tk.END, ser_x.isOpen())
        self.output_text.insert(tk.END, "\nX translation stage connected.\n\n")
        self.output_text.see(tk.END)
        self.update_indicator_lights("x_translation")  # Update the indicator light for the X translation stage

    def connect_y_translation(self):
        self.output_text.insert(tk.END, "Connecting to Y translation stage...\n")
        # Connect to the Y translation stage equipment
        ser_y = serial.Serial('COM5', baudrate=9600, timeout=0)
        print(ser_y.isOpen())
        self.output_text.insert(tk.END, ser_y.isOpen())
        self.output_text.insert(tk.END, "\nY translation stage connected.\n\n")
        self.output_text.see(tk.END)
        self.update_indicator_lights("y_translation")  # Update the indicator light for the Y translation stage

    def connect_rotation1(self):
        self.output_text.insert(tk.END, "Connecting to rotation 1 stage...\n")
        self.output_text.see(tk.END)
        # Connect to the first rotation stage equipment
        devices = apt.list_available_devices()
        print(devices)
        motor1 = apt.Motor(devices[0][1])
        print("Connected to device #", devices[0][1])
        self.output_text.insert(tk.END, "Rotation 1 stage connected.\n\n")
        self.output_text.see(tk.END)
        self.update_indicator_lights("rotation1")  # Update the indicator light for rotation 1 stage

    def connect_rotation2(self):
        self.output_text.insert(tk.END, "Connecting to rotation 2 stage...\n")
        self.output_text.see(tk.END)
        # Connect to the second rotation stage equipment
        devices = apt.list_available_devices()
        print(devices)
        motor2 = apt.Motor(devices[1][1])
        print("Connected to device #", devices[1][1])
        self.output_text.insert(tk.END, "Rotation 2 stage connected.\n\n")
        self.output_text.see(tk.END)
        self.update_indicator_lights("rotation2")  # Update the indicator light for rotation 2 stage

    def connect_lockin_amplifier(self):
        self.output_text.insert(tk.END, "Connecting to lock-in amplifier...\n")
        # Connect to the lock-in amplifier equipment
        lockin = SR7230(Socket(address=('169.254.150.230', 50000)))
        lockin.fast_buffer.enabled = True   # Use fast curve buffer.
        self.output_text.insert(tk.END, "Lock-in amplifier connected.\n\n")
        self.output_text.see(tk.END)
        self.update_indicator_lights("lockin_amplifier")  # Update the indicator light for the lock-in amplifier

    def update_indicator_lights(self, equipment):
        # Update the indicator light based on the connection status of the specified equipment
        if equipment == "laser":
            self.laser_indicator.configure(text="Laser: Connected", fg="green")
        elif equipment == "monochromator":
            self.monochromator_indicator.configure(text="Monochromator: Connected", fg="green")
        elif equipment == "x_translation":
            self.x_translation_indicator.configure(text="X Translation: Connected", fg="green")
        elif equipment == "y_translation":
            self.y_translation_indicator.configure(text="Y Translation: Connected", fg="green")
        elif equipment == "rotation1":
            self.rotation1_indicator.configure(text="Rotation 1: Connected", fg="green")
        elif equipment == "rotation2":
            self.rotation2_indicator.configure(text="Rotation 2: Connected", fg="green")
        elif equipment == "lockin_amplifier":
            self.lockin_amplifier_indicator.configure(text="Lock-in Amplifier: Connected", fg="green")

    #def output_message(self, message):
    #    # Output a message to the GUI
    #    self.output_text.insert(tk.END, message + '\n')
    #    self.output_text.see(tk.END)  # Scroll to the bottom to show the latest message

    def output_message(self, message):
        # Schedule the update operations to be run on the main thread
        self.output_text.after(0, lambda: (self.output_text.insert(tk.END, message + '\n'), self.output_text.see(tk.END)))

    def set_wavelength(self):
        wavelength = self.wavelength_entry.get()
        if wavelength:
            self.wavelength = float(wavelength)
            mono = bendev.Device()
            mono.write("SYSTEM:REMOTE")
            mono.query("MONO:GOTO? %s" % self.wavelength)
            self.output_message(f"Wavelength set to: {self.wavelength} nm")
            self.output_text.see(tk.END)
        else:
            self.output_message("Please enter a valid wavelength.")
            self.output_text.see(tk.END)

    def auto_wavelength(self, wavelength):
        mono = bendev.Device()
        mono.write("SYSTEM:REMOTE")
        mono.query("MONO:GOTO? %s" % wavelength)

    def convert_steps(self, step):
        # TODO: Update this function to convert steps to mm for the translation stages properly
        # Convert the number of steps to a distance in mm, if zero return zero
        if step == 0:
            return 0
        else:
            # conversion factor determined experimentally and verified as step size from the manual
            return float(step) * 8.0645

    def convert_signal(self, signal):
        # TODO: Update this function to convert the signal from the lock-in amplifier to a voltage properly
        # Convert the signal from the lock-in amplifier to a voltage
        return float(signal) / 200

    def move_x_abs(self):
        x_translation_mm = self.x_translation_entry.get()
        x_translation = self.convert_steps(x_translation_mm)
        self.output_message(f"X translation set to: {self.x_translation} mm")
        if x_translation:
            self.x_translation = float(x_translation)
            ser_x = serial.Serial('COM4', baudrate=9600, timeout=0)
            ser_x.write(b'MA ' + str(self.x_translation).encode() + b'\r\n')
            self.output_message(f"X translation set to: {self.x_translation} mm")
            self.output_text.see(tk.END)
        else:
            self.output_message("Please enter a valid X translation.")
            self.output_text.see(tk.END)

    def move_y_abs(self):
        y_translation_mm = self.y_translation_entry.get()
        y_translation = self.convert_steps(y_translation_mm)
        if y_translation:
            self.y_translation = float(y_translation)
            ser_y = serial.Serial('COM5', baudrate=9600, timeout=0)
            ser_y.write(b'MA ' + str(self.y_translation).encode() + b'\r\n')
            self.output_message(f"Y translation set to: {self.y_translation} mm")
            self.output_text.see(tk.END)
        else:
            self.output_message("Please enter a valid Y translation.")
            self.output_text.see(tk.END)

    def move_x_rel(self):
        x_translation_mm = self.x_translation_entry.get()
        x_translation = self.convert_steps(x_translation_mm)
        if x_translation:
            self.x_translation = float(x_translation)
            ser_x = serial.Serial('COM4', baudrate=9600, timeout=0)
            ser_x.write(b'MR ' + str(self.x_translation).encode() + b'\r\n')
            self.output_message(f"X translation moved by: {x_translation_mm} mm")
            self.output_text.see(tk.END)
        else:
            self.output_message("Please enter a valid X translation.")
            self.output_text.see(tk.END)

    def move_y_rel(self):
        y_translation_mm = self.y_translation_entry.get()
        y_translation = self.convert_steps(y_translation_mm)
        if y_translation:
            self.y_translation = float(y_translation)
            ser_y = serial.Serial('COM5', baudrate=9600, timeout=0)
            ser_y.write(b'MR ' + str(self.y_translation).encode() + b'\r\n')
            self.output_message(f"Y translation set to: {y_translation_mm} mm")
            self.output_text.see(tk.END)
        else:
            self.output_message("Please enter a valid Y translation.")
            self.output_text.see(tk.END)

    def move_y_auto(self, y_translation):
        y_translation = self.convert_steps(float(y_translation))
        ser_y = serial.Serial('COM5', baudrate=9600, timeout=0)
        ser_y.write(b'MR ' + str(y_translation).encode() + b'\r\n')

    def move_x_auto(self, x_translation):
        x_translation = self.convert_steps(float(x_translation))
        ser_x = serial.Serial('COM4', baudrate=9600, timeout=0)
        ser_x.write(b'MR ' + str(x_translation).encode() + b'\r\n')

    def zero_x(self):
        ser_x = serial.Serial('COM4', baudrate=9600, timeout=0)
        ser_x.write(b'P=0\r\n')
        self.output_message("X location set to zero")
        self.output_text.see(tk.END)

    def zero_y(self):
        ser_y = serial.Serial('COM5', baudrate=9600, timeout=0)
        ser_y.write(b'P=0\r\n')
        self.output_message("Y location set to zero")
        self.output_text.see(tk.END)

    def reset_buffers(self):
        # Reset the buffers of the lock-in amplifier
        ser_x = serial.Serial('COM4', baudrate=9600, timeout=0)
        ser_y = serial.Serial('COM5', baudrate=9600, timeout=0)
        ser_x.reset_input_buffer()
        ser_y.reset_input_buffer()

    def move_rotation1_abs(self):
        rotation1 = self.rotation1_entry.get()
        if rotation1:
            self.rotation1 = float(rotation1)
            devices = apt.list_available_devices()
            motor1 = apt.Motor(devices[0][1])
            motor1.move_to(self.rotation1/5.5)  # converted to degrees
            self.output_message(f"Rotation 1 set to: {self.rotation1} degrees")
            self.output_text.see(tk.END)
        else:
            self.output_message("Please enter a valid Rotation 1.")
            self.output_text.see(tk.END)

    def move_rotation2_abs(self):
        rotation2 = self.rotation2_entry.get()
        if rotation2:
            self.rotation2 = float(rotation2)
            devices = apt.list_available_devices()
            motor2 = apt.Motor(devices[1][1])
            motor2.move_to(self.rotation2/5.5)  # converted to degrees
            self.output_message(f"Rotation 2 set to: {self.rotation2} degrees")
            self.output_text.see(tk.END)
        else:
            self.output_message("Please enter a valid Rotation 2.")
            self.output_text.see(tk.END)

    def move_rotation1_rel(self):
        rotation1 = self.rotation1_entry.get()
        if rotation1:
            self.rotation1 = float(rotation1)
            devices = apt.list_available_devices()
            motor1 = apt.Motor(devices[0][1])
            motor1.move_by(self.rotation1/5.5)  # converted to degrees
            self.output_message(f"Rotation 1 moved by: {self.rotation1} degrees")
            self.output_text.see(tk.END)
        else:
            self.output_message("Please enter a valid Rotation 1.")
            self.output_text.see(tk.END)

    def move_rotation2_rel(self):
        rotation2 = self.rotation2_entry.get()
        if rotation2:
            self.rotation2 = float(rotation2)
            devices = apt.list_available_devices()
            motor2 = apt.Motor(devices[1][1])
            motor2.move_by(self.rotation2/5.5)  # converted to degrees
            self.output_message(f"Rotation 2 moved by: {self.rotation2} degrees")
            self.output_text.see(tk.END)
        else:
            self.output_message("Please enter a valid Rotation 2.")
            self.output_text.see(tk.END)

    def move_rotation1_home(self):
        devices = apt.list_available_devices()
        motor1 = apt.Motor(devices[0][1])
        motor1.move_home(True)
        self.output_message(f"Rotation 1 moved to home.")
        self.output_text.see(tk.END)

    def move_rotation2_home(self):
        devices = apt.list_available_devices()
        motor2 = apt.Motor(devices[1][1])
        motor2.move_home(True)
        self.output_message(f"Rotation 2 moved to home.")
        self.output_text.see(tk.END)

    def threading(self):
        # call experiment in a thread so that the GUI doesn't freeze
        t1=Thread(target=self.run_experiment)
        t1.start()

    def run_experiment(self):
        # clear the output text box
        self.output_text.insert(tk.END, "\n")
        self.output_text.insert(tk.END, "\n")
        self.output_text.insert(tk.END, "Running experiment...\n")
        self.output_text.see(tk.END)
        time.sleep(1)

        # Create csv file to save data
        if self.save_data.get():
            self.output_text.insert(tk.END, "Creating csv file...\n")
            self.output_text.see(tk.END)
            timestr = time.strftime("%Y%m%d-%H%M%S")
            filename = f"{self.root_folder_entry.get()}/%s_{self.file_name_entry.get()}.csv" % timestr

            # save header information
            header_line = "Wavelength (nm),X step (mm),Y step (mm),Signal (mV),Signal std (mV)"

            with open(filename, mode='w', newline='') as csv_file:
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(header_line.split(','))
            self.output_text.insert(tk.END, f"File created: {filename}\n")
            self.output_text.see(tk.END)

        # Get the parameters from the GUI

        wavelengths = np.arange(float(self.wavelength_start_entry.get()),
                                float(self.wavelength_stop_entry.get()),
                                float(self.wavelength_step_entry.get()))
        self.output_text.insert(tk.END, f"Wavelengths: {wavelengths}\n")

        # if there are x steps, then create an array of x steps
        if self.x_step_number_entry.get():
            x_steps = np.arange(0, (float(self.x_step_size_entry.get()) * float(self.x_step_number_entry.get())),
                                int(self.x_step_size_entry.get()))
            self.output_text.insert(tk.END, f"X steps: {x_steps}\n")
        else:
            x_steps = np.array([0])
            self.output_text.insert(tk.END, f"X steps: {x_steps}\n")

        # if there are y steps, then create an array of y steps
        if self.y_step_number_entry.get():
            y_steps = np.arange(0, (float(self.y_step_size_entry.get()) * float(self.y_step_number_entry.get())),
                                int(self.y_step_size_entry.get()))
            self.output_text.insert(tk.END, f"Y steps: {y_steps}\n")
        else:
            y_steps = np.array([0])
            self.output_text.insert(tk.END, f"Y steps: {y_steps}\n")

        # sleep for 1 second to allow the user to see the message
        time.sleep(1)

        # Run the experiment
        signals = []
        stds = []

        output_data = np.zeros((len(x_steps), len(y_steps), len(wavelengths)))
        output_std = np.zeros((len(x_steps), len(y_steps), len(wavelengths)))
        length = len(x_steps) * len(y_steps) * len(wavelengths)
        full_data = np.zeros((length, 5))

        # loop through the wavelengths
        for k in range(len(wavelengths)):
            # return x to 0
            if k != 0:
                time.sleep(2)
                #self.output_text.insert(tk.END, f"Returning to x = 0\n")
                self.move_x_auto(-x_steps[-1])
                time.sleep(2)
                self.move_y_auto(-y_steps[-1])
                time.sleep(2)

            # wavelength loop
            wavelength = wavelengths[k]
            #self.output_text.insert(tk.END, f"Current wavelength: {wavelength}\n")
            #self.output_text.see(tk.END)
            self.auto_wavelength(wavelength)
            time.sleep(1)

            # loop through the x steps
            for i in range(len(x_steps)):

                # reset buffers
                self.reset_buffers()

                x_step = x_steps[i]

                if i != 0:
                    # return y to 0
                    time.sleep(3)
                    #self.output_text.insert(tk.END, f"Returning to y = 0\n")
                    self.move_y_auto(-y_steps[-1])
                    time.sleep(4)

                    # reset buffers
                    self.reset_buffers()

                    # move x to the next step
                    # self.output_text.insert(tk.END, f"X step: {x_step}\n")
                    # self.output_text.see(tk.END)
                    time.sleep(1)
                    self.move_x_auto(float(self.x_step_size_entry.get()))
                    time.sleep(1)

                # loop through the y steps
                for j in range(len(y_steps)):
                    y_step = y_steps[j]
                    # self.output_text.insert(tk.END, f"Y step: {y_step}\n")
                    # self.output_text.see(tk.END)
                    time.sleep(1)
                    if j != 0:
                        # move y to the next step
                        self.move_y_auto(float(self.y_step_size_entry.get()))
                        time.sleep(1)

                    # take the measurement
                    signal, signal_std = self.acquisition()
                    winsound.Beep(600, 1000)
                    signals.append(signal)
                    stds.append(signal_std)
                    print(wavelength, x_step, y_step, signal, signal_std)
                    self.output_message(f"{wavelength}, {x_step}, {y_step}, {signal}, {signal_std}")
                    output_data[i, j, k] = signal
                    output_std[i, j, k] = signal_std

                    if self.save_data.get():
                        # save the data to a file
                        with open(filename, 'a') as f:
                            f.write(f"{wavelength}, {x_step}, {y_step}, {signal}, {signal_std}\n")

                    # store the data in an array
                    # TODO: fix ordering of wavelengths in data array - not used currently
                    full_data[i * len(y_steps) * len(wavelengths) + j * len(wavelengths) + k, 0] = wavelengths[k]
                    full_data[i * len(y_steps) * len(wavelengths) + j * len(wavelengths) + k, 1] = x_steps[i]
                    full_data[i * len(y_steps) * len(wavelengths) + j * len(wavelengths) + k, 2] = y_steps[j]
                    full_data[i * len(y_steps) * len(wavelengths) + j * len(wavelengths) + k, 3] = signal
                    full_data[i * len(y_steps) * len(wavelengths) + j * len(wavelengths) + k, 4] = signal_std
                    # self.output_text.insert(tk.END, f"Signal: {signal}\n")

                    # plot the data
                    plt.plot(wavelength, signal, 'o', color='black')
                    # plt.errorbar(wavelength, signal, 'o', yerr=signal_std, color='black')

        # return x to 0
        self.output_text.insert(tk.END, f"Returning to x = 0\n")
        self.move_x_auto(-x_steps[-1])
        time.sleep(2)
        # return y to 0
        self.output_text.insert(tk.END, f"Returning to y = 0\n")
        self.move_y_auto(-y_steps[-1])
        time.sleep(2)
        # return wavelength to start position
        self.output_text.insert(tk.END, "Returning wavelength to start position.\n")
        self.auto_wavelength(float(wavelengths[0]))

        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Signal (mV)')
        plt.show()

        # Experiment completed
        winsound.Beep(440, 1000)
        winsound.Beep(440, 2000)
        self.output_text.insert(tk.END, "Experiment completed.\n\n")
        self.output_text.see(tk.END)

    """
    def run_experiment(self):
        self.output_text.insert(tk.END, "\n")
        self.output_text.insert(tk.END, "\n")
        self.output_text.insert(tk.END, "Running experiment...\n")
        self.output_text.see(tk.END)
        # sleep for 1 second to allow the user to see the message
        time.sleep(1)

        # Get the parameters from the GUI

        wavelengths = np.arange(float(self.wavelength_start_entry.get()),
                                float(self.wavelength_stop_entry.get()),
                                float(self.wavelength_step_entry.get()))
        self.output_text.insert(tk.END, f"Wavelengths: {wavelengths}\n")

        # if there are x steps, then create an array of x steps
        if self.x_step_number_entry.get():
            x_steps = np.arange(0, (float(self.x_step_size_entry.get()) * float(self.x_step_number_entry.get())),
                                int(self.x_step_size_entry.get()))
            self.output_text.insert(tk.END, f"X steps: {x_steps}\n")
        else:
            x_steps = np.array([0])
            self.output_text.insert(tk.END, f"X steps: {x_steps}\n")

        # if there are y steps, then create an array of y steps
        if self.y_step_number_entry.get():
            y_steps = np.arange(0, (float(self.y_step_size_entry.get()) * float(self.y_step_number_entry.get())),
                                int(self.y_step_size_entry.get()))
            self.output_text.insert(tk.END, f"Y steps: {y_steps}\n")
        else:
            y_steps = np.array([0])
            self.output_text.insert(tk.END, f"Y steps: {y_steps}\n")

        # sleep for 1 second to allow the user to see the message
        time.sleep(1)

        # Run the experiment
        signals = []
        stds = []

        output_data = np.zeros((len(x_steps), len(y_steps), len(wavelengths)))
        output_std = np.zeros((len(x_steps), len(y_steps), len(wavelengths)))
        length = len(x_steps) * len(y_steps) * len(wavelengths)
        full_data = np.zeros((length, 5))

        for i in range(len(x_steps)):
            # return y to 0
            if i != 0:
                time.sleep(1)
                self.output_text.insert(tk.END, f"Returning to y = 0\n")
                self.move_y_auto(-y_steps[-1])
                time.sleep(1)

            # x step loop
            x_step = x_steps[i]
            self.output_text.insert(tk.END, f"X step: {x_step}\n")
            self.output_text.see(tk.END)
            time.sleep(1)
            self.move_x_auto(float(self.x_step_size_entry.get()))
            time.sleep(1)

            for j in range(len(y_steps)):
                # y step loop
                y_step = y_steps[j]
                self.output_text.insert(tk.END, f"Y step: {y_step}\n")
                self.output_text.see(tk.END)
                time.sleep(1)
                self.move_y_auto(float(self.y_step_size_entry.get()))
                time.sleep(1)

                for k in range(len(wavelengths)):
                    # wavelength loop
                    wavelength = wavelengths[k]
                    self.output_text.insert(tk.END, f"Current wavelength: {wavelength}\n")
                    self.output_text.see(tk.END)
                    self.auto_wavelength(wavelength)

                    signal, signal_std = self.acquisition()
                    signals.append(signal)
                    stds.append(signal_std)
                    print(signal)
                    print(signal_std)
                    output_data[i, j, k] = signal
                    output_std[i, j, k] = signal_std
                    full_data[i * len(y_steps) * len(wavelengths) + j * len(wavelengths) + k, 0] = wavelengths[k]
                    full_data[i * len(y_steps) * len(wavelengths) + j * len(wavelengths) + k, 1] = x_steps[i]
                    full_data[i * len(y_steps) * len(wavelengths) + j * len(wavelengths) + k, 2] = y_steps[j]
                    full_data[i * len(y_steps) * len(wavelengths) + j * len(wavelengths) + k, 3] = signal
                    full_data[i * len(y_steps) * len(wavelengths) + j * len(wavelengths) + k, 4] = signal_std
                    self.output_text.insert(tk.END, f"Signal: {signal}\n")

                    plt.plot(wavelength, signal, 'o', color='black')
                    # plt.errorbar(wavelength, signal, 'o', yerr=signal_std, color='black')

        # return x to 0
        self.output_text.insert(tk.END, f"Returning to x = 0\n")
        self.move_x_auto(-x_steps[-1])

        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Signal (a.u.)')
        plt.show()

        # return wavelength to start position
        self.output_text.insert(tk.END, "Returning wavelength to start position.\n")
        self.auto_wavelength(float(wavelengths[0]))

        # save the data if box is ticked
        if self.save_data.get():
            self.output_text.insert(tk.END, "Saving data...\n")
            self.output_text.see(tk.END)
            # save the data
            # wavelengths_save = np.tile(wavelengths, len(x_steps) * len(y_steps))
            # x_steps_save = np.repeat(x_steps, len(y_steps))
            # y_steps_save = np.tile(y_steps, len(x_steps))
            # signals_save = np.array(signals).flatten()
            # stds_save = np.array(stds).flatten()
            # print(wavelengths_save)
            # print(x_steps_save)
            # print(y_steps_save)
            # print(signals_save)
            # print(stds_save)
            # self.save_data_csv(wavelengths_save, x_steps_save, y_steps_save, signals_save, stds_save)
            # self.save_data_csv(wavelengths, x_steps, y_steps, signals, stds)

            timestr = time.strftime("%Y%m%d-%H%M%S")
            filename = f"{self.root_folder_entry.get()}/%s_{self.file_name_entry.get()}.csv" % timestr
            # save the data to csv
            np.savetxt(filename, np.column_stack(full_data).T, delimiter=",", header="Wavelength (nm), X step (mm), Y step (mm), Signal (a.u.), Signal std (a.u.)")
            self.output_text.insert(tk.END, f"Data saved to {filename}\n")
            self.output_text.see(tk.END)

        # Experiment completed
        winsound.Beep(440, 1000)
        self.output_text.insert(tk.END, "Experiment completed.\n\n")
        self.output_text.see(tk.END)
        """

    def acquisition(self, rate: int = 10000, length: int = 500):
        # Take data from the lock-in
        lockin = SR7230(Socket(address=('169.254.150.230', 50000)))
        lockin.fast_buffer.enabled = True  # Use fast curve buffer.

        # Set the fast buffer parameters
        lockin.fast_buffer.storage_interval = rate  # Take data every x us.
        lockin.fast_buffer.length = length  # Store the max number of points
        lockin.take_data()  # Start data acquisition immediately.

        # Wait for the data to be taken
        while lockin.acquisition_status[0] == 'on':
            time.sleep(0.1)

        # Get the data
        x = lockin.fast_buffer['x']

        # Return the data
        return self.convert_signal(np.mean(x)), self.convert_signal(np.std(x))

    def browse_root_folder(self):
        self.root_folder = tk.filedialog.askdirectory()
        self.root_folder_entry.delete(0, tk.END)
        self.root_folder_entry.insert(0, self.root_folder)

    def open_help(self):
        # open pdf file
        os.startfile("Grating Test Instructions.pdf")

    def save_data_csv(self, wavelengths, x_steps, y_steps, signal, signal_std):
        # create a filename
        timestr = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{self.root_folder_entry.get()}/%s_{self.file_name_entry.get()}.csv" % timestr
        # save the data to csv
        np.savetxt(filename, np.column_stack([wavelengths, x_steps, y_steps, signal, signal_std]), delimiter=",",
                      header="Wavelength (nm), X Step (mm), Y Step (mm), Signal (V), Signal Std (V)", comments='')
        self.output_text.insert(tk.END, f"Data saved to {filename}\n")
        self.output_text.see(tk.END)

    def open_grating_calculator(self):
        calculator_path = "gratingequation.py"
        subprocess.Popen(["python", calculator_path])

    def __init__(self, master):
        self.master = master
        master.title("Grating Tester v0.1")

        # CONNECTION FRAME

        # Display image on top left of GUI
        image_file = "vphgicon.png"
        image = Image.open(image_file)
        image = image.resize((100, 100), Image.LANCZOS)
        image = ImageTk.PhotoImage(image)
        image_label = tk.Label(connect_frame, image=image)
        image_label.image = image
        image_label.grid(row=0, column=0, padx=10, pady=10)

        # Create buttons to connect/disconnect equipment
        self.monochromator_indicator = tk.Label(connect_frame, text="Monochromator: Not Connected", fg="red")
        self.monochromator_indicator.grid(row=2, column=0, padx=5, pady=5)
        self.x_translation_indicator = tk.Label(connect_frame, text="X Translation: Not Connected", fg="red")
        self.x_translation_indicator.grid(row=3, column=0, padx=10, pady=5)
        self.y_translation_indicator = tk.Label(connect_frame, text="Y Translation: Not Connected", fg="red")
        self.y_translation_indicator.grid(row=4, column=0, padx=10, pady=5)
        self.rotation1_indicator = tk.Label(connect_frame, text="Rotation 1: Not Connected", fg="red")
        self.rotation1_indicator.grid(row=5, column=0, padx=10, pady=5)
        self.rotation2_indicator = tk.Label(connect_frame, text="Rotation 2: Not Connected", fg="red")
        self.rotation2_indicator.grid(row=6, column=0, padx=10, pady=5)
        self.lockin_amplifier_indicator = tk.Label(connect_frame, text="Lock-in Amplifier: Not Connected", fg="red")
        self.lockin_amplifier_indicator.grid(row=7, column=0, padx=10, pady=5)

        # self.laser_connect_button = tk.Button(connect_frame, text="Connect", command=self.connect_laser)
        # self.laser_connect_button.grid(row=1, column=1, padx=10, pady=5)
        self.monochromator_connect_button = tk.Button(connect_frame, text="Connect", command=self.connect_monochromator)
        self.monochromator_connect_button.grid(row=2, column=1, padx=10, pady=5)
        self.x_translation_connect_button = tk.Button(connect_frame, text="Connect", command=self.connect_x_translation)
        self.x_translation_connect_button.grid(row=3, column=1, padx=10, pady=5)
        self.y_translation_connect_button = tk.Button(connect_frame, text="Connect", command=self.connect_y_translation)
        self.y_translation_connect_button.grid(row=4, column=1, padx=10, pady=5)
        self.rotation1_connect_button = tk.Button(connect_frame, text="Connect", command=self.connect_rotation1)
        self.rotation1_connect_button.grid(row=5, column=1, padx=10, pady=5)
        self.rotation2_connect_button = tk.Button(connect_frame, text="Connect", command=self.connect_rotation2)
        self.rotation2_connect_button.grid(row=6, column=1, padx=10, pady=5)
        self.lockin_amplifier_connect_button = tk.Button(connect_frame, text="Connect", command=self.connect_lockin_amplifier)
        self.lockin_amplifier_connect_button.grid(row=7, column=1, padx=10, pady=5)

        # CONTROL HARDWARE FRAME

        # Control wavelength
        self.wavelength_label = tk.Label(control_frame, text="Wavelength (nm):")
        self.wavelength_label.grid(row=1, column=0, padx=5, pady=5)
        self.default_wavelength = tk.StringVar(value="700")
        self.wavelength_entry = tk.Entry(control_frame, width=10, textvariable=self.default_wavelength)
        self.wavelength_entry.grid(row=1, column=1, padx=10, pady=5)
        self.set_wavelength_button = tk.Button(control_frame, text="Set", command=self.set_wavelength)
        self.set_wavelength_button.grid(row=1, column=2, padx=10, pady=10)

        # Move X stage
        self.x_translation_label = tk.Label(control_frame, text="X translation (mm):")
        self.x_translation_label.grid(row=2, column=0, padx=10, pady=5)
        self.x_translation_entry = tk.Entry(control_frame, width=10)
        self.x_translation_entry.grid(row=2, column=1, padx=10, pady=5)
        self.move_x_abs_button = tk.Button(control_frame, text="Absolute", command=self.move_x_abs)
        self.move_x_abs_button.grid(row=2, column=2, padx=10, pady=10)
        self.move_x_rel_button = tk.Button(control_frame, text="Relative", command=self.move_x_rel)
        self.move_x_rel_button.grid(row=2, column=3, padx=10, pady=10)
        self.zero_x_button = tk.Button(control_frame, text="Zero", command=self.zero_x)
        self.zero_x_button.grid(row=2, column=4, padx=10, pady=10)

        # Move Y stage
        self.y_translation_label = tk.Label(control_frame, text="Y translation (mm):")
        self.y_translation_label.grid(row=3, column=0, padx=10, pady=5)
        self.y_translation_entry = tk.Entry(control_frame, width=10)
        self.y_translation_entry.grid(row=3, column=1, padx=10, pady=5)
        self.move_y_abs_button = tk.Button(control_frame, text="Absolute", command=self.move_y_abs)
        self.move_y_abs_button.grid(row=3, column=2, padx=10, pady=10)
        self.move_y_rel_button = tk.Button(control_frame, text="Relative", command=self.move_y_rel)
        self.move_y_rel_button.grid(row=3, column=3, padx=10, pady=10)
        self.zero_y_button = tk.Button(control_frame, text="Zero", command=self.zero_y)
        self.zero_y_button.grid(row=3, column=4, padx=10, pady=10)

        # Move Rotation 1 stage
        self.rotation1_label = tk.Label(control_frame, text="Rotation 1 (deg):")
        self.rotation1_label.grid(row=4, column=0, padx=10, pady=5)
        self.rotation1_entry = tk.Entry(control_frame, width=10)
        self.rotation1_entry.grid(row=4, column=1, padx=10, pady=5)
        self.move_rotation1_abs_button = tk.Button(control_frame, text="Absolute", command=self.move_rotation1_abs)
        self.move_rotation1_abs_button.grid(row=4, column=2, padx=10, pady=10)
        self.move_rotation1_rel_button = tk.Button(control_frame, text="Relative", command=self.move_rotation1_rel)
        self.move_rotation1_rel_button.grid(row=4, column=3, padx=10, pady=10)
        self.move_rotation1_home_button = tk.Button(control_frame, text="Home", command=self.move_rotation1_home)
        self.move_rotation1_home_button.grid(row=4, column=4, padx=10, pady=10)

        # Move Rotation 2 stage
        self.rotation2_label = tk.Label(control_frame, text="Rotation 2 (deg):")
        self.rotation2_label.grid(row=5, column=0, padx=10, pady=5)
        self.rotation2_entry = tk.Entry(control_frame, width=10)
        self.rotation2_entry.grid(row=5, column=1, padx=10, pady=5)
        self.move_rotation2_abs_button = tk.Button(control_frame, text="Absolute", command=self.move_rotation2_abs)
        self.move_rotation2_abs_button.grid(row=5, column=2, padx=10, pady=10)
        self.move_rotation2_rel_button = tk.Button(control_frame, text="Relative", command=self.move_rotation2_rel)
        self.move_rotation2_rel_button.grid(row=5, column=3, padx=10, pady=10)
        self.move_rotation2_home_button = tk.Button(control_frame, text="Home", command=self.move_rotation2_home)
        self.move_rotation2_home_button.grid(row=5, column=4, padx=10, pady=10)

        # EXPERIMENT FRAME

        # Define wavelength start, stop, and step size
        self.wavelength_start_label = tk.Label(experiment_frame, text="Wavelength [start, stop, step] (nm):")
        self.wavelength_start_label.grid(row=1, column=0, padx=10, pady=5)
        self.wavelength_start_entry = tk.Entry(experiment_frame, width=10)
        self.wavelength_start_entry.grid(row=1, column=1, padx=10, pady=5)
        self.wavelength_stop_entry = tk.Entry(experiment_frame, width=10)
        self.wavelength_stop_entry.grid(row=1, column=2, padx=10, pady=5)
        self.wavelength_step_entry = tk.Entry(experiment_frame, width=10)
        self.wavelength_step_entry.grid(row=1, column=3, padx=10, pady=5)

        # Define X translation distance
        self.x_step_label = tk.Label(experiment_frame, text="X translation [step, # steps] (mm):")
        self.x_step_label.grid(row=2, column=0, padx=10, pady=5)
        self.x_step_size_entry = tk.Entry(experiment_frame, width=10)
        self.x_step_size_entry.grid(row=2, column=1, padx=10, pady=5)
        self.x_step_number_entry = tk.Entry(experiment_frame, width=10)
        self.x_step_number_entry.grid(row=2, column=2, padx=10, pady=5)

        # Define Y translation distance
        self.y_step_label = tk.Label(experiment_frame, text="Y translation [step, # steps] (mm):")
        self.y_step_label.grid(row=3, column=0, padx=10, pady=5)
        self.y_step_size_entry = tk.Entry(experiment_frame, width=10)
        self.y_step_size_entry.grid(row=3, column=1, padx=10, pady=5)
        self.y_step_number_entry = tk.Entry(experiment_frame, width=10)
        self.y_step_number_entry.grid(row=3, column=2, padx=10, pady=5)

        # self.output_text = ScrolledText(master, height=8, width=60)
        # self.output_text.grid(row=5, column=0, columnspan=7, padx=10, pady=10)

        # Define root folder to save data
        self.root_folder_label = tk.Label(experiment_frame, text="Save data to:")
        self.root_folder_label.grid(row=7, column=0, padx=10, pady=5)
        self.default_folder = tk.StringVar(value="C:/Users/gooding/Desktop/Automation/Results")
        self.root_folder_entry = tk.Entry(experiment_frame, width=50, textvariable=self.default_folder)
        self.root_folder_entry.grid(row=7, column=1, columnspan=3, padx=10, pady=5)
        self.root_folder_button = tk.Button(experiment_frame, text="Browse", command=self.browse_root_folder)
        self.root_folder_button.grid(row=7, column=4, padx=10, pady=10)

        # Define file name
        self.file_name_label = tk.Label(experiment_frame, text="File name:")
        self.file_name_label.grid(row=8, column=0, padx=10, pady=5)
        self.file_name_entry = tk.Entry(experiment_frame, width=50)
        self.file_name_entry.grid(row=8, column=1, columnspan=3, padx=10, pady=5)

        # add a tick box to save data, default is checked
        self.save_data = tk.IntVar(value=1)
        self.save_data_checkbutton = tk.Checkbutton(experiment_frame, text="Save data", variable=self.save_data)
        self.save_data_checkbutton.grid(row=8, column=4, padx=10, pady=10)

        # Buttons
        self.run_button = tk.Button(experiment_frame, text="Run", command=self.threading)
        #command=self.run_experiment)
        self.run_button.grid(row=9, column=3, padx=10, pady=10)
        self.quit_button = tk.Button(experiment_frame, text="Quit", command=master.quit)
        self.quit_button.grid(row=9, column=4, padx=10, pady=10)
        # add a help button to open pdf manual
        self.help_button = tk.Button(experiment_frame, text="Help", command=self.open_help)
        self.help_button.grid(row=9, column=0, padx=10, pady=10)
        self.open_calculator_button = tk.Button(root, text="Grating Calculator", command=self.open_grating_calculator)
        self.open_calculator_button.grid(row=9, column=1, padx=10, pady=10)

        # OUTPUT TEXT FRAME

        self.output_text = ScrolledText(master, height=10, width=80)
        self.output_text.grid(row=5, column=0, columnspan=7, padx=10, pady=10)
        # Call output_message to display initial message
        self.output_message("Welcome to the Grating Tester GUI!")
        self.output_message("v0.1.0")
        self.output_message("Author: David Gooding")
        self.output_message("Date: 2023-05-16")


# Create the main window
root = tk.Tk()
root.iconbitmap("vphgicon.ico")

# Create connect frame
connect_frame = tk.Frame(root, width=200, height=400)
connect_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=5)
tk.Label(connect_frame, text="Connect hardware", font='Helvetica 12 bold', justify="left", anchor="w").grid(row=1, column=0, padx=5, pady=5)

# Create control frame
control_frame = tk.Frame(root, width=200, height=400)
control_frame.grid(row=0, column=1, padx=10, pady=5)
tk.Label(control_frame, text="Control hardware", font='Helvetica 12 bold', justify="left", anchor="w").grid(row=0, column=0, padx=5, pady=5)

# Create experiment frame
experiment_frame = tk.Frame(root, width=200, height=400)
experiment_frame.grid(row=1, column=1, padx=10, pady=5)
tk.Label(experiment_frame, text="Experiment settings", font='Helvetica 12 bold', justify="left", anchor="w").grid(row=0, column=0, padx=5, pady=5)

# Create an instance of the experiment GUI
experiment = ExperimentGUI(root)

# Run the GUI
root.mainloop()


#%%

#%%

#%%
