from machine import reset
from network import WLAN, STA_IF
from time import sleep, localtime, time
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
        self.last_cng = 0
        self.must_draw = False
    
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
        if (self.lcd.keyA["v"]): self.lcd.keyA["v"] = False
        if (self.lcd.keyB["v"]): self.lcd.keyB["v"] = False
        if (self.lcd.keyX["v"]): self.lcd.keyX["v"] = False
        if (self.lcd.keyY["v"]): self.lcd.keyY["v"] = False
        if (self.lcd.left["v"]): self.lcd.left["v"] = False
        if (self.lcd.right["v"]): self.lcd.right["v"] = False
        if (self.lcd.up["v"]): self.lcd.up["v"] = False
        if (self.lcd.down["v"]): self.lcd.down["v"] = False
        if (self.lcd.ctrl["v"]): self.lcd.ctrl["v"] = False

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
        if (c): self.last_cng = time()
        return c

    def handleButtons(self, o: bool = True) -> bool:
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
        a = up or down or left or right or keyA or keyB or keyX or keyY or ctrl
        if (a): self.last_cng = time()
        if (o):
            c = self.s.handleButtons(up, down, left, right, keyA, keyB, keyX, keyY, ctrl)
            return c
        return a

    def __manageScreen(self) -> None:
        started = False
        active = True
        self.last_cng = time()
        while (True):
            collect()
            if (localtime()[3] == 0):
                try:
                    settime()
                except:
                    pass
            if (active and time() - self.last_cng > 15):
                LCD.setDuty(0)
                active = False
            elif (active):
                if (self.lcd.ctrl["v"]):
                    LCD.setDuty(0)
                    active = False
                    self.lcd.ctrl["v"] = False
                    continue
                changed = not started or self.__changeScreen()
                # if the screen has changed, redraw the whole screen
                if (changed):
                    self.last_cng = time()
                    if (not started): started = True
                    self.__resetButtonStatuses()
                    collect()
                    if (SCREENS[self.scr_n]["type"] == 0):
                        self.s = LightsScreen(SCREENS[self.scr_n]["name"], SCREENS[self.scr_n]["entities"])
                    elif (SCREENS[self.scr_n]["type"] == 1):
                        self.s = MediaScreen(SCREENS[self.scr_n]["name"], SCREENS[self.scr_n]["entity"])
                    else:
                        self.s = UnknownScreen("Unknown")
                    self.must_draw = self.s.display(self.lcd)
                # otherwise minimise the number of pixels being changed
                else:
                    b = self.handleButtons()
                    if (b):
                        self.last_cng = time()
                        continue
                    if (self.must_draw):
                        self.must_draw = self.s.display(self.lcd)
                    else:
                        self.must_draw = self.s.update(self.lcd)
            else:
                sleep(0.2)
                if (self.handleButtons(False)):
                    LCD.setDuty()
                    active = True

    def run(self) -> None:
        if (self.scr_n == None): return
        self.__boot()
        try:
            start_new_thread(self.__manageButtons, ())
            self.__manageScreen()
        except KeyboardInterrupt:
            reset()
