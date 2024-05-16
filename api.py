from requests import get, post
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

    def __post(self, endpoint, d) -> bool:
        gc.collect()
        url = self.base_url + endpoint
        headers = {
            "Authorization": "Bearer " + self.access_token,
            "content-type": "application/json"
        }
        print("Starting post request to " + endpoint)
        response = post(url, headers=headers, json=d)
        return response.status_code == 200
    
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
    
    def changeVolume(self, entity_id: str, up: bool = True) -> None:
        if (up): dir = "up"
        else: dir = "down"
        self.__post(f"/api/services/media_player/volume_{dir}", {"entity_id": entity_id})
        self.__post(f"/api/services/media_player/volume_{dir}", {"entity_id": entity_id})
    
    def nextTrack(self, entity_id: str) -> None:
        self.__post("/api/services/media_player/media_next_track", {"entity_id": entity_id})
    
    def prevTrack(self, entity_id: str) -> None:
        self.__post("/api/services/media_player/media_previous_track", {"entity_id": entity_id})

    def playPause(self, entity_id: str) -> None:
        self.__post("/api/services/media_player/media_play_pause", {"entity_id": entity_id})

    def toggleLight(self, entity_id: str) -> None:
        self.__post("/api/services/light/toggle", {"entity_id": entity_id})
