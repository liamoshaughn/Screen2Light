from time import sleep
from PIL import ImageGrab
from lifxlan import LifxLAN
from lifxlan.msgtypes import GetLabel, StateLabel
from colour import Color
import sys
import math
import binascii
from tkinter import *
import asyncio
import pyautogui
import numpy as np
from async_tkinter_loop import async_handler, async_mainloop

# //////////////////////////////////////////////////////////////////////////////////////////////////////////
# GLOBAL DEFINES
# //////////////////////////////////////////////////////////////////////////////////////////////////////////
KELVIN = 8000  # 2000 to 8000, where 2000 is the warmest and 8000 is the coolest
DECIMATE = 10  # skip every DECIMATE number of pixels to speed up calculation
DURATION = 1000  # The time over which to change the colour of the lights in ms. Use 100 for faster transitions
BLACK_THRESHOLD = 0.2  # Black Screen Detection Threshold
# Black Screen case's brightness setting
BLACK_BRIGHTNESS = int(round(0x10000 * 0.03 * 360) / 360) % 0x10000
BLACK_KELVIN = 6000  # Black Screen case's Kelvin setting
# //////////////////////////////////////////////////////////////////////////////////////////////////////////


MAX_RETRY_ATTEMPTS = 10
RETRY_DELAY_SECONDS = 5

MAX_DISCOVERY_RETRIES = 5
DISCOVERY_RETRY_DELAY_SECONDS = 5


