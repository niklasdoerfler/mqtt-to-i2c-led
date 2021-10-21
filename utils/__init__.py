def logarithmic_fade(x, rx = 1, ry = 1, b = 3):
    '''Apply a exponential function to the given decimal value x to get a smooth light fade adjusted to the human eye logarithmic characteristic.

    Constants 
    - rx, ry define the range for x and y
    - b defines the exponential base
    '''

    y = ry * (b**(x/rx) - 1) / (b-1) 
    return y
    