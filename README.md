<img src="https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg">

# lifxscreen2
LIFX Movie experience. 
Continuously calculates the average colour of your screen and sets your LIFX bulb(s) to that color.

Watch movies *(or anything you want on your screen)* in style. Like [THIS!](https://youtu.be/WHCtUvEJXq0)

(*seeks to improve over the original lifxscreen at https://github.com/frakman1/lifxscreen*)

- This version uses the much faster LAN protocol 
- Crops the screen so as not to take the black portion into account when calculating the average colour. 
- Better black screen colour handling. 


Tested on a Windows-7, 64bit machine. Python version 2.7.5. 

## Prerequisites:

* colour - Colour Convertions and Manipulations  (https://pypi.python.org/pypi/colour/)

* bitstring-3.1.9


## Syntax:

```
python lifxscreen2.py
```
...trivial change
