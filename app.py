from api import Api
import machine
import network
from time import sleep
from screen import LCD
from font import Font
import gc
from env import *
from utils import Utils
import _thread
import bmp_file_reader as bmpr
import ntptime
import time

class App:
    def __init__(self) -> None:
        if (len(SCREENS) == 0):
            print("No screens configured. Check env.py.")
            self.screen = -1
        else: self.screen = 0
        self.lcd = LCD()
        self.api = Api(HASS_URL, TOKEN)
        self.scr_vals = {} # stored values from the current screen
    
    def __connect(self) -> int:
        wlan = network.WLAN(network.STA_IF)
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
        self.lcd.fill(self.lcd.black)
        Font.cntr_st(self.lcd, self.lcd.width, "Booting...", 120, 2, 150, 150, 150)
        self.lcd.show()
        self.__connect()
        print("Local time before synchronization：%s" %str(time.localtime()))
        ntptime.host = "1.europe.pool.ntp.org"
        ntptime.settime()
        print("Local time after synchronization：%s" %str(time.localtime()))

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
            if (self.lcd.keyA["p"].value() == 0): self.lcd.keyA["v"] = True
            if (self.lcd.keyB["p"].value() == 0): self.lcd.keyB["v"] = True
            if (self.lcd.keyX["p"].value() == 0): self.lcd.keyX["v"] = True
            if (self.lcd.keyY["p"].value() == 0): self.lcd.keyY["v"] = True
            if (self.lcd.right["p"].value() == 0): self.lcd.right["v"] = True
            if (self.lcd.left["p"].value() == 0): self.lcd.left["v"] = True
            if (self.lcd.up["p"].value() == 0):
                self.lcd.up["v"] = True
            if (self.lcd.down["p"].value() == 0): self.lcd.down["v"] = True
            if (self.lcd.ctrl["p"].value() == 0): self.lcd.ctrl["v"] = True
    
    def __changeScreen(self) -> bool:
        orig = self.screen
        if (self.lcd.right["v"]):
            if (self.screen == len(SCREENS) - 1):
                self.screen = 0
            else:
                self.screen += 1
        elif (self.lcd.left["v"]):
            if (self.screen == 0):
                self.screen = len(SCREENS) - 1
            else:
                self.screen -= 1
        change = self.screen != orig
        if (change):
            self.scr_vals = {}
        self.lcd.left["v"] = False
        self.lcd.right["v"] = False
        print(f"Screen change: {change}")
        return change
    
    def __displayLightEntity(self, i: int, w: int, h: int, xo: int, yo: int, n: str, d) -> None:
        self.scr_vals[i] = d
        # if the light is turned on, display the filled-in lightbulb icon in the colour of the light, centrally in the light's grid square
        if (d["on"]):
            color = Utils.colour(d["rgb_color"][0], d["rgb_color"][1], d["rgb_color"][2])
            with open("images/lightbulb-on.bmp", "rb") as file_handle:
                reader = bmpr.BMPFileReader(file_handle)
                img_height = reader.get_height()
                x_offset = w//2 + xo - reader.get_width()//2
                y_offset = h//2 + yo - reader.get_height()//2 - 4
                for row_i in range(0, reader.get_height()):
                    row = reader.get_row(row_i)
                    for col_i, color in enumerate(row):
                        r = d["rgb_color"][0] if (color.red) != 0 else 0
                        g = d["rgb_color"][1] if (color.green) != 0 else 0
                        b = d["rgb_color"][2] if (color.blue) != 0 else 0
                        if (color.red != 0 or color.green != 0 or color.blue != 0):
                            self.lcd.pixel(col_i + x_offset, row_i + y_offset, Utils.colour(r,g,b))
        # otherwise display the outline lightbulb icon in grey, centrally in the light's grid square
        else:
            color = Utils.colour(80, 80, 80)
            with open("images/lightbulb-off.bmp", "rb") as file_handle:
                reader = bmpr.BMPFileReader(file_handle)
                img_height = reader.get_height()
                x_offset = w//2 + xo - reader.get_width()//2
                y_offset = h//2 + yo - reader.get_height()//2 - 4
                for row_i in range(0, reader.get_height()):
                    row = reader.get_row(row_i)
                    for col_i, color in enumerate(row):
                        if (color.red != 0 or color.green != 0 or color.blue != 0):
                            self.lcd.pixel(col_i + x_offset, row_i + y_offset, Utils.colour(color.red, color.green, color.blue))
        # display the name of the light 8px below the lightbulb icon
        Font.cntr_st(self.lcd, w, n, y_offset + img_height + 8, 2, 220, 220, 220, xo)
    
    def __displayLightsScreen(self, d=None) -> None:
        # display up to four lights as defined in env.py
        self.lcd.fill(self.lcd.black)
        Font.cntr_st(self.lcd, self.lcd.width, SCREENS[self.screen]["name"], 10, 2, 255, 255, 255)
        entities = len(SCREENS[self.screen]["entities"])
        # for each defined entity (up to a max total of 4), display its data in a 2x2 grid
        if (d == None): d = []
        for i in range(0, min(entities, 4)):
            if (len(d) == i): d.append(self.api.getLightData(SCREENS[self.screen]["entities"][i]["id"]))
            self.__displayLightEntity(i, self.lcd.width//2, self.lcd.height//2, self.lcd.width//2 * (i % 2), self.lcd.height//2 * (i//2), SCREENS[self.screen]["entities"][i]["name"], d[i])
        self.lcd.show()
        # TODO: handle buttons

    def __updateMediaPositionBar(self, d):
        if (d["media_position"] != None and d["media_duration"] != None and d["media_duration"] != 0):
            for x in range (0, (self.lcd.width * d["media_position"])//d["media_duration"]):
                self.lcd.pixel(x, self.lcd.height - 2, self.lcd.white)
                self.lcd.pixel(x, self.lcd.height - 1, self.lcd.white)
                self.lcd.pixel(x, self.lcd.height, self.lcd.white)

    def __displayMediaScreen(self, d=None) -> None:
        self.lcd.fill(self.lcd.black)
        e = SCREENS[self.screen]["entity"]
        if (e == None and d == None):
            Font.cntr_st(self.lcd, self.lcd.width, "No media player selected", 110, 3, 255, 255, 255)
            self.lcd.show()
            return
        if (d == None): d = self.api.getMediaPlayerData(e)
        self.scr_vals[0] = d
        self.lcd.fill(self.lcd.black)
        Font.cntr_st(self.lcd, self.lcd.width, SCREENS[self.screen]["name"], 20, 2, 255, 255, 255)
        self.__updateMediaPositionBar(d)
        if (d["media_duration"] != None):
            mins = d["media_duration"] // 60
            secs = d["media_duration"] % 60
            Font.rght_st(self.lcd, f"{mins}:{secs}", self.lcd.width, self.lcd.height - 16, 1, 180, 180, 180)
        Font.cntr_st(self.lcd, self.lcd.width, d["media_title"], self.lcd.height - 72, 3, 255, 255, 255)
        Font.cntr_st(self.lcd, self.lcd.width, d["media_artist"], self.lcd.height - 96, 2, 255, 255, 255)
        self.lcd.show()
        # TODO: display album art
        # TODO: handle button presses for volume and changing tracks
        # TODO: add icons next to buttons
    
    def __displayUnknownScreen(self) -> None:
        self.lcd.fill(self.lcd.black)
        Font.cntr_st(self.lcd, self.lcd.width, "Invalid config", 110, 3, 255, 255, 255)
        Font.cntr_st(self.lcd, self.lcd.width, "Screen " + str(self.screen), 130, 2, 255, 255, 255)

    def __updateLightsScreen(self) -> None:
        e = min(len(SCREENS[self.screen]["entities"]), 4)
        # for each light to be displayed
        for i in range(0, e):
            # if its settings have changed, re-draw them without clearing the display
            d = self.api.getLightData(SCREENS[self.screen]["entities"][i]["id"])
            if (d != self.scr_vals[i]):
                self.__displayLightEntity(i, self.lcd.width//2, self.lcd.height//2, self.lcd.width//2 * (i % 2), self.lcd.height//2 * (i//2), SCREENS[self.screen]["entities"][i]["name"], d[i])
        # TODO: double button press to select a light, then up/down to change brightness? and single button click to turn on/off?
        self.lcd.show()

    def __handleLightsScreenButtons(self) -> bool:
        # TODO: reset buttons used
        return False

    def __updateMediaScreen(self) -> None:
        d = self.api.getMediaPlayerData(SCREENS[self.screen]["entity"])
        # if same media is playing (same title and duration), just update the position bar
        if (self.scr_vals[0]["media_title"] == d["media_title"] and self.scr_vals[0]["media_duration"] == d["media_duration"]):
            self.__updateMediaPositionBar(d)
            self.lcd.show()
        # otherwise redraw the whole screen
        else:
            self.__displayMediaScreen(d)

    def __handleMediaScreenButtons(self) -> bool:
        up = self.lcd.up["v"]
        down = self.lcd.down["v"]
        self.lcd.up["v"] = False
        self.lcd.down["v"] = False
        a = False
        if (up):
            self.api.changeVolume(SCREENS[self.screen]["entity"])
            a = True
        elif (down):
            self.api.changeVolume(SCREENS[self.screen]["entity"], False)
            a = True
        return a
        # if (a): self.__handleMediaScreenButtons()

    def __manageScreen(self) -> None:
        started = False
        while (True):
            gc.collect()
            changed = not started or self.__changeScreen()
            # TODO: make screen not change within given interval, as holding button too long changes it twice
            if (not started): started = True
            # if the screen has changed, redraw the whole screen
            if (changed):
                if (SCREENS[self.screen]["type"] == 0):
                    self.__resetButtonStatuses()
                    self.__displayLightsScreen()
                elif (SCREENS[self.screen]["type"] == 1):
                    self.__resetButtonStatuses()
                    self.__displayMediaScreen()
                else:
                    self.__resetButtonStatuses()
                    self.__displayUnknownScreen()
            # otherwise minimise the number of pixels being changed
            else:
                if (SCREENS[self.screen]["type"] == 0):
                    if (self.__handleLightsScreenButtons()): continue
                    self.__updateLightsScreen()
                elif (SCREENS[self.screen]["type"] == 1):
                    if (self.__handleMediaScreenButtons()): continue
                    self.__updateMediaScreen()

    def run(self) -> None:
        if (self.screen == None): return
        self.__boot()
        try:
            _thread.start_new_thread(self.__manageButtons, ())
            self.__manageScreen()
        except KeyboardInterrupt:
            machine.reset()

if __name__ == "__main__":
    app = App()
    app.run()