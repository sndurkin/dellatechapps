import logging
import requests
import json
import os
import textwrap
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

EASTERN_TZ = ZoneInfo('America/New_York')

logger = logging.getLogger(__name__)



weather_codes = {
    "code_to_slug": {
        "1000": "clear",
        "1001": "cloudy",
        "1100": "mostly-clear",
        "1101": "partly-cloudy",
        "1102": "mostly-cloudy",
        "1103": "partly-cloudy-mostly-clear",
        "2000": "fog",
        "2100": "light-fog",
        "2101": "mostly-clear-light-fog",
        "2102": "partly-cloudy-light-fog",
        "2103": "mostly-cloudy-light-fog",
        "2106": "mostly-clear-fog",
        "2107": "partly-cloudy-fog",
        "2108": "mostly-cloudy-fog",
        "4000": "drizzle",
        "4001": "rain",
        "4200": "light-rain",
        "4201": "heavy-rain",
        "4202": "partly-cloudy-heavy-rain",
        "4203": "mostly-clear-drizzle",
        "4204": "partly-cloudy-drizzle",
        "4205": "mostly-cloudy-drizzle",
        "4208": "partly-cloudy-rain",
        "4209": "mostly-clear-rain",
        "4210": "mostly-cloudy-rain",
        "4211": "mostly-clear-heavy-rain",
        "4212": "mostly-cloudy-heavy-rain",
        "4213": "mostly-clear-light-rain",
        "4214": "partly-cloudy-light-rain",
        "4215": "mostly-cloudy-light-rain",
        "5000": "snow",
        "5001": "flurries",
        "5100": "light-snow",
        "5101": "heavy-snow",
        "5102": "mostly-clear-light-snow",
        "5103": "partly-cloudy-light-snow",
        "5104": "mostly-cloudy-light-snow",
        "5105": "mostly-clear-snow",
        "5106": "partly-cloudy-snow",
        "5107": "mostly-cloudy-snow",
        "5108": "rain-snow",
        "5110": "drizzle-snow",
        "5112": "snow-ice-pellets",
        "5114": "snow-freezing-rain",
        "5115": "mostly-clear-flurries",
        "5116": "partly-cloudy-flurries",
        "5117": "mostly-cloudy-flurries",
        "5119": "mostly-clear-heavy-snow",
        "5120": "partly-cloudy-heavy-snow",
        "5121": "mostly-cloudy-heavy-snow",
        "5122": "drizzle-light-snow",
        "6000": "freezing-drizzle",
        "6001": "freezing-rain",
        "6002": "partly-cloudy-freezing-drizzle",
        "6003": "mostly-clear-freezing-drizzle",
        "6004": "mostly-cloudy-freezing-drizzle",
        "6200": "light-freezing-drizzle",
        "6201": "heavy-freezing-rain",
        "6202": "partly-cloudy-heavy-freezing-rain",
        "6203": "partly-cloudy-light-freezing-rain",
        "6204": "drizzle-freezing-drizzle",
        "6205": "mostly-clear-light-freezing-rain",
        "6206": "light-rain-freezing-drizzle",
        "6207": "mostly-clear-heavy-freezing-rain",
        "6208": "mostly-cloudy-heavy-freezing-rain",
        "6209": "mostly-cloudy-light-freezing-rain",
        "6212": "drizzle-freezing-rain",
        "6213": "mostly-clear-freezing-rain",
        "6214": "partly-cloudy-freezing-rain",
        "6215": "mostly-cloudy-freezing-rain",
        "6220": "light-rain-freezing-rain",
        "6222": "rain-freezing-rain",
        "7000": "ice-pellets",
        "7101": "heavy-ice-pellets",
        "7102": "light-ice-pellets",
        "7103": "freezing-rain-heavy-ice-pellets",
        "7105": "drizzle-ice-pellets",
        "7106": "freezing-rain-ice-pellets",
        "7107": "partly-cloudy-ice-pellets",
        "7108": "mostly-clear-ice-pellets",
        "7109": "mostly-cloudy-ice-pellets",
        "7110": "mostly-clear-light-ice-pellets",
        "7111": "partly-cloudy-light-ice-pellets",
        "7112": "mostly-cloudy-light-ice-pellets",
        "7113": "mostly-clear-heavy-ice-pellets",
        "7114": "partly-cloudy-heavy-ice-pellets",
        "7115": "light-rain-ice-pellets",
        "7116": "mostly-cloudy-heavy-ice-pellets",
        "7117": "rain-ice-pellets",
        "8000": "thunderstorm",
        "8001": "mostly-clear-thunderstorm",
        "8002": "mostly-cloudy-thunderstorm",
        "8003": "partly-cloudy-thunderstorm",
        "10000": "clear",
        "10001": "clear",
        "10010": "cloudy",
        "10011": "cloudy",
        "11000": "mostly-clear",
        "11001": "mostly-clear",
        "11010": "partly-cloudy",
        "11011": "partly-cloudy",
        "11020": "mostly-cloudy",
        "11021": "mostly-cloudy",
        "11030": "partly-cloudy-mostly-clear",
        "11031": "partly-cloudy-mostly-clear",
        "20000": "fog",
        "20001": "fog",
        "21000": "light-fog",
        "21001": "light-fog",
        "21010": "mostly-clear-light-fog",
        "21011": "mostly-clear-light-fog",
        "21020": "partly-cloudy-light-fog",
        "21021": "partly-cloudy-light-fog",
        "21030": "mostly-cloudy-light-fog",
        "21031": "mostly-cloudy-light-fog",
        "21060": "mostly-clear-fog",
        "21061": "mostly-clear-fog",
        "21070": "partly-cloudy-fog",
        "21071": "partly-cloudy-fog",
        "21080": "mostly-cloudy-fog",
        "21081": "mostly-cloudy-fog",
        "40000": "drizzle",
        "40001": "drizzle",
        "40010": "rain",
        "40011": "rain",
        "42000": "light-rain",
        "42001": "light-rain",
        "42010": "heavy-rain",
        "42011": "heavy-rain",
        "42020": "partly-cloudy-heavy-rain",
        "42021": "partly-cloudy-heavy-rain",
        "42030": "mostly-clear-drizzle",
        "42031": "mostly-clear-drizzle",
        "42040": "partly-cloudy-drizzle",
        "42041": "partly-cloudy-drizzle",
        "42050": "mostly-cloudy-drizzle",
        "42051": "mostly-cloudy-drizzle",
        "42080": "partly-cloudy-rain",
        "42081": "partly-cloudy-rain",
        "42090": "mostly-clear-rain",
        "42091": "mostly-clear-rain",
        "42100": "mostly-cloudy-rain",
        "42101": "mostly-cloudy-rain",
        "42110": "mostly-clear-heavy-rain",
        "42111": "mostly-clear-heavy-rain",
        "42120": "mostly-cloudy-heavy-rain",
        "42121": "mostly-cloudy-heavy-rain",
        "42130": "mostly-clear-light-rain",
        "42131": "mostly-clear-light-rain",
        "42140": "partly-cloudy-light-rain",
        "42141": "partly-cloudy-light-rain",
        "42150": "mostly-cloudy-light-rain",
        "42151": "mostly-cloudy-light-rain",
        "50000": "snow",
        "50001": "snow",
        "50010": "flurries",
        "50011": "flurries",
        "51000": "light-snow",
        "51001": "light-snow",
        "51010": "heavy-snow",
        "51011": "heavy-snow",
        "51020": "mostly-clear-light-snow",
        "51021": "mostly-clear-light-snow",
        "51030": "partly-cloudy-light-snow",
        "51031": "partly-cloudy-light-snow",
        "51040": "mostly-cloudy-light-snow",
        "51041": "mostly-cloudy-light-snow",
        "51050": "mostly-clear-snow",
        "51051": "mostly-clear-snow",
        "51060": "partly-cloudy-snow",
        "51061": "partly-cloudy-snow",
        "51070": "mostly-cloudy-snow",
        "51071": "mostly-cloudy-snow",
        "51080": "rain-snow",
        "51081": "rain-snow",
        "51100": "drizzle-snow",
        "51101": "drizzle-snow",
        "51120": "snow-ice-pellets",
        "51121": "snow-ice-pellets",
        "51140": "snow-freezing-rain",
        "51141": "snow-freezing-rain",
        "51150": "mostly-clear-flurries",
        "51151": "mostly-clear-flurries",
        "51160": "partly-cloudy-flurries",
        "51161": "partly-cloudy-flurries",
        "51170": "mostly-cloudy-flurries",
        "51171": "mostly-cloudy-flurries",
        "51190": "mostly-clear-heavy-snow",
        "51191": "mostly-clear-heavy-snow",
        "51200": "partly-cloudy-heavy-snow",
        "51201": "partly-cloudy-heavy-snow",
        "51210": "mostly-cloudy-heavy-snow",
        "51211": "mostly-cloudy-heavy-snow",
        "51220": "drizzle-light-snow",
        "51221": "drizzle-light-snow",
        "60000": "freezing-drizzle",
        "60001": "freezing-drizzle",
        "60010": "freezing-rain",
        "60011": "freezing-rain",
        "60020": "partly-cloudy-freezing-drizzle",
        "60021": "partly-cloudy-freezing-drizzle",
        "60030": "mostly-clear-freezing-drizzle",
        "60031": "mostly-clear-freezing-drizzle",
        "60040": "mostly-cloudy-freezing-drizzle",
        "60041": "mostly-cloudy-freezing-drizzle",
        "62000": "light-freezing-drizzle",
        "62001": "light-freezing-drizzle",
        "62010": "heavy-freezing-rain",
        "62011": "heavy-freezing-rain",
        "62020": "partly-cloudy-heavy-freezing-rain",
        "62021": "partly-cloudy-heavy-freezing-rain",
        "62030": "partly-cloudy-light-freezing-rain",
        "62031": "partly-cloudy-light-freezing-rain",
        "62040": "drizzle-freezing-drizzle",
        "62041": "drizzle-freezing-drizzle",
        "62050": "mostly-clear-light-freezing-rain",
        "62051": "mostly-clear-light-freezing-rain",
        "62060": "light-rain-freezing-drizzle",
        "62061": "light-rain-freezing-drizzle",
        "62070": "mostly-clear-heavy-freezing-rain",
        "62071": "mostly-clear-heavy-freezing-rain",
        "62080": "mostly-cloudy-heavy-freezing-rain",
        "62081": "mostly-cloudy-heavy-freezing-rain",
        "62090": "mostly-cloudy-light-freezing-rain",
        "62091": "mostly-cloudy-light-freezing-rain",
        "62120": "drizzle-freezing-rain",
        "62121": "drizzle-freezing-rain",
        "62130": "mostly-clear-freezing-rain",
        "62131": "mostly-clear-freezing-rain",
        "62140": "partly-cloudy-freezing-rain",
        "62141": "partly-cloudy-freezing-rain",
        "62150": "mostly-cloudy-freezing-rain",
        "62151": "mostly-cloudy-freezing-rain",
        "62200": "light-rain-freezing-rain",
        "62201": "light-rain-freezing-rain",
        "62220": "rain-freezing-rain",
        "62221": "rain-freezing-rain",
        "70000": "ice-pellets",
        "70001": "ice-pellets",
        "71010": "heavy-ice-pellets",
        "71011": "heavy-ice-pellets",
        "71020": "light-ice-pellets",
        "71021": "light-ice-pellets",
        "71030": "freezing-rain-heavy-ice-pellets",
        "71031": "freezing-rain-heavy-ice-pellets",
        "71050": "drizzle-ice-pellets",
        "71051": "drizzle-ice-pellets",
        "71060": "freezing-rain-ice-pellets",
        "71061": "freezing-rain-ice-pellets",
        "71070": "partly-cloudy-ice-pellets",
        "71071": "partly-cloudy-ice-pellets",
        "71080": "mostly-clear-ice-pellets",
        "71081": "mostly-clear-ice-pellets",
        "71090": "mostly-cloudy-ice-pellets",
        "71091": "mostly-cloudy-ice-pellets",
        "71100": "mostly-clear-light-ice-pellets",
        "71101": "mostly-clear-light-ice-pellets",
        "71110": "partly-cloudy-light-ice-pellets",
        "71111": "partly-cloudy-light-ice-pellets",
        "71120": "mostly-cloudy-light-ice-pellets",
        "71121": "mostly-cloudy-light-ice-pellets",
        "71130": "mostly-clear-heavy-ice-pellets",
        "71131": "mostly-clear-heavy-ice-pellets",
        "71140": "partly-cloudy-heavy-ice-pellets",
        "71141": "partly-cloudy-heavy-ice-pellets",
        "71150": "light-rain-ice-pellets",
        "71151": "light-rain-ice-pellets",
        "71160": "mostly-cloudy-heavy-ice-pellets",
        "71161": "mostly-cloudy-heavy-ice-pellets",
        "71170": "rain-ice-pellets",
        "71171": "rain-ice-pellets",
        "80000": "thunderstorm",
        "80001": "thunderstorm",
        "80010": "mostly-clear-thunderstorm",
        "80011": "mostly-clear-thunderstorm",
        "80020": "mostly-cloudy-thunderstorm",
        "80021": "mostly-cloudy-thunderstorm",
        "80030": "partly-cloudy-thunderstorm",
        "80031": "partly-cloudy-thunderstorm"
    },
    "slug_to_meta": {
        "clear": {
            "name": "Clear",
            "icon": "wi-day-sunny",
        },
        "mostly-clear": {
            "name": "Mostly Clear",
            "icon": "wi-day-sunny",
        },
        "partly-cloudy": {
            "name": "Partly Cloudy",
            "icon": "wi-day-cloudy",
        },
        "mostly-cloudy": {
            "name": "Mostly Cloudy",
            "icon": "wi-day-cloudy",
        },
        "cloudy": {
            "name": "Cloudy",
            "icon": "wi-day-cloudy",
        },
        "partly-cloudy-mostly-clear": {
            "name": "Partly Cloudy, Mostly Clear",
            "icon": "wi-day-cloudy",
        },
        "light-fog": {
            "name": "Light Fog",
            "icon": "wi-day-fog",
        },
        "fog": {
            "name": "Fog",
            "icon": "wi-day-fog",
        },
        "mostly-clear-light-fog": {
            "name": "Mostly Clear, Light Fog",
            "icon": "wi-day-fog",
        },
        "partly-cloudy-light-fog": {
            "name": "Partly Cloudy, Light Fog",
            "icon": "wi-day-fog",
        },
        "mostly-cloudy-light-fog": {
            "name": "Mostly Cloudy, Light Fog",
            "icon": "wi-day-fog",
        },
        "mostly-clear-fog": {
            "name": "Mostly Clear, Fog",
            "icon": "wi-day-fog",
        },
        "partly-cloudy-fog": {
            "name": "Partly Cloudy, Fog",
            "icon": "wi-day-fog",
        },
        "mostly-cloudy-fog": {
            "name": "Mostly Cloudy, Fog",
            "icon": "wi-day-fog",
        },
        "drizzle": {
            "name": "Drizzle",
            "icon": "wi-day-showers",
        },
        "light-rain": {
            "name": "Light Rain",
            "icon": "wi-day-showers",
        },
        "rain": {
            "name": "Rain",
            "icon": "wi-day-rain",
        },
        "heavy-rain": {
            "name": "Heavy Rain",
            "icon": "wi-day-rain",
        },
        "mostly-clear-drizzle": {
            "name": "Mostly Clear, Drizzle",
            "icon": "wi-day-sprinkle",
        },
        "partly-cloudy-drizzle": {
            "name": "Partly Cloudy, Drizzle",
            "icon": "wi-day-sprinkle",
        },
        "mostly-cloudy-drizzle": {
            "name": "Mostly Cloudy, Drizzle",
            "icon": "wi-day-sprinkle",
        },
        "mostly-clear-light-rain": {
            "name": "Mostly Clear, Light Rain",
            "icon": "wi-day-showers",
        },
        "partly-cloudy-light-rain": {
            "name": "Partly Cloudy, Light Rain",
            "icon": "wi-day-showers",
        },
        "mostly-cloudy-light-rain": {
            "name": "Mostly Cloudy, Light Rain",
            "icon": "wi-day-showers",
        },
        "mostly-clear-rain": {
            "name": "Mostly Clear, Rain",
            "icon": "wi-day-rain-mix",
        },
        "partly-cloudy-rain": {
            "name": "Partly Cloudy, Rain",
            "icon": "wi-day-rain",
        },
        "mostly-cloudy-rain": {
            "name": "Mostly Cloudy, Rain",
            "icon": "wi-day-rain",
        },
        "mostly-clear-heavy-rain": {
            "name": "Mostly Clear, Heavy Rain",
            "icon": "wi-day-rain",
        },
        "partly-cloudy-heavy-rain": {
            "name": "Partly Cloudy, Heavy Rain",
            "icon": "wi-day-rain",
        },
        "mostly-cloudy-heavy-rain": {
            "name": "Mostly Cloudy, Heavy Rain",
            "icon": "wi-day-rain",
        },
        "flurries": {
            "name": "Flurries",
            "icon": "wi-day-snow",
        },
        "light-snow": {
            "name": "Light Snow",
            "icon": "wi-day-snow",
        },
        "snow": {
            "name": "Snow",
            "icon": "wi-day-snow",
        },
        "heavy-snow": {
            "name": "Heavy Snow",
            "icon": "wi-day-snow",
        },
        "mostly-clear-flurries": {
            "name": "Mostly Clear, Flurries",
            "icon": "wi-day-snow",
        },
        "partly-cloudy-flurries": {
            "name": "Partly Cloudy, Flurries",
            "icon": "wi-day-snow",
        },
        "mostly-cloudy-flurries": {
            "name": "Mostly Cloudy, Flurries",
            "icon": "wi-day-snow",
        },
        "drizzle-light-snow": {
            "name": "Drizzle, Light Snow",
            "icon": "wi-day-snow",
        },
        "mostly-clear-light-snow": {
            "name": "Mostly Clear, Light Snow",
            "icon": "wi-day-snow",
        },
        "partly-cloudy-light-snow": {
            "name": "Partly Cloudy, Light Snow",
            "icon": "wi-day-snow",
        },
        "mostly-cloudy-light-snow": {
            "name": "Mostly Cloudy, Light Snow",
            "icon": "wi-day-snow",
        },
        "mostly-clear-snow": {
            "name": "Mostly Clear, Snow",
            "icon": "wi-day-snow",
        },
        "partly-cloudy-snow": {
            "name": "Partly Cloudy, Snow",
            "icon": "wi-day-snow",
        },
        "mostly-cloudy-snow": {
            "name": "Mostly Cloudy, Snow",
            "icon": "wi-day-snow",
        },
        "mostly-clear-heavy-snow": {
            "name": "Mostly Clear, Heavy Snow",
            "icon": "wi-day-snow",
        },
        "partly-cloudy-heavy-snow": {
            "name": "Partly Cloudy, Heavy Snow",
            "icon": "wi-day-snow",
        },
        "mostly-cloudy-heavy-snow": {
            "name": "Mostly Cloudy, Heavy Snow",
            "icon": "wi-day-snow",
        },
        "drizzle-snow": {
            "name": "Drizzle, Snow",
            "icon": "wi-day-snow",
        },
        "rain-snow": {
            "name": "Rain, Snow",
            "icon": "wi-day-sleet",
        },
        "snow-freezing-rain": {
            "name": "Snow, Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "snow-ice-pellets": {
            "name": "Snow, Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "freezing-drizzle": {
            "name": "Freezing Drizzle",
            "icon": "wi-day-sleet",
        },
        "light-freezing-drizzle": {
            "name": "Light Freezing Drizzle",
            "icon": "wi-day-sleet",
        },
        "freezing-rain": {
            "name": "Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "heavy-freezing-rain": {
            "name": "Heavy Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "mostly-clear-freezing-drizzle": {
            "name": "Mostly Clear, Freezing Drizzle",
            "icon": "wi-day-sleet",
        },
        "partly-cloudy-freezing-drizzle": {
            "name": "Partly Cloudy, Freezing Drizzle",
            "icon": "wi-day-sleet",
        },
        "mostly-cloudy-freezing-drizzle": {
            "name": "Mostly Cloudy, Freezing Drizzle",
            "icon": "wi-day-sleet",
        },
        "drizzle-freezing-drizzle": {
            "name": "Drizzle, Freezing Drizzle",
            "icon": "wi-day-sleet",
        },
        "light-rain-freezing-drizzle": {
            "name": "Light Rain, Freezing Drizzle",
            "icon": "wi-day-sleet",
        },
        "mostly-clear-light-freezing-rain": {
            "name": "Mostly Clear, Light Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "partly-cloudy-light-freezing-rain": {
            "name": "Partly Cloudy, Light Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "mostly-cloudy-light-freezing-rain": {
            "name": "Mostly Cloudy, Light Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "mostly-clear-freezing-rain": {
            "name": "Mostly Clear, Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "partly-cloudy-freezing-rain": {
            "name": "Partly Cloudy, Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "mostly-cloudy-freezing-rain": {
            "name": "Mostly Cloudy, Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "drizzle-freezing-rain": {
            "name": "Drizzle, Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "light-rain-freezing-rain": {
            "name": "Light Rain, Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "rain-freezing-rain": {
            "name": "Rain, Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "mostly-clear-heavy-freezing-rain": {
            "name": "Mostly Clear, Heavy Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "partly-cloudy-heavy-freezing-rain": {
            "name": "Partly Cloudy, Heavy Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "mostly-cloudy-heavy-freezing-rain": {
            "name": "Mostly Cloudy, Heavy Freezing Rain",
            "icon": "wi-day-sleet",
        },
        "light-ice-pellets": {
            "name": "Light Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "ice-pellets": {
            "name": "Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "heavy-ice-pellets": {
            "name": "Heavy Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "mostly-clear-light-ice-pellets": {
            "name": "Mostly Clear, Light Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "partly-cloudy-light-ice-pellets": {
            "name": "Partly Cloudy, Light Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "mostly-cloudy-light-ice-pellets": {
            "name": "Mostly Cloudy, Light Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "mostly-clear-ice-pellets": {
            "name": "Mostly Clear, Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "partly-cloudy-ice-pellets": {
            "name": "Partly Cloudy, Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "mostly-cloudy-ice-pellets": {
            "name": "Mostly Cloudy, Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "mostly-clear-heavy-ice-pellets": {
            "name": "Mostly Clear, Heavy Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "partly-cloudy-heavy-ice-pellets": {
            "name": "Partly Cloudy, Heavy Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "mostly-cloudy-heavy-ice-pellets": {
            "name": "Mostly Cloudy, Heavy Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "drizzle-ice-pellets": {
            "name": "Drizzle, Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "light-rain-ice-pellets": {
            "name": "Light Rain, Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "rain-ice-pellets": {
            "name": "Rain, Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "freezing-rain-ice-pellets": {
            "name": "Freezing Rain, Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "freezing-rain-heavy-ice-pellets": {
            "name": "Freezing Rain, Heavy Ice Pellets",
            "icon": "wi-day-sleet",
        },
        "thunderstorm": {
            "name": "Thunderstorm",
            "icon": "wi-day-lightning",
        },
        "mostly-clear-thunderstorm": {
            "name": "Mostly Clear, Thunderstorm",
            "icon": "wi-day-lightning",
        },
        "partly-cloudy-thunderstorm": {
            "name": "Partly Cloudy, Thunderstorm",
            "icon": "wi-day-lightning",
        },
        "mostly-cloudy-thunderstorm": {
            "name": "Mostly Cloudy, Thunderstorm",
            "icon": "wi-day-lightning",
        }
    }
}


