from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import openrouteservice
import googlemaps
import webbrowser
import os
import json
import sys
import folium
import polyline
import datetime
import copy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils import settings

# Constants
PATH = os.path.dirname(os.path.abspath(__file__))
OPENROUTESERVICE_MODES = ["foot-walking", "cycling-road", ""]
GMAPS_MODES = ["walking", "bicycling", "transit", "driving"]


def address_to_coordinates(address: str) -> tuple:
    """Takes an address and returns its coordinates.

    Args:
        address (str): address.

    Returns:
        tuple: (lat, lon)
    """
    loc = Nominatim(user_agent="Geopy Library")
    getLoc = loc.geocode(address)
    lat, lon = getLoc.latitude, getLoc.longitude

    return lat, lon

def get_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float, profile: str = "foot-walking"):
    
    client = openrouteservice.Client(key=settings.get_parameter("API_KEY_OPENROUTESERVICE"))

    coordinates = [[start_lon, start_lat], [end_lon, end_lat]]

    route = client.directions(
        coordinates=coordinates,
        profile=profile,
        format='geojson',
        options={"avoid_features": ["steps"]},
        validate=False,
    )

    return route

def get_time_distance_openrouteservice(route: json):
    """Uses the response from the Openrouteservice API to extract the duration and the distance of the route.

    Args:
        route (json): API response.
    """

    distance = route["features"][0]["properties"]["summary"]["distance"]
    duration = route["features"][0]["properties"]["summary"]["duration"]

    return distance, duration

def get_route_gmaps(start_lat: float, start_lon: float, end_lat: float, end_lon: float, arrival_time: datetime = None, transit: str = "walking"):
    """Computes the full route form the start point to the end point, which are coordinates. 
    If the argument 'arrival_time' is entered, it has to be a datetime object, and the route returned will arrive at this specific time.
    

    Args:
        start_lat (float): starting point latitude.
        start_lon (float): starting point longitude.
        end_lat (float): ending point latitude.
        end_lon (float): ending point longitude.
        arrival_time (datetime, optional): if not None, specifies the arrical time when computing the route. Defaults to None.
        transit (str, optional): Mode of transit. Values: "walking", "bicycling", "transit", "driving". Defaults to "walking".

    Returns:
        json: full detailled route.
    """
    gmaps = googlemaps.Client(key=settings.get_parameter("API_KEY_GOOGLEMAPS"))

    origin = f"{start_lat},{start_lon}"
    destination = f"{end_lat},{end_lon}"
    
    if arrival_time:
        
        dir = gmaps.directions(
            origin = origin,
            destination = destination,
            mode= transit,
            arrival_time = arrival_time)
    else:
        
        dir = gmaps.directions(
            origin = origin,
            destination = destination,
            mode= transit)
    
    return dir

def get_route_gmaps_address(start_address: str, end_address: str, arrival_time: datetime = None, transit: str = "walking") -> json:
    """Get the route between two addresses. 

    Args:
        start_address (str): starting point address.
        end_address (str): ending point address.
        arrival_time (datetime, optional): if not None, specifies the arrical time when computing the route. Defaults to None.
        transit (str, optional): Mode of transit. Values: "walking", "bicycling", "transit", "driving". Defaults to "walking".

    Returns:
        json: full detailled route.
    """
    start_lat, start_lon = address_to_coordinates(start_address)
    end_lat, end_lon = address_to_coordinates(end_address)

    route = get_route_gmaps(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        arrival_time=arrival_time,
        transit=transit
        )

    return route


def display_route_map(route: json, open_web = None):
    """Given a route, it displays the path on a map.

    Args:
        route (json): full detailled route.
        open_web (bool, optional): if True, it displays the map on a web page (for terminal use). Defaults to None.

    Returns:
        mymap: map (for notebooks)
    """
    start_coords = [route[0]["legs"][0]["start_location"]["lat"], route[0]["legs"][0]["start_location"]["lng"]]
    start_address = route[0]["legs"][0]["start_address"]
    end_coords = [route[0]["legs"][0]["end_location"]["lat"], route[0]["legs"][0]["end_location"]["lng"]]
    end_address = route[0]["legs"][0]["end_address"]

    # Create a map centered around the starting point
    mymap = folium.Map(location=start_coords, zoom_start=15)
    
    folium.TileLayer('CartoDB dark_matter').add_to(mymap)
    folium.TileLayer('CartoDB positron').add_to(mymap)

    # Adding a layer control element
    folium.LayerControl().add_to(mymap)

    overview_polyline = route[0]["overview_polyline"]["points"]
    decoded_polyline = polyline.decode(overview_polyline)

    # Add the route to the map
    folium.PolyLine(locations=decoded_polyline, color='blue', weight=5).add_to(mymap)
    folium.Marker(location=start_coords, popup=start_address).add_to(mymap)
    folium.Marker(location=end_coords, popup=end_address).add_to(mymap)

    file_path = "Route/Data/route_map.html"

    mymap.save(file_path)

    if open_web:
        webbrowser.open('file://' + os.path.realpath(file_path))

    return mymap


