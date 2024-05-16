from font import Font
from utils import Utils
import bmp_file_reader as bmpr

class Screen():
    def __init__(self, api, n: str) -> None:
        self.api = api
        self.name = n
        self.d = {}
        self.prev = {}

    def display(self, lcd) -> None:
        lcd.fill(lcd.black)
        Font.cntr_st(lcd, lcd.width, self.name, 20, 2, 255, 255, 255)

    def update(self, lcd) -> None:
        pass

    def handleButtons(self, up: bool, down: bool, left: bool, right: bool, keyA: bool, keyB: bool, keyX: bool, keyY: bool, ctrl: bool) -> bool:
        return False
    
    def _updateData(self) -> dict:
        return {}

    def _invalidConfig(self, lcd) -> None:
        Font.cntr_st(lcd, lcd.width, "Invalid config", lcd.height//2, 2, 255, 255, 255)
        lcd.show()

class MediaScreen(Screen):
    def __init__(self, api, n: str, e: str) -> None:
        super().__init__(api, n)
        self.e = e
        self.valid = e != None and e != ""
    
    def display(self, lcd) -> None:
        super().display(lcd)
        if (not self.valid):
            self._invalidConfig(lcd)
            return
        if (self.d == {}):
            self.d = self._updateData()
        self.__updateMediaPositionBar(lcd, self.d["media_position"], self.d["media_duration"])
        if (self.d["media_duration"] != None):
            mins = self.d["media_duration"] // 60
            secs = self.d["media_duration"] % 60
            Font.rght_st(lcd, f"{mins}:{secs}", lcd.width, lcd.height - 16, 1, 180, 180, 180)
        Font.cntr_st(lcd, lcd.width, self.d["media_title"], lcd.height - 72, 3, 255, 255, 255)
        Font.cntr_st(lcd, lcd.width, self.d["media_artist"], lcd.height - 96, 2, 255, 255, 255)
        lcd.show()
    
    def __updateMediaPositionBar(self, lcd, p: int, d: int):
        if (d > 0):
            for x in range (0, (lcd.width * p)//d):
                lcd.pixel(x, lcd.height - 5, lcd.white)
                lcd.pixel(x, lcd.height - 4, lcd.white)
                lcd.pixel(x, lcd.height - 3, lcd.white)
                lcd.pixel(x, lcd.height - 2, lcd.white)
                lcd.pixel(x, lcd.height - 1, lcd.white)
                lcd.pixel(x, lcd.height, lcd.white)

    def update(self, lcd):
        if (not self.valid):
            super().display(lcd)
            self._invalidConfig(lcd)
            return
        self._updateData()
        # if same media is playing (same title and duration), just update the position bar
        if (self.d["media_title"] == self.prev["media_title"] and self.d["media_duration"] == self.prev["media_duration"]):
            self.__updateMediaPositionBar(lcd, self.d["media_position"], self.d["media_duration"])
            lcd.show()
        # otherwise redraw the whole screen
        else:
            self.display(lcd)

    def _updateData(self) -> dict:
        self.prev = self.d
        self.d = self.api.getMediaPlayerData(self.e)
        return self.d
    
    def handleButtons(self, up: bool, down: bool, left: bool, right: bool, keyA: bool, keyB: bool, keyX: bool, keyY: bool, ctrl: bool) -> bool:
        a = False
        if (up):
            self.api.changeVolume(self.e)
            a = True
        elif (down):
            self.api.changeVolume(self.e, False)
            a = True
        if (keyX):
            self.api.nextTrack(self.e)
        elif (keyY):
            self.api.prevTrack(self.e)
        if (keyA):
            self.api.playPause(self.e)
        return a

class LightsScreen(Screen):
    def __init__(self, api, n: str, es: list) -> None:
        super().__init__(api, n)
        self.es = es
        self.valid = es != None and len(es) != 0
    
    def display(self, lcd) -> None:
        super().display(lcd)
        if (not self.valid):
            self._invalidConfig(lcd)
            return
        if (self.d == {}):
            self._updateData()
        # display up to four lights as defined in env.py
        # for each defined entity (up to a max total of 4), display its data in a 2x2 grid
        for i in range(0, len(self.d)):
            self.__displayLightEntity(lcd, i, lcd.width//2, lcd.height//2, lcd.width//2 * (i % 2), lcd.height//2 * (i//2), self.es[i]["name"], self.d[i])
        lcd.show()
    
    def __displayLightEntity(self, lcd, i: int, w: int, h: int, xo: int, yo: int, n: str, d) -> None:
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
                            lcd.pixel(col_i + x_offset, row_i + y_offset, Utils.colour(r,g,b))
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
                            lcd.pixel(col_i + x_offset, row_i + y_offset, Utils.colour(color.red, color.green, color.blue))
                        else:
                            lcd.pixel(col_i + x_offset, row_i + y_offset, Utils.colour(0,0,0))
        # display the name of the light 8px below the lightbulb icon
        Font.cntr_st(lcd, w, n, y_offset + img_height + 8, 2, 220, 220, 220, xo)

    def update(self, lcd):
        if (not self.valid):
            super().display(lcd)
            self._invalidConfig(lcd)
            return
        self._updateData()
        # for each light to be displayed
        for i in range(0, len(self.d)):
            # if its settings have changed, re-draw them without clearing the display
            if (self.d[i] != self.prev[i]):
                self.__displayLightEntity(lcd, i, lcd.width//2, lcd.height//2, lcd.width//2 * (i % 2), lcd.height//2 * (i//2), self.es[i]["name"], self.d[i])
        lcd.show()

    def _updateData(self) -> dict:
        self.prev = self.d
        for i in range(0, min(len(self.es), 4)):
            self.d[i] = self.api.getLightData(self.es[i]["id"])
        return self.d
    
    def handleButtons(self, up: bool, down: bool, left: bool, right: bool, keyA: bool, keyB: bool, keyX: bool, keyY: bool, ctrl: bool) -> bool:
        e = min(len(self.es), 4)
        b = [keyA, keyB, keyX, keyY]
        a = False
        for i in range(0, e):
            # if button for light clicked, toggle the light
            if (b[i]):
                self.api.toggleLight(self.es[i]["id"])
                a = True
            # if up/down clicked, adjust brightness for all lights that are turned on
            pcfg = i in self.prev and "on" in self.prev[i] and self.prev[i]["on"] and "brightness" in self.prev[i]
            if (up and pcfg):
                self.api.setBrightness(self.es[i]["id"], min(255, self.prev[i]["brightness"] + 35))
                a = True
            elif (down and pcfg):
                self.api.setBrightness(self.es[i]["id"], max(1, self.prev[i]["brightness"] - 35))
                a = True
        return a
    
class UnknownScreen(Screen):
    def __init__(self, api, t: int, n: str) -> None:
        super().__init__(api, t, n)
    
    def display(self, lcd) -> None:
        super().display(lcd)
        self._invalidConfig(lcd)
    
    def update(self, lcd) -> None:
        pass

    def _updateData(self) -> dict:
        return {}

    def handleButtons(self, up: bool, down: bool, left: bool, right: bool, keyA: bool, keyB: bool, keyX: bool, keyY: bool, ctrl: bool) -> bool:
        return False
