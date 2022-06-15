from networkLightControlClient import networkControlledStrip
import time
import socket

# a simple wipe across the strip, this program is set by default to run when the server starts

def startScript():
    strip = networkControlledStrip(socket.gethostname())

    for i in range(strip.LED_COUNT):

        strip.setAllPixels(0, 0, 0, 0)
        strip.setPixelColour(i, 0, 255, 0, 127)
        strip.send()

        time.sleep(0.03)
    
    strip.setAllPixels(0, 0, 0, 0)
    strip.disconnect()