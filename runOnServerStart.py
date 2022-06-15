from networkLightControlClient import networkControlledStrip

# a simple wipe across the strip, this program is set by default to run when the server starts

def startScript():
    strip = networkControlledStrip("127.0.0.1")

    lightsArr = [0]*strip.LED_COUNT

    for i in lightsArr:
        i = [0,0,0,0]

    for i in range(strip.LED_COUNT*2):
        
        # decrement everything for fading trail
        for j in lightsArr:
            for k in j:
                k = max(0, k-16)
        
        lightsArr[i][1] = 255
        lightsArr[i][3] = 127

        for j in lightsArr:
            strip.setPixelColour(i, lightsArr[i][0], lightsArr[i][1], lightsArr[i][2], lightsArr[i][3])
        
        strip.send()