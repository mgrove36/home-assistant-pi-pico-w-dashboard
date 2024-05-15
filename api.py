from requests import get
import gc

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
        print("Received response for " + endpoint)
        return response.json()
    
    def getLightData(self, entity_id: str) -> dict:
        # TODO: error handling if can't access hass (e.g. no connection, invalid token)
        response = self.__request("/api/states/" + entity_id)
        return {
            "on": response["state"] == "on",
            "rgb_color": response["attributes"]["rgb_color"],
            "rgbw_color": response["attributes"]["rgbw_color"],
            "brightness": response["attributes"]["brightness"],
            "friendly_name": response["attributes"]["friendly_name"],
            "icon": response["attributes"]["icon"]
        }
    
    def getMediaPlayerData(self, entity_id: str) -> dict:
        response = self.__request("/api/states/" + entity_id)
        return {
            "playing": response["state"] in ["on", "playing", "buffering"],
            "shuffle": response["attributes"]["shuffle"],
            "repeat": response["attributes"]["repeat"] == "on",
            "volume_level": response["attributes"]["volume_level"],
            "friendly_name": response["attributes"]["friendly_name"],
            "entity_picture": response["attributes"]["entity_picture"] if "entity_picture" in (dict)(response["attributes"]) else None,
            "media_duration": response["attributes"]["media_duration"] if "media_duration" in (dict)(response["attributes"]) else None,
            "media_position": response["attributes"]["media_position"] if "media_position" in (dict)(response["attributes"]) else None,
            "media_title": response["attributes"]["media_title"] if "media_title" in (dict)(response["attributes"]) else None,
            "media_artist": response["attributes"]["media_artist"] if "media_artist" in (dict)(response["attributes"]) else None,
            "media_album_name": response["attributes"]["media_album_name"] if "media_album_name" in (dict)(response["attributes"]) else None
        }