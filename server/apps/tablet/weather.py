import requests
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta



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


def get_hourly_forecast(latitude: float, longitude: float, api_key: str, timezone: str = 'America/New_York') -> Optional[List[Dict]]:
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


def get_weekly_forecast(latitude: float, longitude: float, api_key: str, timezone: str = 'America/New_York') -> Optional[List[Dict]]:
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

