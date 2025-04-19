HOSTNAME="pico-hostname"
SSID = 'wifi-ssid'
WIFI_PASSWORD = 'wifi-password'
HASS_URL = "http://url.to.hass:port"
TOKEN = "long.lived.hass.token"
SCREENS = [
    {
        "name": "Lights",
        "type": 0,
        "entities": [
            {
                "id": "light.bedroom_light",
                "name": "Bedroom"
            },
            {
                "id": "light.bedroom_lamp",
                "name": "Lamp"
            },
            {
                "id": "light.tv_leds",
                "name": "TV"
            },
            {
                "id": "light.bedroom_lights",
                "name": "All"
            }
        ]
    },
    {
        "name": "Kitchen",
        "type": 1,
        "entity": "media_player.kitchen"
    },
    {
        "name": "Living Room",
        "type": 1,
        "entity": "media_player.living_room"
    }
]