def get_time_distance(route: json):
    
    trip_duration = route[0]["legs"][0]["duration"]["text"] # in seconds
    trip_distance = route[0]["legs"][0]["distance"]["text"] # in meters
    
    try:
        departure_time = route[0]["legs"][0]["departure_time"]["value"] # in seconds
    except:
        departure_time = None
    
    return departure_time, trip_duration, trip_distance



def get_transport_details(route: json) -> list:
    """From the dictionnary of the full route, it extracts only the different steps of the route that requires public transport usage. Then, selects some relevant information.

    Args:
        route (json): full detailled route.

    Returns:
        list: returns a list of dict, that contains the info of each step. 
        ex: [
        {
            "departure_stop": "Ouchy\u2013Olympique",
            "departure_time": 1724487000,
            "arrival_stop": "Lausanne-Flon",
            "arrival_time": 1724487420,
            "nb_stops": 5,
            "transport": "m2"
        },
        {
            "departure_stop": "Lausanne-Flon",
            "departure_time": 1724487600,
            "arrival_stop": "EPFL",
            "arrival_time": 1724488380,
            "nb_stops": 9,
            "transport": "m1"
        }
        ]
    """

    transport_details_full = route[0]["legs"]
    transport_details = transport_details_full[0]["steps"]
    
    try:
        departure_time_route = transport_details_full[0]["departure_time"]["value"]
        arrival_time_route = transport_details_full[0]["arrival_time"]["value"]
    except:
        departure_time_route, arrival_time_route = None, None

    transit_details = []

    for step in range(len(transport_details)):
        if "transit_details" in list(transport_details[step].keys()):

            details = transport_details[step]["transit_details"]
            departure_stop = details["departure_stop"]["name"]
            departure_time = details["departure_time"]["value"] # in sec
            arrival_stop = details["arrival_stop"]["name"]
            arrival_time = details["arrival_time"]["value"] # in sec
            nb_stops = details["num_stops"]
            transport = details["line"]["short_name"]
            
            step_details = {
                "departure_stop": departure_stop,
                "departure_time": departure_time,
                "arrival_stop": arrival_stop,
                "arrival_time": arrival_time,
                "nb_stops": nb_stops,
                "transport": transport
            }

            transit_details.append(copy.deepcopy(step_details))

    return departure_time_route, arrival_time_route, transit_details

def string_public_transport(transit_details: list) -> list:
    """Takes the transit details of the route and returns a list of the string for each step.

    Args:
        transit_details (list): each element is a dictionary of the details of each step of the transports.

    Returns:
        list: list of the strings for each step.
    """

    transit_steps = []

    for transit in transit_details:
        duration = datetime.timedelta(seconds=(transit["arrival_time"] - transit["departure_time"]))
        transit_step = f" - Take the {transit['transport']} at {transit['departure_stop']} at {convert_epoch_datetime(transit['departure_time']).strftime('%Hh%M')} for {transit['nb_stops']} stops until {transit['arrival_stop']} ({duration.seconds//60}min)."
        transit_steps.append(transit_step)
    
    return transit_steps


def string_car(route: json) -> str:
    """En theorie: si on prend la voiture, alors on s'en tape de tout: 
    - prendre simplement l'heure de départ et l'heure d'arrivée, peut être les km? mais pas besoin de plus."""
    distance = route[0]["legs"][0]["distance"]["text"]
    duration = route[0]["legs"][0]["duration"]["text"]
    out_string = f"🚘 The {distance} should take about {duration}."
    
    return out_string


def check_public_transport(route: json) -> bool:
    """Check if the route requires the use of public transports.

    Args:
        route (json): full detailled route.

    Returns:
        bool: True if the route requires the use of public transports. False otherwise.
    """

    transport_details = route[0]["legs"][0]["steps"]
    
    check = False

    for step in range(len(transport_details)):
        if "transit_details" in list(transport_details[step].keys()):
            check = True
    
    return check


def check_car(route: json) -> bool:
    """Check if the route is done by car.

    Args:
        route (json): full detailled route.

    Returns:
        bool: True if travel by car. False otherwise.
    """

    if route[0]["legs"][0]["steps"][-1]["travel_mode"] == "DRIVING":
        check = True
    else:
        check = False

    return check
    

