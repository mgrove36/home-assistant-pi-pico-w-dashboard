from requests import get, post
from gc import collect
from time import mktime, time
from env import HASS_URL, TOKEN

def getReq(endpoint) -> dict:
    collect()
    headers = {
        "Authorization": "Bearer " + TOKEN,
        "content-type": "application/json"
    }
    print("GET " + endpoint)
    try:
        response = get(HASS_URL + endpoint, headers=headers, timeout=2)
        return response.json()
    except:
        return {}

def postReq(endpoint, d) -> bool:
    collect()
    headers = {
        "Authorization": "Bearer " + TOKEN,
        "content-type": "application/json"
    }
    print("POST " + endpoint)
    try:
        response = post(HASS_URL + endpoint, headers=headers, json=d, timeout=2)
        return response.status_code == 200
    except:
        return False

def getLightData(entity_id: str) -> dict:
    # TODO: error handling if can't access hass (e.g. no connection, invalid token)
    response = getReq("/api/states/" + entity_id)
    on = "state" in response and response["state"] == "on"
    return {
        "on": on,
        "rgb_color": response["attributes"]["rgb_color"] if on else None,
        "rgbw_color": response["attributes"]["rgbw_color"] if on else None,
        "brightness": response["attributes"]["brightness"] if on else 0.0
    }

def getMediaPlayerData(entity_id: str) -> dict:
    response = getReq("/api/states/" + entity_id)
    if (not "state" in response or not "attributes" in response):
        response = {
            "state": "",
            "attributes": {}
        }
    e = "state" in response and "attributes" in response
    if ("media_position" in (dict)(response["attributes"])):
        p = response["attributes"]["media_position"]
    else:
        p = 0
    if ("media_position_updated_at" in (dict)(response["attributes"])):
        dts = response["attributes"]["media_position_updated_at"]
        t = mktime((int(dts[0:4]), int(dts[5:7]), int(dts[8:10]), int(dts[11:13]) + int(dts[27:29]), int(dts[14:16]) + int(dts[30:31]), int(dts[17:19]), 0, 0))
        p += time() - t
    return {
        "playing": response["state"] in ["on", "playing", "buffering"],
        "shuffle": response["attributes"]["shuffle"] if e and "shuffle" in response["attributes"] else False,
        "repeat": response["attributes"]["repeat"] == "on" if e and "repeat" in response["attributes"] else False,
        "volume_level": response["attributes"]["volume_level"] if e and "volume_level" in response["attributes"] else 0,
        "media_content_type": response["attributes"]["media_content_type"] if e and "media_content_type" in (dict)(response["attributes"]) else "music",
        "media_series_title": response["attributes"]["media_series_title"] if e and "media_series_title" in (dict)(response["attributes"]) else "",
        "media_season": response["attributes"]["media_season"] if e and "media_season" in (dict)(response["attributes"]) else "",
        "media_episode": response["attributes"]["media_episode"] if e and "media_episode" in (dict)(response["attributes"]) else "",
        "media_duration": response["attributes"]["media_duration"] if e and "media_duration" in (dict)(response["attributes"]) else 0,
        "media_position": p,
        "media_title": response["attributes"]["media_title"] if e and "media_title" in (dict)(response["attributes"]) else "Not playing",
        "media_artist": response["attributes"]["media_artist"] if e and "media_artist" in (dict)(response["attributes"]) else "",
        "media_album_name": response["attributes"]["media_album_name"] if e and "media_album_name" in (dict)(response["attributes"]) else ""
    }

def setVolume(entity_id: str, v: float) -> None:
    postReq(f"/api/services/media_player/volume_set", {"entity_id": entity_id, "volume_level": v})

def nextTrack(entity_id: str) -> None:
    postReq("/api/services/media_player/media_next_track", {"entity_id": entity_id})

def prevTrack(entity_id: str) -> None:
    postReq("/api/services/media_player/media_previous_track", {"entity_id": entity_id})

def playPause(entity_id: str) -> None:
    postReq("/api/services/media_player/media_play_pause", {"entity_id": entity_id})

def toggleLight(entity_id: str) -> None:
    postReq("/api/services/light/toggle", {"entity_id": entity_id})

def setBrightness(entity_id: str, v: int) -> None:
    postReq("/api/services/light/turn_on", {"entity_id": entity_id, "brightness": v})
