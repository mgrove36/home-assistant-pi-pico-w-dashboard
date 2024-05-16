from machine import reset
from network import WLAN, STA_IF
from time import sleep, localtime
from lcd import LCD
from font import cntr_st
from gc import collect, mem_free
from env import HOSTNAME, SSID, WIFI_PASSWORD, SCREENS
from _thread import start_new_thread
from ntptime import settime
from screens import *

class App:
    def __init__(self) -> None:
        if (len(SCREENS) == 0):
            print("No screens configured. Check env.py.")
            self.scr_n = -1
        else: self.scr_n = 0
        self.lcd = LCD()
    
    def __connect(self) -> int:
        wlan = WLAN(STA_IF)
        wlan.active(True)
        wlan.config(hostname=HOSTNAME)
        wlan.connect(SSID, WIFI_PASSWORD)
        while wlan.isconnected() == False:
            print('Waiting for connection...')
            sleep(1)
        self.ip = wlan.ifconfig()[0]
        print(f'Connected on {self.ip}')
        return self.ip

    def __boot(self) -> None:
        collect()
        print("Booting")
        self.lcd.fill(0x0000)
        cntr_st(self.lcd, self.lcd.width, "Booting...", 120, 2, 150, 150, 150)
        self.lcd.show()
        self.__connect()
        try:
            settime()
            print("Local time after synchronization: %s" %str(localtime()))
        except:
            pass

    def __resetButtonStatuses(self) -> None:
        self.lcd.keyA["v"] = False
        self.lcd.keyB["v"] = False
        self.lcd.keyX["v"] = False
        self.lcd.keyY["v"] = False
        self.lcd.left["v"] = False
        self.lcd.right["v"] = False
        self.lcd.up["v"] = False
        self.lcd.down["v"] = False
        self.lcd.ctrl["v"] = False

    def __manageButtons(self) -> None:
        while (True):
            a = False
            if (self.lcd.keyA["p"].value() == 0):
                self.lcd.keyA["v"] = True
                a = True
            if (self.lcd.keyB["p"].value() == 0):
                self.lcd.keyB["v"] = True
                a = True
            if (self.lcd.keyX["p"].value() == 0):
                self.lcd.keyX["v"] = True
                a = True
            if (self.lcd.keyY["p"].value() == 0):
                self.lcd.keyY["v"] = True
                a = True
            if (self.lcd.right["p"].value() == 0):
                self.lcd.right["v"] = True
                a = True
            if (self.lcd.left["p"].value() == 0):
                self.lcd.left["v"] = True
                a = True
            if (self.lcd.up["p"].value() == 0):
                self.lcd.up["v"] = True
                a = True
            if (self.lcd.down["p"].value() == 0):
                self.lcd.down["v"] = True
                a = True
            if (self.lcd.ctrl["p"].value() == 0):
                self.lcd.ctrl["v"] = True
                a = True
            if (a):
                sleep(0.2)
    
    def __changeScreen(self) -> bool:
        c = False
        if (self.lcd.right["v"]):
            c = True
            if (self.scr_n == len(SCREENS) - 1):
                self.scr_n = 0
            else:
                self.scr_n += 1
        elif (self.lcd.left["v"]):
            c = True
            if (self.scr_n == 0):
                self.scr_n = len(SCREENS) - 1
            else:
                self.scr_n -= 1
        self.lcd.left["v"] = False
        self.lcd.right["v"] = False
        return c

    def handleButtons(self) -> bool:
        up = self.lcd.up["v"]
        down = self.lcd.down["v"]
        left = self.lcd.left["v"]
        right = self.lcd.right["v"]
        ctrl = self.lcd.ctrl["v"]
        keyA = self.lcd.keyA["v"]
        keyB = self.lcd.keyB["v"]
        keyX = self.lcd.keyX["v"]
        keyY = self.lcd.keyY["v"]
        self.__resetButtonStatuses()
        if (ctrl):
            reset()
        return self.s.handleButtons(up, down, left, right, keyA, keyB, keyX, keyY, ctrl)

    def __manageScreen(self) -> None:
        started = False
        while (True):
            print("Mem free before and after collecting:")
            print(mem_free())
            collect()
            print(mem_free())
            if (localtime()[3] == 0):
                try:
                    settime()
                except:
                    pass
            changed = not started or self.__changeScreen()
            if (not started): started = True
            # if the screen has changed, redraw the whole screen
            if (changed):
                self.__resetButtonStatuses()
                collect()
                if (SCREENS[self.scr_n]["type"] == 0):
                    self.s = LightsScreen(SCREENS[self.scr_n]["name"], SCREENS[self.scr_n]["entities"])
                elif (SCREENS[self.scr_n]["type"] == 1):
                    self.s = MediaScreen(SCREENS[self.scr_n]["name"], SCREENS[self.scr_n]["entity"])
                else:
                    self.s = UnknownScreen("Unknown")
                self.s.display(self.lcd)
            # otherwise minimise the number of pixels being changed
            else:
                b = self.handleButtons()
                if (b): continue
                self.s.update(self.lcd)

    def run(self) -> None:
        if (self.scr_n == None): return
        self.__boot()
        try:
            start_new_thread(self.__manageButtons, ())
            self.__manageScreen()
        except KeyboardInterrupt:
            reset()