def export_string_route(route: json) -> str:
    
    # Check if public transport is used
    public_transport = check_public_transport(route = route)

    # Check if car is used
    car = check_car(route = route)

    if car:
        output = string_car(route = route)

    elif public_transport:
        departure_time_route, arrival_time_route, transit_details = get_transport_details(route=route)
        transit_steps_string = string_public_transport(transit_details=transit_details)
        
        # Example value of transit_steps_string: 
        # "Take the m2 at Ouchy–Olympique at 10h10 for 5 stops until Lausanne-Flon (7min).
        # Take the m1 at Lausanne-Flon at 10h20 for 9 stops until EPFL (13min)."
        departure_time_route = convert_epoch_datetime(departure_time_route).strftime('%Hh%M')
        arrival_time_route = convert_epoch_datetime(arrival_time_route).strftime('%Hh%M')
        output = f"🚌 Leave at {departure_time_route} by foot.\n" + "\n".join(transit_steps_string) + f"\n🎯 Arrival at {arrival_time_route}."

    else:
        departure_time, trip_duration, trip_distance = get_time_distance(route = route)
        if departure_time:
            output = f"🚶‍♂️‍➡️ Leave at {convert_epoch_datetime(departure_time).strftime('%Hh%M')} by foot and walk {trip_distance} ({trip_duration}min)."
        else:
            output = f"🚶‍♂️‍➡️ Walk {trip_distance} for about {trip_duration}."

    return output

# && utils function &&
def convert_epoch_datetime(epoch: int) -> datetime:
    return datetime.datetime.fromtimestamp(epoch)


if __name__ == "__main__":

    address1 = "Ouchy Olympique, Lausanne"
    address2 = "Rolex Learning Center, Ecublens"

    # 1. Get the coordinates using the adress
    lat1, lon1 = address_to_coordinates(address=address1)
    lat2, lon2 = address_to_coordinates(address=address2)
    print(address1, f"Lat, Lon: ({lat1}, {lon1})", sep = "\n")
    print(address2, f"Lat, Lon: ({lat2}, {lon2})", "", sep = "\n")

    # # 2. Get route between two points using Openrouteservice api
    # route = get_route(lat1, lon1, lat2, lon2)
    # print(json.dumps(route, indent=4), "", sep = "\n") # json.dump: better display

    # 3.1 Get route between two points using Googlemaps api
    # arrival_time = datetime.datetime.now() + timedelta(hours = 2)
    # route_gmaps = get_route_gmaps(lat1, lon1, lat2, lon2, arrival_time=arrival_time, transit="transit")
    # print(json.dumps(route_gmaps, indent=4), "", sep = "\n")

    # 3.2 Get route between two points using Googlemaps api, with addresses (and save the result in Data/route.json)
    # route_gmaps_address = get_route_gmaps_address(address1, address2, arrival_time=arrival_time, transit="transit")

    # To avoid multiple requests to googlemaps api, use example
    with open(PATH + "/Data/route_transit.json", 'r') as json_file:
        route = json.load(json_file)

    # # 4. Display the route created with googlemaps api on a map 
    # map = display_route_map(route = route, open_web= True)

    # # 5. Get the duration and distance of the trip
    # departure_time, trip_duration, trip_distance = get_time_distance(route = route)
    # print(departure_time, trip_duration, trip_distance, "", sep="\n")

    # # 6. Get the details of the route in the case it takes public transports, and returns the steps
    # departure_time_route, arrival_time_route, transit_details = get_transport_details(route = route)
    # print(departure_time_route, arrival_time_route, transit_details, "", sep = "\n")

    # # 7. Print all relevant information from the json. It determines what type of transport is being used, and adapt the output
    information = export_string_route(route = route)
    print(information, "", sep = "\n")

    # ======================================================
    # address1 = "Ouchy Olympique, Lausanne"
    # address2 = "Rolex Learning Center, Ecublens"

    # # 1. Get the coordinates using the adress
    # lat1, lon1 = address_to_coordinates(address=address1)
    # lat2, lon2 = address_to_coordinates(address=address2)
    # print(address1, f"Lat, Lon: ({lat1}, {lon1})", sep = "\n")
    # print(address2, f"Lat, Lon: ({lat2}, {lon2})", "", sep = "\n")

    # # 2. Get route between two points using Openrouteservice api
    # route = get_route(lat1, lon1, lat2, lon2)
    # # print(json.dumps(route, indent=4), "", sep = "\n") # json.dump: better display

    # distance = route["features"][0]["properties"]["summary"]["distance"]
    # duration = route["features"][0]["properties"]["summary"]["duration"]

    # print(distance, duration)