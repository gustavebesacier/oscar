from datetime import datetime

import requests
import json
import sys
import os

# Needed to import Utils/setting.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils import settings

# print(os.path.dirname(os.path.abspath(__file__)))


def get_json_file(station:str, limit:int=5, base_url=settings.get_parameter("URL_SBB")) -> json:
    """Requests the SBB API to get informations about the next departures from the specified stop.

    Args:
        station (str): station stop of interest.
        limit (int, optional): max number of departures to return. Defaults to 5.
        base_url (_type_, optional): API enter point. Defaults to settings.get_parameter("URL_SBB").

    Returns:
        json: SBB API request result.
    """

    url = f"{base_url}station={station}&limit={str(limit)}"
    r = requests.get(url)
    json_file = r.json()

    return json_file

def get_coordinates(request):
    """Uses the transport API to get the station coodrinates. 

    Args:
        request (json): json file, raw form the request to the API

    Returns:
        lat, lon: coordinates.
    """
    lat, lon = request["station"]["coordinate"]["x"], request["station"]["coordinate"]["y"]
    
    return lat, lon


def get_next_departures(request: json):
    """Get some information about the next departures at a given station.
    Returns a list of dictionnary with the elements:
    ['starting_stop', 'starting_time', 'starting_time_format', 'delay', 'arrival_stop', 'transport_type']
    """

    departures = request["stationboard"]

    list_departures = list()

    for depart in departures:

        starting_stop = depart["stop"]["station"]["name"]
        starting_time = datetime.strptime(depart["stop"]["departure"], "%Y-%m-%dT%H:%M:%S%z")
        delay = depart["stop"]["delay"]
        arrival_stop = depart["to"]
        transport_type = depart["number"]

        starting_time_format = starting_time.strftime("%H:%M")

        dic_res = {
            "starting_stop": starting_stop,
            "starting_time": starting_time,
            "starting_time_format": starting_time_format,
            "delay": delay,
            "arrival_stop": arrival_stop,
            "transport_type": transport_type
            }
        list_departures.append(dic_res.copy())

    return list_departures

def export_string_sbb(station:str, limit:int=5, base_url=settings.get_parameter("URL_SBB")):

    json_file = get_json_file(station=station, limit=limit, base_url=base_url)

    list_departures = get_next_departures(request=json_file)
    start = json_file["station"]["name"]

    out = f"🚉 Soon leaving from from {start}:\n"
    departure = [" - {} to {}: {} (+{}min).".format(list_departures[i]["transport_type"], list_departures[i]["arrival_stop"], list_departures[i]["starting_time_format"], list_departures[i]["delay"]) for i in range(len(list_departures))]

    out = out + "\n".join(departure)

    return out


if __name__ == "__main__":
    
    json_file = get_json_file("EPFL")

    lat, lon = get_coordinates(json_file)


    res = get_next_departures(json_file)[1].keys()

    print(export_string_sbb("figuiers"))
    
    