import RPi.GPIO as GPIO
import time
import datetime
import feedparser
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import smbus
import threading

def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text
	
def split_every(n, s):
    return [ s[i:i+n] for i in xrange(0, len(s), n) ]

def clearScreen():
    disp.clear()
    disp.display()

def getWeather(input):
    if input == 0:
        global forecast_title, forecast_desc
        if len(forecast_title) > 0:
            forecast_title = []
            forecast_desc = []
        d = feedparser.parse('http://open.live.bbc.co.uk/weather/feeds/en/ky6/3dayforecast.rss')
        for x, xitem in enumerate(d.entries):
            forecast_title.append(d.entries[x].title.split(","))
            forecast_title[x][0] = forecast_title[x][0].split(":")
            forecast_title[x][1] = forecast_title[x][1].split(":")
            forecast_desc.append(d.entries[x].description.split(","))
            for y, yitem in enumerate(forecast_desc[x]):
                forecast_desc[x][y] = forecast_desc[x][y].split(":")
        #print(forecast_title)
        #print(forecast_desc)


def mainMenu():
    global menuIndex1, menuIndex2, menuBounds1, menuBounds2, runmode, menuList, cancelFlag, selectFlag, runMode
    runmode = 0
    if cancelFlag == 1:
       cancelFlag = 0
    menuList = {0: [showWeather,"Weather"], 1:[setTimer,"Timer"]}
    menuIndex1 = 0
    menuIndex2 = 0
    menuBounds1 = [1,0]
    font = ImageFont.load_default()
    image = Image.new('1', (width, height))
    while selectFlag == 0:
        markery = ((menuIndex1+1) * line_height) + 5
        markerx = 6
        draw = ImageDraw.Draw(image)
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        draw.text((posx, (0 * line_height)), "Select Application", fill=255)
        for x in range(0,len(menuList)):
            draw.text((posx + 10, ((x+1) * line_height)), menuList[x][1], font=font, fill=255)
        draw.ellipse((markerx,markery,markerx+3, markery+3), fill=255)
        print markerx
        print markery
        disp.image(image)
        disp.display()
        EVENT.wait(1200)
        consume_queue()
        EVENT.clear()

def countdown(t):
    global runmode, cancelFlag, font
    runmode = 3
    font = ImageFont.load_default()
    timeNow = datetime.datetime.now()
    remaining = t - timeNow
    startTime = timeNow
    font = ImageFont.load_default()
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    while timeNow < t and cancelFlag == 0:
        timeNow = datetime.datetime.now()
        remaining = t - timeNow
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        draw.text((posx, (0 * line_height)), "Timer Started: " + str(startTime.time()),  font=font, fill=255)
        draw.text((posx, (1 * line_height)), str(remaining),  font=font, fill=255)
        draw.text((posx, (2 * line_height)), "End time: " + str(t.time()),  font=font, fill=255)
        draw.text((posx, (3 * line_height)), "Time now: " + str(timeNow.time()),  font=font, fill=255)
        disp.image(image)
        disp.display()
        consume_queue()
        EVENT.clear()
        time.sleep(0.001)

    clearScreen()
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    draw.text((posx, (0 * line_height)), "Timer Ended",  font=font, fill=255)
    draw.text((posx, (1 * line_height)), "started: " + str(startTime.time()),  font=font, fill=255)
    draw.text((posx, (2 * line_height)), "End: " + str(t.time()),  font=font, fill=255)
    draw.text((posx, (3 * line_height)), "Cancelled: " + str(timeNow.time()),  font=font, fill=255)
    disp.image(image)
    disp.display()
    if cancelFlag == 1:
        cancelFlag = 0
    time.sleep(5)
    setTimer()

def setTimer():
    global runmode, cancelFlag, selectFlag, menuIndex1, menuIndex2, menuBounds1, menuBounds2
    runmode = 2
    selectFlag = 0
    clearScreen()
    tsec = 0
    tmin = 0
    zeroIndex()
    menuBounds1 = [59,0]
    menuBounds2 = [59,0]
    print cancelFlag
    print selectFlag
    while cancelFlag == 0 and selectFlag == 0:
        tsec = menuIndex2
        tmin = menuIndex1
        timeNow = datetime.datetime.now()
        endTime = timeNow + datetime.timedelta(minutes=tmin,seconds=tsec)
        image = Image.new('1', (width, height))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0,0,width,height), outline=0, fill=0)
        draw.text((posx, (0 * line_height)), "Enter Time",  font=font, fill=255)
        draw.text((posx, (1 * line_height)), "Min: " + str(tmin) + " |  Sec: " + str(tsec),  font=font, fill=255)
        draw.text((posx, (2 * line_height)), "End Time:",  font=font, fill=255)
        draw.text((posx, (3 * line_height)), str(endTime.time()),  font=font, fill=255)
        draw.text((posx, (4 * line_height)), "Time Now:",  font=font, fill=255)
        draw.text((posx, (5 * line_height)), str(timeNow.time()),  font=font, fill=255)
        draw = ImageDraw.Draw(image)
        disp.image(image)
        disp.display()
        consume_queue()
        EVENT.clear()
    if cancelFlag == 1:
        cancelFlag = 0
        mainMenu()
    if selectFlag == 1:
        endTime = datetime.datetime.now() + datetime.timedelta(minutes=tmin,seconds=tsec)
        t = endTime
        selectFlag = 0
        countdown(t)


