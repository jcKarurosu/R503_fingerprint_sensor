# R503 Fingerprint Sensor
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This is a basic program with code to start working and understand how works R503 fingerprint sensor.

## Software structure

There are two files: `main.py` and `r503_sensor.py`.

- `main.py`: This file displays a console-based menu to the user, allowing them to test the functionality of the sensor.

- `r503_sensor.py`: Located within the `jcLibs` folder, this file contains the core functions necessary for interacting with the sensor. It is the primary file you should use to quickly implement a program that works with the R503 sensor.

## Hardware needed

- [R503 Fingerprint Sensor 3.3V version](https://zjgrow.com/grow-r503-new-circular-round-two-color-ring-indicator-led-control-dc33v-mx10-6pin-capacitive-fingerprint-module-sensor-scanner-p2112363.html)
- [Raspberry Pi Pico](https://www.raspberrypi.com/products/raspberry-pi-pico/)

## Software

- Visual Studio Code with MicroPico extension
- Setup Micropython on the Raspberry Pi Pico, instructions and downloads [here](https://micropython.org/download/?vendor=Raspberry%20Pi)

## Setting the Hardware

Make the connections that are shown in the next table

![Conections Screenshot](https://github.com/jcKarurosu/PuertaDigital/blob/33086ff06544216921624508046400ebfd028fac/conecciones.png?raw=true)

Use a micro USB cable to connect the Raspberry Pi Pico to a USB port on your PC.

## Running the software

1. Open Visual Studio Code
2. Open the folder in which you save the files
3. Initialize your project, press the keys `Ctrl + Shift + P` and search for `MicroPico: Initialize MicroPico project` in the command bar of VS code
	![micropico initialization](https://github.com/jcKarurosu/PuertaDigital/blob/master/initialization.png?raw=true)
4. If your Raspberry was already connected the message: `Connection to Micropython board established` will appear indicating a succesful connection.
5. Righ click on `jcLibs` Folder from the explorer side bar and select `upload project to Pico`
	![upload-project-to-pico](https://github.com/jcKarurosu/PuertaDigital/blob/master/upload_files.png?raw=true)
6. Select `main.py` file and then run the program by clicking on the Run menu at the bottom left of the screen
7. In the terminal you will see the program running and the menu for testing the functions of the sensor
	![console](https://github.com/jcKarurosu/PuertaDigital/blob/master/console.png?raw=true)
8. Have fun
