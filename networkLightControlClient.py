import socket
import math
import time
import threading


class networkControlledStrip:
    def __init__(self, ip:str, port:int=1337):
        # connect to the strip and init arrays

        # networking vars
        self.__DISCONNECT_MESSAGE = b"DISCONNECT"
        self.__DESIRED_BUFFER_SIZE = 2048
        self.__KEEPALIVE_MSG = b"KEEPALIVE"

        # init socket
        self.__s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.__s.connect((ip, port))
        except Exception as e:
            print(f"Failed to connect to socket at {ip}:{port}")
            print(e)
            return -1
        
        # listen for LED count message from the server
        knowLEDCount = False
        while not knowLEDCount:
            LEDCountMessage = self.__s.recv(128)
            if len(LEDCountMessage) != 0:
                LEDCountInt = int.from_bytes(LEDCountMessage, byteorder="big")
                knowLEDCount = True
                self.LED_COUNT = LEDCountInt
        
        # send desired buffer size to server
        self.__s.send(self.__DESIRED_BUFFER_SIZE.to_bytes(2, byteorder="big"))

        # listen for server confirmation of buffer size
        bufferSizeConfirmed = False
        while not bufferSizeConfirmed:
            bufferSizeConfirmationMessage = self.__s.recv(128)
            if len(bufferSizeConfirmationMessage) != 0:
                if int.from_bytes(bufferSizeConfirmationMessage, byteorder="big") == self.__DESIRED_BUFFER_SIZE:
                    bufferSizeConfirmed = True
                else:
                    print("Server failed to confirm buffer size")
                    return -1
        
        # initialise write mask as array of length LEDCount full of Falses
        self.__write_mask = [False] * self.LED_COUNT

        # initialise colour data as array of length LEDCount full of arrays of length 4 full of 0s
        self.__colour_data = [0] * self.LED_COUNT
        for i in range(0, self.LED_COUNT):
            self.__colour_data[i] = [0,0,0,0]

        # start keepAlive thread
        self.__connectionTerminating = False
        self.__keepAlive = threading.Thread(target=self.keepAlive)
        self.__keepAlive.start()

        # wait a moment to avoid messages getting overlapped because sockets are DUMB
        time.sleep(0.5)

    def keepAlive(self):
        # send a keepAlive message to the server every 15(ish) seconds
        # this method is run in a seperate thread
        while True:
            for i in range(0, 30):
                # check if thread has been told to stop every 0.5s so overall connection shutdown can be faster without a race condition
                if self.__connectionTerminating:
                    break
                time.sleep(0.5)
            self.__s.send(self.__KEEPALIVE_MSG)

    def disconnect(self):
        # disconnect from the server

        # shut down keepAlive thread


        self.__s.send(self.__DISCONNECT_MESSAGE)
    
    def setAllPixels(self, w:int, r:int, g:int, b:int):
        # set every pixel value to the set colour

        self.__write_mask = [True] * self.LED_COUNT

        for i in range(0, self.LED_COUNT):
            self.__colour_data[i] = [w, r, g, b]
    
    def setPixelColour(self, LEDID:int, w:int, r:int, g:int, b:int):
        # alter internal arrays to reflect changed colour

        # do a bunch of checks
        if LEDID < 0 or LEDID > self.LED_COUNT:
            print(f"Invalid LED ID of {LEDID}")
            return -1
        elif w < 0 or w > 255:
            print(f"Invalid white value of {w}")
            return -1
        elif r < 0 or r > 255:
            print(f"Invalid red value of {r}")
            return -1
        elif g < 0 or g > 255:
            print(f"Invalid green value of {g}")
            return -1
        elif b < 0 or b > 255:
            print(f"Invalid blue value of {b}")
            return -1

        self.__write_mask[LEDID] = True

        self.__colour_data[LEDID] = [w, r, g, b]

        return 0

    def send(self):
        # send accumulated changes over the network as a command
        
        messageToSend = bytearray(24)

        binaryStringToConvertToWriteMask = ""
        for i in range(0, self.LED_COUNT):
            if self.__write_mask[i]:
                binaryStringToConvertToWriteMask += "1"
            else:
                binaryStringToConvertToWriteMask += "0"
        writeMaskInt = int(binaryStringToConvertToWriteMask, 2)
        writeMaskBytes = writeMaskInt.to_bytes(math.ceil(self.LED_COUNT/8), byteorder="big")

        messageToSend += writeMaskBytes

        colourDataByteArray = bytearray(0) # init empty to append to
        for i in range(0, self.LED_COUNT):
            if self.__write_mask[i]:
                colourDataByteArray += self.__colour_data[i][0].to_bytes(1, byteorder="big")
                colourDataByteArray += self.__colour_data[i][1].to_bytes(1, byteorder="big")
                colourDataByteArray += self.__colour_data[i][2].to_bytes(1, byteorder="big")
                colourDataByteArray += self.__colour_data[i][3].to_bytes(1, byteorder="big")
        
        messageToSend += colourDataByteArray

        # now that we're done reading them, clear the data arrays for next time
        self.__write_mask = [False] * self.LED_COUNT
        self.__colour_data = [0] * self.LED_COUNT
        for i in range(0, self.LED_COUNT):
            self.__colour_data[i] = [0,0,0,0]

        # send to socket
        try:
            self.__s.send(messageToSend)
        except:
            print("Failed to send message to socket!")
            return -1
        
        return 0