def showWeather():
    getWeather(0)
    EVENT.wait(20)
    EVENT.clear()
    global runmode, menuBounds1, menuBounds2, menuIndex1, menuIndex2, forecast_title, forecast_desc, cancelFlag
    zeroIndex()
    runmode = 1
    font = ImageFont.load_default()
    while cancelFlag == 0:
        if len(forecast_title) > 0:
            menuBounds1 = [2,0]
            menuBounds2 = [len(forecast_desc[menuIndex1])-1,0]
            font = ImageFont.load_default()
            image = Image.new('1', (width, height))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0,0,width,height), outline=0, fill=0)
            draw.text((posx, (0 * line_height)), forecast_title[menuIndex1][0][0],  font=font, fill=255)
            draw.text((posx, (1 * line_height)), forecast_title[menuIndex1][0][1],  font=font, fill=255)
            draw.text((posx, (2 * line_height)), forecast_desc[menuIndex1][menuIndex2][0],  font=font, fill=255)
            draw = ImageDraw.Draw(image)
            if len(forecast_desc[menuIndex1][menuIndex2]) < 3:
                draw.text((posx, (3 * line_height)), forecast_desc[menuIndex1][menuIndex2][1],  font=font, fill=255)
            else:
                draw.text((posx, (3 * line_height)), forecast_desc[menuIndex1][menuIndex2][1] + ":" + forecast_desc[menuIndex1][menuIndex2][2],  font=font, fill=255)
        else:
            font = ImageFont.load_default()
            image = Image.new('1', (width, height))
            draw = ImageDraw.Draw(image)
            draw.rectangle((0,0,width,height), outline=0, fill=0)
            draw.text((posx, (0 * line_height)), "..Feed Updating..",  font=font, fill=255)
        disp.image(image)
        disp.display()
        EVENT.wait(1)
        consume_queue()
        EVENT.clear()
    mainMenu()

def zeroIndex():
    global menuIndex1, menuIndex2
    menuIndex1 = 0
    menuIndex2 = 0


def mcpInterrupt(channel):
    if channel == 24:
        port_capture = bus.read_byte_data(MCP01, 0x10)
    if channel == 25:
        port_capture = bus.read_byte_data(MCP01, 0x11)
    handle_input(channel, port_capture)

def get_bit(x):
    return (x&-x).bit_length()-1

def handle_input(channel, port_capture):
    global port_data_1A
    global port_data_1B
    if channel == 25:
        portDiff = port_capture ^ port_data_1A 
        pinNum = get_bit(portDiff)
        invertedPort = '{:08b}'.format(port_capture)[::-1]
        pinVal = invertedPort[pinNum]
        pinName = "A"+str(pinNum)
        print(pinName)
        print(pinVal)
        instructionQueue.append([pinName,pinVal])
        port_data_1A = port_capture
        EVENT.set()
    if channel == 24:
        portDiff = port_capture ^ port_data_1B
        pinNum = get_bit(portDiff)
        pinVal = bin(port_capture)[pinNum]
        print(pinName)
        print(pinVal)
        instructionQueue.append([pinNum,pinVal])
        port_data_1B = port_capture
        EVENT.set()
    #if channel == INT2A:
        #port_data_2A == port_capture
    #if channel == INT2B:
        #port_data_2A == port_capture

def handle_rotation(channel, rot):
    instructionQueue.append([channel,rot])
    EVENT.set()

def consume_queue():
    while len(instructionQueue) > 0:
      input = instructionQueue.pop(0)
      print("consume queue")
      handle_queue(input)

def handle_queue(input):
    channel = input[0]
    data = input[1]
    input_dispatch = [{22:index1, "A4":index1Select},{22:index1, 17:index2, "A4":getWeather, "A5":cancel},{22:index1, 17:index2, "A4":select, "A5":cancel},{"A5":cancel}]
    if channel in input_dispatch[runmode]:
        f = input_dispatch[runmode].get(channel,"")
        print("handle queue")
        f(data)

def cancel(input):
    global cancelFlag
    if input == "0":
       cancelFlag = 1

