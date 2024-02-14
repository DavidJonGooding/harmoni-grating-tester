"""import tkinter as tk
from tkinter import ttk


def calculate_grating_angle(parent_window):
    def calculate():

        try:
            lines_per_mm = float(lines_per_mm_value.get())
            m = int(m_value.get())
            wavelength_nm = float(wavelength_value.get())

            if lines_per_mm <= 0 or m <= 0 or wavelength_nm <= 0:
                result_label.config(text="Please enter valid values.")
                return

            d = 1 / lines_per_mm  # Calculate grating spacing from line density
            wavelength_m = wavelength_nm * 1e-9  # Convert nm to meters
            angle = m * wavelength_m / (2 * d)
            result_label.config(text=f"Calculated Angle: {angle:.2f} degrees")
        except ValueError:
            result_label.config(text="Please enter valid values.")

    # Create Grating Calculator window inside the parent window
    calculator_frame = ttk.Frame(parent_window)
    calculator_frame.pack(padx=20, pady=20)

# Create main window
root = tk.Tk()
root.title("Grating Equation Calculator")

# Labels
lines_per_mm_label = ttk.Label(root, text="Line Density (lines/mm):")
m_label = ttk.Label(root, text="Order (m):")
wavelength_label = ttk.Label(root, text="Wavelength (nm):")
result_label = ttk.Label(root, text="Calculated Angle: ")

# Entry fields
lines_per_mm_value = tk.StringVar()
lines_per_mm_entry = ttk.Entry(root, textvariable=lines_per_mm_value)

m_value = tk.StringVar()
m_entry = ttk.Entry(root, textvariable=m_value)

wavelength_value = tk.StringVar()
wavelength_entry = ttk.Entry(root, textvariable=wavelength_value)

# Calculate button
calculate_button = ttk.Button(root, text="Calculate", command=calculate)

# Layout
lines_per_mm_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
lines_per_mm_entry.grid(row=0, column=1, padx=10, pady=5)

m_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
m_entry.grid(row=1, column=1, padx=10, pady=5)

wavelength_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
wavelength_entry.grid(row=2, column=1, padx=10, pady=5)

calculate_button.grid(row=3, columnspan=2, padx=10, pady=10)

result_label.grid(row=4, columnspan=2, padx=10, pady=5)

# Start the main loop
root.mainloop()
"""
#%%
import tkinter as tk
from tkinter import ttk
import math

def calculate():
    try:
        lines_per_mm = float(lines_per_mm_value.get())
        m = int(m_value.get())
        wavelength_nm = float(wavelength_value.get())

        if lines_per_mm <= 0 or m <= 0 or wavelength_nm <= 0:
            result_label.config(text="Please enter valid values.")
            return

        d = 1 / (lines_per_mm * 1000)  # Calculate grating spacing from line density in meters
        wavelength_m = wavelength_nm * 1e-9  # Convert nm to meters
        angle = math.degrees(math.asin(m * wavelength_m / (2 * d)))
        result_label.config(text=f"Calculated Angle: {angle:.2f} degrees")
    except ValueError:
        result_label.config(text="Please enter valid values.")


def calculate_grating_angle(parent_window):
    # Create Grating Calculator window inside the parent window
    calculator_frame = ttk.Frame(parent_window)
    calculator_frame.pack(padx=20, pady=20)

# Create main window
root = tk.Tk()
root.title("Grating Equation Calculator")

# Labels
lines_per_mm_label = ttk.Label(root, text="Line Density (lines/mm):")
m_label = ttk.Label(root, text="Order (m):")
wavelength_label = ttk.Label(root, text="Wavelength (nm):")
result_label = ttk.Label(root, text="Calculated Angle: ")

# Entry fields
lines_per_mm_value = tk.StringVar()
lines_per_mm_entry = ttk.Entry(root, textvariable=lines_per_mm_value)

m_value = tk.StringVar()
m_entry = ttk.Entry(root, textvariable=m_value)

wavelength_value = tk.StringVar()
wavelength_entry = ttk.Entry(root, textvariable=wavelength_value)

# Calculate button
calculate_button = ttk.Button(root, text="Calculate", command=calculate)

# Layout
lines_per_mm_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
lines_per_mm_entry.grid(row=0, column=1, padx=10, pady=5)

m_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
m_entry.grid(row=1, column=1, padx=10, pady=5)

wavelength_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
wavelength_entry.grid(row=2, column=1, padx=10, pady=5)

calculate_button.grid(row=3, columnspan=2, padx=10, pady=10)

result_label.grid(row=4, columnspan=2, padx=10, pady=5)

# Start the main loop
root.mainloop()



#%%
