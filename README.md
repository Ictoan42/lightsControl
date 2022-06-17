# Network LED Strip Control for Raspberry Pi

A Python implementation of a server and client for controlling addressable SK6812 LED strips

## Usage

---

### Dependencies

[rpi-ws281x-python](https://github.com/rpi-ws281x/rpi-ws281x-python) is required on the Pi running the server.

---

### Hardware Setup

- Runs on any model of RasPi
- Requires a 5V power supply for the strip
- Connect pins correctly:
    1. Power supply ground to strip ground
    2. Pi ground to strip ground
    3. Power supply +5v to strip +5v
    4. Pi GPIO18 to strip data in

---

### Software Setup

Place the `server.py` file in any folder on the Pi, and place `runOnServerStart.py` and `networkLightControlClient.py` in the same directory. Place `lightStripServer.service` in `/etc/systemd/system/` and in the file, change `PATH_TO_SERVER.PY` on line 9 to the path to where you put `server.py`. To start or stop the server, run `sudo systemctl start lightStripServer.service` or `sudo systemctl stop lightStripServer.service`, respectively. To set the server to run on startup, run `sudo systemctl enable lightStripServer.service`.

---

### Client API Usage

To import, simply import networkControlledStrip from networkLightControlClient. networkLightControlClient.py must be in the same directory as the program.

`from networkLightControlClient import networkControlledStrip`

#### Initialisation

Initalise a connection to the server by initialising a `networkControlledStrip` object

`strip = networkControlledStrip(ip, port)`

**Parameters:**

- `ip`: String - The IP to connect to
- `port`: Integer - The port to connect to, defaults to 1337

**Returns:**

- Nothing

**Throws:**

- If a connection to the server cannot be established, the network exception is thrown.

#### Method `setPixelColour(LED_ID, w, r, g, b)`

Sets the specified LED to the specified colour. This function does not take effect immediately, it stores changes to the strip which are then pushed with `send()`.

**Parameters:**

- `LED_ID`: Integer - The ID of the LED to set the colour of. Counts from 0, starts at the start of the strip and enumerates.
- `w`: Integer - The brightness to set the white channel to. Accepts values 0-255 inclusive.
- `r`: Integer - The brightness to set the red channel to. Accepts values 0-255 inclusive.
- `g`: Integer - The brightness to set the green channel to. Accepts values 0-255 inclusive.
- `b`: Integer - The brightness to set the blue channel to. Accepts values 0-255 inclusive.

**Returns:**

- `0` If the operation was successful.
- `-1` If the operation failed.

#### Method `setAllPixels(w, r, g, b)`

Sets all LEDs in the strip to the specified colour. This function also does not take effect immediately, rather buffering it's changes to be sent in one go with `send()`.

**Parameters:**

- `w`: Integer - The brightness to set the white channel to. Accepts values 0-255 inclusive.
- `r`: Integer - The brightness to set the red channel to. Accepts values 0-255 inclusive.
- `g`: Integer - The brightness to set the green channel to. Accepts values 0-255 inclusive.
- `b`: Integer - The brightness to set the blue channel to. Accepts values 0-255 inclusive.

**Returns:**

- Nothing.

#### Method `send()`

Sends all buffered changes to the server in a single message.

**Parameters:**

- None.

**Returns:**

- `0` If the operation was successful.
- `-1` If the operation failed due to Timeout, Connection Reset or Broken Pipe.

**Throws:**

- If any other exception is thrown by attempting to send the message, that exception is not handled

#### Method `disconnect()`

Disconnects from the server. If the disconnect message fails to get to the server due to Connection Reset or Broken Pipe, the exception is caught and treated as a disconnection anyway.

**Parameters:**

- None.

**Returns:**

- Nothing.

**Throws:**

- If the message fails to reach the server for a reason other than Connection Reset or Broken Pipe.

### Property `LED_COUNT`

A property of the `networkControlledStrip` object that represents the number of LEDs in the strip.

Example, set every other LED to red:

    for i in range(strip.LED_COUNT):
        if i%2 == 0:
            strip.setPixelColour(i, 0, 255, 0, 0)
    strip.send()