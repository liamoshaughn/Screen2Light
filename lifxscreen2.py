#!/usr/bin/env python
# coding=utf-8
from time import sleep
from PIL import ImageGrab
from lifxlan import BLUE, GREEN, LifxLAN
import time
import os
from colour import Color
import sys
import math
import binascii
from tkinter import *
import asyncio
from async_tkinter_loop import async_handler, async_mainloop

# //////////////////////////////////////////////////////////////////////////////////////////////////////////
# GLOBAL DEFINES
# //////////////////////////////////////////////////////////////////////////////////////////////////////////
KELVIN = 5000    # 2000 to 8000, where 2000 is the warmest and 8000 is the coolest
DECIMATE = 10   # skip every DECIMATE number of pixels to speed up calculation
DURATION = 500  # The time over which to change the colour of the lights in ms. Use 100 for faster transitions
BLACK_THRESHOLD = 0.2  # Black Screen Detection Threshold
# Black Screen case's brightness setting
BLACK_BRIGHTNESS = int(round(0x10000 * 0.03*360)/360) % 0x10000
BLACK_KELVIN = 6000  # Black Screen case's Kelvin setting
# //////////////////////////////////////////////////////////////////////////////////////////////////////////


async def screen():
    num_lights = None
    if len(sys.argv) != 2:
        print("\nDiscovery will go much faster if you provide the number of lights on your LAN:")
        print("  python {} <number of lights on LAN>\n".format(sys.argv[0]))
    else:
        num_lights = int(sys.argv[1])

    # instantiate LifxLAN client, num_lights may be None (unknown).
    # In fact, you don't need to provide LifxLAN with the number of bulbs at all.
    # lifx = LifxLAN() works just as well. Knowing the number of bulbs in advance
    # simply makes initial bulb discovery faster.
    print("Discovering lights...")
    lifx = LifxLAN(num_lights)

    # get devices
    devices = lifx.get_lights()
    bulb = devices[0]
    print("Selected {}".format(bulb.get_label()))

    # get original state
    original_power = bulb.get_power()
    original_color = bulb.get_color()
    bulb.set_power("on")

    sleep(0.2)  # to look pretty

    num = 1

    while num == 1:
        # init counters/accumulators
        red = 0
        green = 0
        blue = 0

        # Crop a chunk of the screen out
        # This is hacky and is currently screen and movie-size specific.
        # To get these values, I take a screenshot and use Paint.Net to easily find the coordinates
        # TODO: clean this up and make it dynamically detect size and crop the black bits out automagically
        left = 0      # The x-offset of where your crop box starts
        top = 140    # The y-offset of where your crop box starts
        width = 1920   # The width  of crop box
        height = 800    # The height of crop box
        box = (left, top, left+width, top+height)

        # take a screenshot
        image = ImageGrab.grab(bbox=box)
        # //////////////////////////////////////////////////////////////////////////////////////////////////////////
        # Left Side of Screen
        # //////////////////////////////////////////////////////////////////////////////////////////////////////////
        for y in range(0, height, DECIMATE):  # loop over the height
            for x in range(0, width, DECIMATE):
                color = image.getpixel((x, y))  # grab a pixel
                # calculate sum of each component (RGB)
                if ((color[0]+color[1]+color[2]) == 0):

                    next
                red = red + color[0]
                green = green + (color[1])
                blue = blue + color[2]

        # calculate the averages
        red = (((red / ((height/DECIMATE) * (width/DECIMATE))))/255.0)
        green = (((green / ((height/DECIMATE) * (width/DECIMATE))))/255.0)
        blue = (((blue / ((height/DECIMATE) * (width/DECIMATE))))/255.0)

        # generate a composite colour from these averages
        c = Color(rgb=(red, green, blue))
        # We create the widgets here

        print(c)
        # print(original_color)

        hue = min(
            (int(round(0x10000 * c.hue*360)/360) % 0x10000), 65535)
        saturation = min(int(round(0xFFFF * c.saturation)), 65535)
        brightness = min(int(round(0xFFFF * c.luminance)), 65535)
        # print(saturation)
        print(c.hue*360, " ", c.saturation, " ", c.luminance)

        # print "\naverage1  red:%s green:%s blue:%s" % (red,green,blue)
        # print "average1   hue:%f saturation:%f luminance:%f" % (c.hue,c.saturation,c.luminance)
        # print "average1  (hex) "+  (c.hex)
        # //////////////////////////////////////////////////////////////////////////////////////////////////////////
        # PROGRAM LIFX BULBS (LEFT)
        # //////////////////////////////////////////////////////////////////////////////////////////////////////////
        if (c.red < BLACK_THRESHOLD) and (c.green < BLACK_THRESHOLD) and (c.blue < BLACK_THRESHOLD):
            # print("black1 detected")
            bulb.set_color([0, 0, BLACK_BRIGHTNESS, BLACK_KELVIN], DURATION)

        else:
            bulb.set_color(
                [hue, saturation, brightness, KELVIN], DURATION, True)

        win.config(bg=c)
        await asyncio.sleep(0.05)

        # //////////////////////////////////////////////////////////////////////////////////////////////////////////
    # restore original color
    # color can be restored after the power is turned off as well
    print("Restoring original color and power...")
    bulb.set_color(original_color)

    sleep(1)  # to look pretty.

    # restore original power
    bulb.set_power(original_power)


win = Tk()  # creating the main window and storing the window object in 'win'
win.attributes('-topmost', True)
Button(win, text="Quit", command=win.destroy).pack()
Button(win, text="Start", command=async_handler(screen)).pack()


win.geometry('200x200')
async_mainloop(win)