def _load_test_data() -> Optional[Dict]:
    """
    Load test data from test_data.json if it exists.

    Returns:
        Dictionary containing test data or None if file doesn't exist
    """
    # Get the directory where this file is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_data_path = os.path.join(current_dir, 'assets', 'test_data.json')

    if os.path.exists(test_data_path):
        try:
            with open(test_data_path, 'r', encoding='utf-8') as f:
                print(f"Loading test data from {test_data_path}")
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading test data from {test_data_path}: {e}")
            return None
    return None


def _get_hourly_forecast(latitude: float, longitude: float, api_key: str, timezone: str = 'America/New_York') -> Optional[List[Dict]]:
    """
    Get hourly weather forecast for the next specified hours using Tomorrow.io API.
    If test_data.json exists, it will be used instead of making API requests.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        api_key: Tomorrow.io API key
        hours: Number of hours to forecast (default 48, max 120 for free tier)

    Returns:
        List of hourly forecast periods or None if error
    """
    # Check if test data exists and use it instead of API
    test_data = _load_test_data()
    if test_data and test_data.get('success') and 'hourly' in test_data:
        hourly_data = test_data.get('hourly', {})
        forecast = hourly_data.get('forecast', [])
        if forecast:
            print(f"Using test data for hourly forecast ({len(forecast)} hours)", flush=True)
            return forecast

    # Fall back to API if test data not available
    try:
        # Tomorrow.io Timelines API endpoint
        url = "https://api.tomorrow.io/v4/timelines"

        params = {
            'location': f"{latitude},{longitude}",
            'fields': [
                'temperature', 'weatherCode', 'uvIndex', 'precipitationProbability', 'precipitationType',
                'temperatureApparent', 'humidity', 'windSpeed', 'windDirection',
                'pressureSeaLevel', 'visibility', 'cloudCover'
            ],
            'units': 'imperial',
            'timesteps': ['1h'],
            'startTime': 'now',
            'endTime': 'nowPlus1d',
            'timezone': timezone,
            'apikey': api_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract hourly intervals from the timeline
        timelines = data.get('data', {}).get('timelines', [])
        if not timelines:
            print("No timeline data found in Tomorrow.io response")
            return None

        intervals = timelines[0].get('intervals', [])

        # Format the data for easier consumption
        formatted_forecast = []
        for interval in intervals:
            start_time = interval.get('startTime', '')
            values = interval.get('values', {})

            # Parse the ISO timestamp
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

            # Map weather code to description
            weather_code = values.get('weatherCode', 1000)
            weather_desc = _get_weather_description(weather_code)

            formatted_period = {
                'datetime': dt.isoformat(),
                'temperature': round(values.get('temperature', 0)),
                'temperature_unit': 'F',
                'feels_like': round(values.get('temperatureApparent', 0)),
                'humidity': values.get('humidity'),
                'wind_speed': f"{values.get('windSpeed', 0)} mph",
                'wind_direction': values.get('windDirection'),
                'short_forecast': weather_desc,
                'detailed_forecast': weather_desc,
                'precipitation_probability': round(values.get('precipitationProbability', 0)),
                'precipitation_type': _get_precipitation_type(values.get('precipitationType', 0)),
                'icon': _get_weather_icon(weather_code),
                'uv_index': values.get('uvIndex', 0),
                'pressure': values.get('pressureSeaLevel'),
                'visibility': values.get('visibility'),
                'clouds': values.get('cloudCover')
            }
            formatted_forecast.append(formatted_period)

        return formatted_forecast

    except requests.exceptions.RequestException as e:
        print(f"Error fetching hourly forecast: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Error parsing hourly forecast response: {e}")
        return None


def _get_weekly_forecast(latitude: float, longitude: float, api_key: str, timezone: str = 'America/New_York') -> Optional[List[Dict]]:
    """
    Get 5-day weather forecast with high/low temperatures, conditions, and UV index using Tomorrow.io API.
    If test_data.json exists, it will be used instead of making API requests.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        api_key: Tomorrow.io API key

    Returns:
        List of daily forecast periods or None if error
    """
    # Check if test data exists and use it instead of API
    test_data = _load_test_data()
    if test_data and test_data.get('success') and 'weekly' in test_data:
        weekly_data = test_data.get('weekly', {})
        forecast = weekly_data.get('forecast', [])
        if forecast:
            print(f"Using test data for weekly forecast ({len(forecast)} days)")
            return forecast

    # Fall back to API if test data not available
    try:
        # Tomorrow.io Timelines API endpoint
        url = "https://api.tomorrow.io/v4/timelines"
        params = {
            'location': f"{latitude},{longitude}",
            'fields': ','.join([
                'temperatureMax', 'temperatureMin', 'weatherCodeDay', 'uvIndex',
                'precipitationProbability', 'precipitationType',
                'temperatureApparentMax', 'temperatureApparentMin',
                'humidity', 'windSpeed', 'windDirection', 'pressureSeaLevel',
                'visibility', 'cloudCover', 'sunriseTime', 'sunsetTime'
            ]),
            'units': 'imperial',
            'timesteps': ['1d'],
            'startTime': 'now',
            'endTime': 'nowPlus5d',
            'dailyStartHour': 6,
            'timezone': timezone,
            'apikey': api_key
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract daily intervals from the timeline
        timelines = data.get('data', {}).get('timelines', [])
        if not timelines:
            print("No timeline data found in Tomorrow.io response")
            return None

        intervals = timelines[0].get('intervals', [])

        # Format the data for easier consumption
        daily_forecast = []
        for interval in intervals:
            start_time = interval.get('startTime', '')
            values = interval.get('values', {})

            # Parse the ISO timestamp
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

            # Map weather code to description (use weatherCodeDay for daily forecasts)
            weather_code = values.get('weatherCodeDay', values.get('weatherCode', 1000))
            weather_desc = _get_weather_description(weather_code)

            formatted_day = {
                'date': dt.isoformat(),
                'name': dt.strftime('%A'),  # Day name (Monday, Tuesday, etc.)
                'high_temp': round(values.get('temperatureMax', 0)),
                'low_temp': round(values.get('temperatureMin', 0)),
                'morning_temp': None,  # Not available in Tomorrow.io daily data
                'day_temp': round((values.get('temperatureMax', 0) + values.get('temperatureMin', 0)) / 2),
                'evening_temp': None,  # Not available in Tomorrow.io daily data
                'night_temp': None,  # Not available in Tomorrow.io daily data
                'feels_like_day': round(values.get('temperatureApparentMax', 0)),
                'feels_like_night': round(values.get('temperatureApparentMin', 0)),
                'day_forecast': weather_desc,
                'day_detailed': weather_desc,
                'day_icon': _get_weather_icon(weather_code),
                'precipitation_probability': round(values.get('precipitationProbability', 0)),
                'precipitation_type': _get_precipitation_type(values.get('precipitationType', 0)),
                'humidity': values.get('humidity'),
                'wind_speed': f"{values.get('windSpeed', 0)} mph",
                'wind_direction': values.get('windDirection'),
                'pressure': values.get('pressureSeaLevel'),
                'uv_index': values.get('uvIndex', 0),
                'clouds': values.get('cloudCover'),
                'sunrise': values.get('sunriseTime', ''),
                'sunset': values.get('sunsetTime', ''),
                'moonrise': None,  # Not available in Tomorrow.io API
                'moonset': None,  # Not available in Tomorrow.io API
                'moon_phase': None  # Not available in Tomorrow.io API
            }
            daily_forecast.append(formatted_day)

        return daily_forecast

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weekly forecast: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"Error parsing weekly forecast response: {e}")
        return None


def _get_weather_description(weather_code: int) -> Dict[str, str]:
    """
    Map Tomorrow.io weather codes to human-readable descriptions.

    Args:
        weather_code: Tomorrow.io weather code

    Returns:
        Dictionary with 'main' and 'description' keys
    """
    return weather_codes["slug_to_meta"].get(weather_codes["code_to_slug"].get(weather_code, ""), {
        "name": "Unknown",
        "icon": "wi-day-sunny",
    })["name"]


def _get_weather_icon(weather_code: int) -> str:
    """
    Map Tomorrow.io weather codes to weather icon URLs.
    Using OpenWeatherMap icons for consistency with existing UI.

    Args:
        weather_code: Tomorrow.io weather code

    Returns:
        URL to weather icon
    """
    # Map Tomorrow.io codes to OpenWeatherMap icon codes
    return weather_codes["slug_to_meta"].get(weather_codes["code_to_slug"].get(weather_code, ""), {
        "name": "Unknown",
        "icon": "wi-day-sunny",
    })["icon"]


def _get_precipitation_type(precip_type_code: int) -> str:
    """
    Map Tomorrow.io precipitation type codes to human-readable strings.

    Args:
        precip_type_code: Tomorrow.io precipitation type code

    Returns:
        Human-readable precipitation type
    """
    precip_types = {
        0: 'None',
        1: 'Rain',
        2: 'Snow',
        3: 'Freezing Rain',
        4: 'Ice Pellets'
    }

    return precip_types.get(precip_type_code, 'Unknown')


def render_weather_chart_bmp(lat: float, lon: float, api_key: str, note_text: str = None) -> Tuple[Optional[bytes], Dict]:
    """
    Fetch weather data and render the weather chart as BMP image bytes.

    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        api_key: Tomorrow.io API key
        note_text: Optional note text to display in the bottom-left sidebar area

    Returns:
        Tuple of (BMP image bytes or None if rendering failed, template context for SVG fallback)
    """
    from .svg_to_bmp import render_svg_to_bmp

    current_time = timezone.now().astimezone(EASTERN_TZ)

    # Get hourly forecast (24 hours)
    hourly_forecast = _get_hourly_forecast(lat, lon, api_key)
    if not hourly_forecast:
        return (None, {})

    # Get weekly forecast
    weekly_forecast = _get_weekly_forecast(lat, lon, api_key)

    # Find current temperature from first or second hourly forecast (whichever is closer to current time)
    current_temp = None
    if len(hourly_forecast) >= 2:
        try:
            dt1_str = hourly_forecast[0]['datetime']
            dt1_str_clean = dt1_str.replace('Z', '+00:00')
            dt1 = datetime.fromisoformat(dt1_str_clean)

            dt2_str = hourly_forecast[1]['datetime']
            dt2_str_clean = dt2_str.replace('Z', '+00:00')
            dt2 = datetime.fromisoformat(dt2_str_clean)

            diff1 = abs((dt1 - current_time).total_seconds())
            diff2 = abs((dt2 - current_time).total_seconds())

            if diff1 <= diff2:
                current_temp = hourly_forecast[0]['temperature']
            else:
                current_temp = hourly_forecast[1]['temperature']
        except Exception as e:
            logger.warning("Failed to parse forecast times for current temp: %s", e)
            current_temp = hourly_forecast[0].get('temperature')
    else:
        current_temp = hourly_forecast[0].get('temperature')

    current_date_str = current_time.strftime('%A, %B %d')
    current_weather_icon_svg = ''

    # Extract temperatures, UV index, precipitation probability, and times from forecast
    temperatures = [item['temperature'] for item in hourly_forecast]
    uv_indices = [item.get('uv_index', 0) for item in hourly_forecast]
    precipitation_probabilities = [item.get('precipitation_probability', 0) for item in hourly_forecast]
    datetimes = [item['datetime'] for item in hourly_forecast]

    # Parse datetime strings to extract hour labels
    hour_labels = []
    datetime_objects = []
    for dt_str in datetimes:
        try:
            dt_str_clean = dt_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(dt_str_clean)
            datetime_objects.append(dt)
            hour_12 = dt.hour % 12
            if hour_12 == 0:
                hour_12 = 12
            am_pm = 'AM' if dt.hour < 12 else 'PM'
            hour_labels.append(f"{hour_12} {am_pm}")
        except Exception as e:
            logger.warning("Failed to parse datetime %s: %s", dt_str, e)
            datetime_objects.append(None)
            hour_labels.append('')

    # Chart dimensions
    chart_width = 600
    total_height = 480
    sidebar_width = 200
    sidebar_height = total_height / 2
    total_width = sidebar_width + chart_width
    x_axis_label_height = 30
    hourly_chart_height = 230
    weekly_chart_height = 230
    chart_margin_y = total_height - hourly_chart_height - weekly_chart_height
    hourly_padding_width = 20
    plot_width = chart_width - 2 * hourly_padding_width
    plot_height = hourly_chart_height - x_axis_label_height

    x_axis_start = sidebar_width
    x_axis_end = sidebar_width + chart_width
    hourly_chart_offset_y = 0
    y_axis_end = hourly_chart_offset_y + plot_height

    # Calculate average temperature and center y-axis on it with 50-degree range
    avg_temp = sum(temperatures) / len(temperatures) if temperatures else 50
    temp_range = 50
    min_temp = avg_temp - 25
    max_temp = avg_temp + 25

    # Generate SVG chart path
    points = []
    temp_points = []
    for i, temp in enumerate(temperatures):
        x = sidebar_width + hourly_padding_width + (i / (len(temperatures) - 1)) * plot_width if len(temperatures) > 1 else sidebar_width + hourly_padding_width + plot_width / 2
        y = hourly_chart_offset_y + plot_height - ((temp - min_temp) / temp_range) * plot_height
        points.append(f"{x},{y}")
        temp_points.append({'x': x, 'y': y, 'temp': temp})

    path_data = f"M {points[0]} " + " ".join([f"L {point}" for point in points[1:]])

    min_temp_point = min(temp_points, key=lambda p: p['temp'])
    max_temp_point = max(temp_points, key=lambda p: p['temp'])

    min_temp_label = {
        'x': round(min_temp_point['x']),
        'y': round(min_temp_point['y'] - 8),
        'temp': int(round(min_temp_point['temp']))
    }
    max_temp_label = {
        'x': round(max_temp_point['x']),
        'y': round(max_temp_point['y'] - 8),
        'temp': int(round(max_temp_point['temp']))
    }

    # UV index shaded area
    uv_max = 11
    uv_min = 0
    uv_range = uv_max - uv_min
    uv_points = []
    uv_points_with_data = []
    for i, uv_index in enumerate(uv_indices):
        x = sidebar_width + hourly_padding_width + (i / (len(uv_indices) - 1)) * plot_width if len(uv_indices) > 1 else sidebar_width + hourly_padding_width + plot_width / 2
        y = hourly_chart_offset_y + plot_height - ((uv_index - uv_min) / uv_range) * plot_height
        uv_points.append(f"{x},{y}")
        uv_points_with_data.append({'x': x, 'y': y, 'uv_index': uv_index})

    uv_path_data = f"M {sidebar_width + hourly_padding_width},{y_axis_end} "
    uv_path_data += f"L {uv_points[0]} "
    uv_path_data += " ".join([f"L {point}" for point in uv_points[1:]])
    uv_path_data += f" L {x_axis_end},{y_axis_end} Z"

    peak_uv_point = max(uv_points_with_data, key=lambda p: p['uv_index'])
    peak_uv_label = {
        'x': round(peak_uv_point['x']),
        'y': round(peak_uv_point['y'] - 8),
        'uv_index': int(round(peak_uv_point['uv_index']))
    }

    # Precipitation probability
    precip_max = 100
    precip_min = 0
    precip_range = precip_max - precip_min
    has_precipitation = any(p > 0 for p in precipitation_probabilities)

    if has_precipitation:
        precip_points = []
        for i, precip_prob in enumerate(precipitation_probabilities):
            x = sidebar_width + hourly_padding_width + (i / (len(precipitation_probabilities) - 1)) * plot_width if len(precipitation_probabilities) > 1 else sidebar_width + hourly_padding_width + plot_width / 2
            y = hourly_chart_offset_y + plot_height - ((precip_prob - precip_min) / precip_range) * plot_height
            precip_points.append(f"{x},{y}")
        precip_path_data = f"M {precip_points[0]} " + " ".join([f"L {point}" for point in precip_points[1:]])
    else:
        precip_path_data = None

    # Grid lines
    num_grid_lines = 5
    grid_lines = []
    for i in range(num_grid_lines + 1):
        y_pos = hourly_chart_offset_y + (i / num_grid_lines) * plot_height
        grid_lines.append({'y_pos': y_pos})

    # Hour labels with x positions
    hour_labels_with_pos = []
    for i, (label, dt_obj) in enumerate(zip(hour_labels, datetime_objects)):
        if dt_obj is not None and dt_obj.hour % 3 == 0:
            x_pos = sidebar_width + hourly_padding_width + (i / (len(hour_labels) - 1)) * plot_width if len(hour_labels) > 1 else sidebar_width + hourly_padding_width + plot_width / 2
            hour_labels_with_pos.append({'label': label, 'x_pos': round(x_pos)})

    y_label_x = sidebar_width + hourly_padding_width - 10
    x_label_y = round(y_axis_end + 20)

    # Weekly forecast data
    weekly_chart_data = []
    weekly_plot_padding_x = 40
    weekly_plot_padding_y = 20
    weekly_plot_height = weekly_chart_height - x_axis_label_height - (2 * weekly_plot_padding_y)
    weekly_plot_width = chart_width - (2 * weekly_plot_padding_x)
    weekly_chart_offset_y = hourly_chart_height + weekly_plot_padding_y + chart_margin_y

    if weekly_forecast:
        all_temps = []
        for day in weekly_forecast:
            if day.get('low_temp') is not None:
                all_temps.append(day['low_temp'])
            if day.get('high_temp') is not None:
                all_temps.append(day['high_temp'])

        if all_temps:
            weekly_min_temp = min(all_temps)
            weekly_max_temp = max(all_temps)
            weekly_temp_range = weekly_max_temp - weekly_min_temp if weekly_max_temp != weekly_min_temp else 1
        else:
            weekly_min_temp = 0
            weekly_max_temp = 100
            weekly_temp_range = 100

        for i, day in enumerate(weekly_forecast):
            day_name = day.get('name', '')
            low_temp = day.get('low_temp')
            high_temp = day.get('high_temp')

            if low_temp is not None and high_temp is not None:
                x_pos = sidebar_width + weekly_plot_padding_x + (i / (len(weekly_forecast) - 1)) * weekly_plot_width if len(weekly_forecast) > 1 else sidebar_width + weekly_plot_padding_x + weekly_plot_width / 2
                low_y = weekly_chart_offset_y + weekly_plot_height - ((low_temp - weekly_min_temp) / weekly_temp_range) * weekly_plot_height
                high_y = weekly_chart_offset_y + weekly_plot_height - ((high_temp - weekly_min_temp) / weekly_temp_range) * weekly_plot_height
                pill_width = 24
                pill_half_width = pill_width / 2
                pill_height = abs(high_y - low_y)
                pill_x = x_pos - pill_half_width
                pill_y = min(low_y, high_y)
                pill_radius = pill_half_width

                weekly_chart_data.append({
                    'day_name': day_name,
                    'x_pos': round(x_pos),
                    'low_temp': int(round(low_temp)),
                    'high_temp': int(round(high_temp)),
                    'low_y': low_y,
                    'high_y': high_y,
                    'pill_x': pill_x,
                    'pill_y': pill_y,
                    'pill_width': pill_width,
                    'pill_height': pill_height,
                    'pill_radius': pill_radius,
                    'low_label_y': round(low_y + 20),
                    'high_label_y': round(high_y - 5),
                    'day_label_y': round(weekly_chart_offset_y + weekly_plot_height + (x_axis_label_height * 1.5)),
                })

    # Word-wrap note text for the bottom-left sidebar area
    note_lines = []
    if note_text:
        lines = textwrap.wrap(note_text, width=20)
        line_height = 20
        total_text_height = len(lines) * line_height
        # Vertically center in the bottom-left empty space (y ≈ 200 to 480)
        available_top = 200
        available_bottom = total_height
        start_y = available_top + (available_bottom - available_top - total_text_height) / 2
        for i, line in enumerate(lines):
            note_lines.append({
                'text': line,
                'y': round(start_y + i * line_height),
            })

    context = {
        'total_width': total_width,
        'chart_width': chart_width,
        'sidebar_width': sidebar_width,
        'sidebar_height': sidebar_height,
        'chart_height': total_height,
        'current_temp': int(round(current_temp)) if current_temp is not None else None,
        'current_date': current_date_str,
        'current_weather_icon_svg': current_weather_icon_svg,
        'padding': hourly_padding_width,
        'x_axis_start': x_axis_start,
        'x_axis_end': x_axis_end,
        'y_axis_end': y_axis_end,
        'y_label_x': y_label_x,
        'x_label_y': x_label_y,
        'grid_lines': grid_lines,
        'hour_labels': hour_labels_with_pos,
        'path_data': path_data,
        'min_temp_label': min_temp_label,
        'max_temp_label': max_temp_label,
        'uv_path_data': uv_path_data,
        'peak_uv_label': peak_uv_label,
        'precip_path_data': precip_path_data,
        'weekly_chart_data': weekly_chart_data,
        'weekly_chart_height': weekly_chart_height,
        'weekly_padding': weekly_plot_padding_x,
        'weekly_y_axis_end': weekly_chart_offset_y + weekly_plot_height + x_axis_label_height,
        'weekly_chart_offset_y': weekly_chart_offset_y,
        'x_axis_label_height': x_axis_label_height,
        'note_lines': note_lines,
    }

    bmp_bytes = render_svg_to_bmp('tablet/weather_chart.svgt', context, width=int(total_width), height=int(total_height))
    return (bmp_bytes, context)