def index1(input):
    global menuIndex1, menuBounds1
    if (menuIndex1 + input) < (menuBounds1[0]) and (menuIndex1 + input) > (menuBounds1[1] - 1):
        menuIndex1 = menuIndex1 + input
    elif menuIndex1 + input < menuBounds1[1]:
        menuIndex1 = menuBounds1[1]
    else:
        menuIndex1 = menuBounds1[0]
    print("index: ")
    print menuIndex1
    print("bounds:")
    print menuBounds1

def select(input):
    if input == "0":
       global selectFlag
       selectFlag = 1

def index1Select(input):
    if input == "0":
       global menuList, menuIndex1
       f = menuList[menuIndex1][0]
       f()
        
def index2(input):
    global menuIndex2, menuBounds2
    if (menuIndex2 + input) < (menuBounds2[0]) and (menuIndex2 + input) > (menuBounds2[1] - 1):
        menuIndex2 = menuIndex2 + input
    elif menuIndex2 + input < menuBounds2[1]:
        menuIndex2 = menuBounds2[1]
    else:
        menuIndex2 = menuBounds2[0]

def index2Select(input):
    if input == "0":
       global menuList, menuIndex2
       f = menuList[menuIndex2][0]
       f()    

class RotaryEncoder:
    def __init__(self, Enc_A, Enc_B, callback=None):
        self.Enc_A = Enc_A
        self.Enc_B = Enc_B
        GPIO.setwarnings(True)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.Enc_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.Enc_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.Enc_A, GPIO.FALLING, callback=self.rotation_decode, bouncetime=2)
        self.callback = callback
        return


    def rotation_decode(self, channel):
        GPIO.setmode(GPIO.BCM)
        Switch_A = GPIO.input(self.Enc_A)
        Switch_B = GPIO.input(self.Enc_B)

        if (Switch_A == 0) and (Switch_B == 1) : # A then B ->
            self.callback(channel, 1)
            print "direction -> "
            # wait for B high
            while Switch_B == 1:
                Switch_B = GPIO.input(self.Enc_B)
            # wait for B drop
            while Switch_B == 0:
                Switch_B = GPIO.input(self.Enc_B)
            return

        elif (Switch_A == 0) and (Switch_B == 0): # B then A <-
            self.callback(channel, -1)
            print "direction <- "
             # wait for A drop
            while Switch_A == 0:
                Switch_A = GPIO.input(self.Enc_A)
            return

        else: # reject other combo
            return




#init encoder
GPIO.setmode(GPIO.BCM)
left_encoder = RotaryEncoder(22, 23, callback=handle_rotation)
right_encoder = RotaryEncoder(17, 18, callback=handle_rotation)
#init oled
RST = None
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)
disp.begin()
disp.clear()
disp.display()
posx = int(2)
font = ImageFont.load_default()
width = disp.width
height = disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline=0, fill=0)
line_height = 8
top = 0
#init mcp23017
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(25, GPIO.IN, pull_up_down=GPIO.PUD_UP)
MCP01 = 0x20
MCP02 = 0x21
global port_capture
port_capture = None
global port_data_1A
global port_data_1B
global port_data_2A
global port_data_2B
bus = smbus.SMBus(1)
bus.write_byte_data(MCP01, 0x00, 0xFF)
bus.write_byte_data(MCP01, 0x01, 0xFF)
bus.write_byte_data(MCP01, 0x0c, 0xFF)
bus.write_byte_data(MCP01, 0x0d, 0xFF)
bus.write_byte_data(MCP01, 0x04, 0xFF)
bus.write_byte_data(MCP01, 0x05, 0xFF)
bus.write_byte_data(MCP01, 0x0a, 0x5)
bus.write_byte_data(MCP01, 0x0b, 0x5)
port_data_1A = bus.read_byte_data(MCP01, 0x12)
port_data_1B = bus.read_byte_data(MCP01, 0x13)
GPIO.add_event_detect(24, GPIO.FALLING, callback=mcpInterrupt)
GPIO.add_event_detect(25, GPIO.FALLING, callback=mcpInterrupt)
#init weather array
forecast_title = []
forecast_desc = []
#init menu
global cancelFlag, selectFlag, runMode, menuIndex1, menuIndex2, menuBounds1, menuBounds2, instructionQueue, menuList
cancelFlag = 0
selectFlag = 0
menuList = {}
menuIndex1 = 0
menuIndex2 = 0
menuBounds1 = [0,0]
menuBounds2 = [0,0]
instructionQueue = []
EVENT = threading.Event()


try:
    getWeather(0)
    mainMenu()
    while true:
        EVENT.wait(1200)
        consume_queue()
        EVENT.clear()

except KeyboardInterrupt: # Ctrl-C to terminate the program
        GPIO.cleanup()
        disp.clear()
        disp.display()

finally:
        GPIO.cleanup()
        disp.clear()
        disp.display()
