import socket
from rpi_ws281x import PixelStrip, Color, ws
import threading
import time
import math
from runOnServerStart import startScript

# server vars
PORT = 1337
SERVER = None # will be defined later
ADDR = None # will be defined later
DISCONNECT_MESSAGE = b"DISCONNECT"
KEEPALIVE_MESSAGE = b"KEEPALIVE"
DEFAULT_BUFFER_SIZE = 128

# LED vars
LED_COUNT = 30
LED_PIN = 18
LED_FREQ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255
LED_INVERT = False
LED_CHANNEL = 0
LED_STRIP = ws.SK6812W_STRIP

# get device local IP
tempSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tempSock.connect(("1.1.1.1", 80)) # doesn't need to be able to connect, just needs to think it can. can be any non-loopback IP
SERVER = tempSock.getsockname()[0]
print(f"Device IP is {SERVER}")
ADDR = (SERVER, PORT)

# server init
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
server.bind(ADDR)

# LED init
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
strip.begin()

def decodeAndApplyCommand(command):
    # command must be a bytes object

    # check header integrity
    if int(command[:24].hex(), 16):
        return 1 # error code 1 (incorrect header)

    # as this function does not handle headers, discard it
    command = command[24:]

    # the first ceil(LED_COUNT/8) bytes are writeMask bytes, so extract them
    writeMaskByteCount = math.ceil(LED_COUNT/8)
    writeMaskBytes = command[:writeMaskByteCount]
    command = command[writeMaskByteCount:] # remove writeMask from command
    writeMaskStr = bin(int(writeMaskBytes.hex(), 16)).lstrip("0b")

    # find expected length of message
    numOfExpectedColourDatapoints = writeMaskStr.count("1")

    # check length of message
    if len(command)/4 < numOfExpectedColourDatapoints:
        return 3 # error code 3 (message is too short)
    elif len(command)/4 > numOfExpectedColourDatapoints:
        return 2 # error code 2 (message is too long)

    # loop over the remaining bytes, extracting in groups of 4 and applying
    colourDataReadPoint = 0
    for i in range(0, LED_COUNT):
        if int(writeMaskStr[i]):
            #print(command[4*colourDataReadPoint:4*(colourDataReadPoint+1)].hex())
            strip.setPixelColor(i, int(command[4*colourDataReadPoint:4*(colourDataReadPoint+1)].hex(), 16))
            colourDataReadPoint += 1

    # apply changes to strip
    strip.show()

    # return 0 for success I guess?
    time.sleep(0.001)
    return 0

def handle_client(conn, addr): # to be run in a seperate thread for every connection
    bufferSize = DEFAULT_BUFFER_SIZE

    # send client number of LEDs connected
    conn.send(LED_COUNT.to_bytes(2, byteorder="big"))
    print(f"Informed client {addr} of LED count {LED_COUNT}")

    # client's first message must define buffer size
    while True:
        bufferSizeExchange = conn.recv(bufferSize)
        if len(bufferSizeExchange) != 0:
            bufferSize = int.from_bytes(bufferSizeExchange, byteorder="big")
            print(f"Client {addr} has set buffer size to {bufferSize}")

            # confirm buffer size to client
            conn.send(bufferSize.to_bytes(2, byteorder="big"))

            break

    # start timeout by taking current time
    lastMessageTime = time.time()

    # listen for client commands
    while True:
        skipExec = False
        conn.settimeout(15)
        try:
            command = conn.recv(bufferSize)
        except socket.timeout:
            command = "" # set command to be empty so the if statement skips and we just wait again
        except ConnectionResetError:
            # I have absolutely no clue why but sometimes when I stop a client program it throws this error in the server
            # so I'm just catching it and calling it "disconnecting ungracefully" because that sounds like I know what
            # I'm doing
            print(f"Client {addr} has disconnected ungracefully")
            break

        if len(command) != 0:
            # reset timeout
            lastMessageTime = time.time()

            # test if the message is a disconnect message
            if command.startswith(DISCONNECT_MESSAGE):
                print(f"Client {addr} has disconnected gracefully")
                break # exit completely, allowing function to end

            # test if the message is a keepAlive
            if command.startswith(KEEPALIVE_MESSAGE):
                skipExec = True # skip the current exec and wait again for an actual command

            if not skipExec:
                try:
                    # sends the error codes in the function to the client, currently unused
                    conn.send(decodeAndApplyCommand(command).to_bytes(1, byteorder="big"))
                except:
                    print(f"Failed to parse in connection to {addr}")
                    conn.send((4).to_bytes(1, byteorder="big")) # error codes, currently unused

        else:
            if time.time() - lastMessageTime >= 30:
                print(f"Client {addr} has timed out")
                break
            time.sleep(0.001)


def start():
    hasStarted.set()
    server.listen(5)
    while True:
        conn, addr = server.accept()
        # server.accept() is blocking, so spin off a thread to handle the new connection
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"{threading.activeCount() - 1} active connections")

def runStartupScript():
    hasStarted.wait() # wait for the server to finish starting
    startScript() # run init script

print("Server Starting")
hasStarted = threading.Event()
threading.Thread(target=runStartupScript) # run startup script in seperate thread that waits for the server to start
start()
