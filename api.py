from requests import get
import gc
import time

class Api:
    def __init__(self, base_url, access_token) -> None:
        self.base_url = base_url
        self.access_token = access_token

    def __request(self, endpoint) -> dict:
        gc.collect()
        url = self.base_url + endpoint
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "content-type": "application/json"
        }
        print("Starting request for " + endpoint)
        response = get(url, headers=headers)
        return response.json()
    
    def getLightData(self, entity_id: str) -> dict:
        # TODO: error handling if can't access hass (e.g. no connection, invalid token)
        response = self.__request("/api/states/" + entity_id)
        on = response["state"] == "on"
        return {
            "on": on,
            "rgb_color": response["attributes"]["rgb_color"] if on else None,
            "rgbw_color": response["attributes"]["rgbw_color"] if on else None,
            "brightness": response["attributes"]["brightness"] if on else 0,
            "friendly_name": response["attributes"]["friendly_name"]
        }
    
    def getMediaPlayerData(self, entity_id: str) -> dict:
        response = self.__request("/api/states/" + entity_id)
        if ("media_position" in (dict)(response["attributes"])):
            p = response["attributes"]["media_position"]
        else:
            p = 0
        if ("media_position_updated_at" in (dict)(response["attributes"])):
            dts = response["attributes"]["media_position_updated_at"]
            # p += (datetime.now() - datetime.strptime(dts, "%Y-%m-%dT%H:%M:%S.%f%z")).total_seconds()
            print(dts)
            t = time.mktime((int(dts[0:4]), int(dts[5:7]), int(dts[8:10]), int(dts[11:13]) + int(dts[27:29]), int(dts[14:16]) + int(dts[30:31]), int(dts[17:19]), 0, 0))
            p += time.mktime(time.localtime()) - t
        return {
            "playing": response["state"] in ["on", "playing", "buffering"],
            "shuffle": response["attributes"]["shuffle"],
            "repeat": response["attributes"]["repeat"] == "on",
            "volume_level": response["attributes"]["volume_level"],
            "friendly_name": response["attributes"]["friendly_name"],
            "entity_picture": response["attributes"]["entity_picture"] if "entity_picture" in (dict)(response["attributes"]) else None,
            "media_duration": response["attributes"]["media_duration"] if "media_duration" in (dict)(response["attributes"]) else 0,
            "media_position": p,
            "media_title": response["attributes"]["media_title"] if "media_title" in (dict)(response["attributes"]) else "Nothing playing",
            "media_artist": response["attributes"]["media_artist"] if "media_artist" in (dict)(response["attributes"]) else "",
            "media_album_name": response["attributes"]["media_album_name"] if "media_album_name" in (dict)(response["attributes"]) else ""
        }