# ... (rest of your constants and global variables)
def find_average_colors(image):
    red, green, blue = 0, 0, 0
    for y in range(0, image.height, DECIMATE):
        for x in range(0, image.width, DECIMATE):
            color = image.getpixel((x, y))
            if sum(color) == 0:
                continue
            red += color[0]
            green += color[1]
            blue += color[2]

    # calculate the averages
    total_pixels = (image.height // DECIMATE) * (image.width // DECIMATE)
    red_average = red / total_pixels
    green_average = green / total_pixels
    blue_average = blue / total_pixels

    # clamp values to [0, 1]
    red_average = min(red_average / 255.0, 1.0)
    green_average = min(green_average / 255.0, 1.0)
    blue_average = min(blue_average / 255.0, 1.0)

    # generate a composite colour from these averages
    c = Color(rgb=(red_average, green_average, blue_average))


async def find_vibrant_colors(image, bulb):
    pixel_colors = {}

    for y in range(0, image.height, DECIMATE):
        for x in range(0, image.width, DECIMATE):
            # Get the RGB color of the pixel
            color = image.getpixel((x, y))
            if sum(color) == 0:
                continue
            red = color[0]
            green = color[1]
            blue = color[2]

            # Convert RGB to HSV (Hue, Saturation, Value) color space using the colour module
            color = Color(rgb=(red / 255, green / 255, blue / 255))
            if (color.get_luminance() > 0.8) or (color.get_luminance() < 0.15):
                continue

            # Store the pixel color and its saturation and brightness in the dictionary
            pixel_colors[(red, green, blue)] = (
                color.saturation,
                color.luminance,
                color.hue,
            )

    # Sort the pixel colors based on their occurrence frequency
    sorted_colors = sorted(pixel_colors.items(), key=lambda item: item[1], reverse=True)

    # Exclude colors that are too similar to each other
    final_colors = []
    for color, (saturation, luminance, hue) in sorted_colors:
        exclude_color = False
        for final_color in final_colors:
            # Calculate the difference in saturation and luminance
            saturation_diff = abs(final_color[1][0] - saturation)
            luminance_diff = abs(final_color[1][1] - luminance)
            if saturation_diff < 0.1 and luminance_diff < 0.1:
                exclude_color = True
                break
        if not exclude_color:
            final_colors.append((color, (saturation, luminance, hue)))

        # Break the loop when we have found 4 colors
        if len(final_colors) == 4:
            break

    hex_values = [
        Color(rgb=(r / 255.0, g / 255.0, b / 255.0)).hex
        for (r, g, b), _ in final_colors
    ]
    print(hex_values)
    for c in final_colors:
        # We create the widgets here

        red, green, blue = c[0]

        # Extract the saturation and luminance values from the second element of the tuple
        saturation, luminance, hue = c[1]
        setLight(red, green, blue, hue, saturation, luminance, bulb, False)
        await asyncio.sleep(5)


def setLight(red, green, blue, hue, saturation, luminance, bulb, fast):
    hue = min(int(round(0x10000 * hue * 360) / 360) % 0x10000, 65535)
    saturation = min(int(round(0xFFFF * saturation)), 65535)
    brightness = min(int(round(0xFFFF * luminance)), 65535)

    if (
        (red < BLACK_THRESHOLD)
        and (green < BLACK_THRESHOLD)
        and (blue < BLACK_THRESHOLD)
    ):
        # print("black1 detected")
        bulb.set_color([0, 0, BLACK_BRIGHTNESS, BLACK_KELVIN], DURATION, fast)

    else:
        bulb.set_color([hue, saturation, brightness, KELVIN], DURATION, fast)

    win.config(bg="#%02x%02x%02x" % c[0])


async def discover_lights():
    num_retries = 0
    while num_retries < MAX_DISCOVERY_RETRIES:
        try:
            lifx = LifxLAN()
            # get devices
            devices = lifx.get_lights()
            # Filter out bulbs with no label (name)
            devices_with_label = [device for device in devices if device.get_label()]
            if devices_with_label:
                return devices_with_label[
                    0
                ]  # Return the first discovered bulb with a label
        except Exception as e:
            print("Error during light discovery: {}. Retrying...".format(e))
            num_retries += 1
            await asyncio.sleep(DISCOVERY_RETRY_DELAY_SECONDS)

    print("Max discovery retries reached or no lights with labels found. Exiting.")
    return None


async def screen():
    if len(sys.argv) != 2:
        print(
            "\nDiscovery will go much faster if you provide the number of lights on your LAN:"
        )
        print("  python {} <number of lights on LAN>\n".format(sys.argv[0]))
    else:
        num_lights = int(sys.argv[1])

    # instantiate LifxLAN client, num_lights may be None (unknown).
    # In fact, you don't need to provide LifxLAN with the number of bulbs at all.
    # lifx = LifxLAN() works just as well. Knowing the number of bulbs in advance
    # simply makes initial bulb discovery faster.
    print("Discovering lights...")
    # Discover lights and initialize bulb
    bulb = await discover_lights()

    if not bulb:
        print("No lights found. Exiting.")
        return

    # Check if the bulb has a label
    try:
        label_response = bulb.req_with_resp(GetLabel, StateLabel)
        print("Selected bulb label: {}".format(label_response.label))
    except Exception as e:
        print("Error occurred while retrieving label: {}".format(e))
        return

    print("Selected bulb label: {}".format(bulb.get_label()))

    # get original state
    original_power = bulb.get_power()
    original_color = bulb.get_color()
    bulb.set_power("on")

    sleep(0.2)  # to look pretty

    # Main retry loop for screen processing
    num_retries = 0
    while num_retries < MAX_RETRY_ATTEMPTS:
        try:
            # init counters/accumulators

            # Just take the middle 15% of the screen
            screen_width, screen_height = pyautogui.size()

            crop_height = int(screen_height * 0.15)

            # Crop a chunk of the screen out
            # This is hacky and is currently screen and movie-size specific.
            # To get these values, I take a screenshot and use Paint.Net to easily find the coordinates
            left = 0
            top = (screen_height - crop_height) // 2
            width = screen_width
            height = crop_height
            box = (left, top, left + width, top + height)

            # take a screenshot
            # bbox=box
            image = ImageGrab.grab()

            await find_vibrant_colors(image, bulb)

        except Exception as e:
            print("Error occurred: {}. Retrying...".e)
            num_retries += 1
            await asyncio.sleep(RETRY_DELAY_SECONDS)

    if num_retries >= MAX_RETRY_ATTEMPTS:
        print("Max retry attempts reached. Aborting.")

        # //////////////////////////////////////////////////////////////////////////////////////////////////////////
    # restore original color
    # color can be restored after the power is turned off as well
    print("Restoring original color and power...")
    bulb.set_color(original_color)

    sleep(1)  # to look pretty.

    # restore original power
    bulb.set_power(original_power)


win = Tk()  # creating the main window and storing the window object in 'win'
win.attributes("-topmost", True)
Button(win, text="Quit", command=win.destroy).pack()
Button(win, text="Start", command=async_handler(screen)).pack()

win.geometry("200x200")
async_mainloop(win)
