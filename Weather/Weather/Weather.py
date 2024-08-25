import openmeteo_requests
import requests_cache
import json
import os
import sys
import pandas as pd
from retry_requests import retry

# Needed to import Utils/setting.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils import settings

TODAY = pd.Timestamp('today').normalize() #+ datetime.timedelta(days=1)


def get_data(id_user:str =None):
    """Requests the Open-Meteo API to extract informations, based on the user's location. 
    The location is specified in setting.json under [_userid_]["COORDINATES"], then LAT and LON.
    Note: most of the code of this function comes directely from the Open-Meteo API website.

    Args:
        id_user (str, optional): user id from the setting file. Defaults to None.

    Returns:
        tuple: returns a tuple, each contains a dataframe, respectively for hourly and daily info
    """
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Get the user's coordinates
    if id_user:
        # lat, lon = settings.get_parameter(id_user)["COORDINATES"]["LAT"], settings.get_parameter(id_user)["COORDINATES"]["LON"]
        try:
            lat, lon = settings.get_parameter(id_user)["COORDINATES"]["LAT"], settings.get_parameter(id_user)["COORDINATES"]["LON"]
        except:
            id_user = settings.get_parameter("ID_MAIN")
            lat, lon = settings.get_parameter(id_user)["COORDINATES"]["LAT"], settings.get_parameter(id_user)["COORDINATES"]["LON"]

    else:
        id_user = settings.get_parameter("ID_MAIN")
        lat, lon = settings.get_parameter(id_user)["COORDINATES"]["LAT"], settings.get_parameter(id_user)["COORDINATES"]["LON"]
    
    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = settings.get_parameter("URL_OPEN_METEO")
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "apparent_temperature", "precipitation", "weather_code", "cloud_cover", "wind_speed_10m"],
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "weather_code", "cloud_cover", "uv_index"],
        "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "uv_index_max", "precipitation_sum", "precipitation_hours"],
        "timezone": "Europe/Berlin",
        "forecast_days": 4
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    lat = response.Latitude()
    lon = response.Longitude()

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_weather_code = hourly.Variables(3).ValuesAsNumpy()
    hourly_cloud_cover = hourly.Variables(4).ValuesAsNumpy()
    hourly_uv_index = hourly.Variables(5).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["weather_code"] = hourly_weather_code
    hourly_data["cloud_cover"] = hourly_cloud_cover
    hourly_data["uv_index"] = hourly_uv_index

    hourly_dataframe = pd.DataFrame(data = hourly_data)

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_max = daily.Variables(1).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(2).ValuesAsNumpy()
    daily_uv_index_max = daily.Variables(3).ValuesAsNumpy()
    daily_precipitation_sum = daily.Variables(4).ValuesAsNumpy()
    daily_precipitation_hours = daily.Variables(5).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}
    daily_data["weather_code"] = daily_weather_code
    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min
    daily_data["uv_index_max"] = daily_uv_index_max
    daily_data["precipitation_sum"] = daily_precipitation_sum
    daily_data["precipitation_hours"] = daily_precipitation_hours

    daily_dataframe = pd.DataFrame(data = daily_data)

    return (hourly_dataframe, daily_dataframe)


def find_precipitation(data_hourly:pd.DataFrame):
    "Returns the hours in the current day at which there will be precipitations, the amount in mm and the weather code."

    # Perform manipulations on the dataframe
    filtered_df = data_hourly[data_hourly['date'].dt.day == TODAY.day]
    filtered_df = filtered_df[filtered_df['precipitation']!= 0]
    hours = filtered_df['date'].dt.hour.tolist()
    precipitation = filtered_df['precipitation'].tolist()
    code = filtered_df['weather_code'].tolist()

    # Formatting the values
    precipitation = list(map(lambda x: round(x, 2), precipitation))
    code = list(map(lambda x: get_weather_code(int(x)), code))

    return hours, precipitation, code

def summarize(id_user:str =None):
    """Extracts relevant information about the weather, relevant for the specified id_user.

    Args:
        id_user (str, optional): user id. Defaults to None.

    Returns:
        weather_code: identifier of the overall weather.
        min_temp: minimum temperature. 
        max_temp: maximum temperature.
        precip: tuple or float. If tuple: ([hours of precipitation], [hourly precipitations in mm], [hourly weather code _str_])
        precip_total: sum of all precipitations.

    """
    hourly, daily = get_data(id_user=id_user)
    
    current_day_infos = daily[daily['date'].dt.day == TODAY.day]

    weather_code, min_temp, max_temp = current_day_infos.weather_code.iloc[0], current_day_infos.temperature_2m_min.iloc[0], current_day_infos.temperature_2m_max.iloc[0]
    
    # Now expore the precipitations: 
    hours, precipitation, code = find_precipitation(hourly) # returns 3 lists, for each hours of precipitations, the amount and the weather code

    # Check if the lists are empty
    if len(hours) == 0:
        precip = 0
        precip_total = 0

    else:
        precip_total = sum(precipitation)
        precip = (hours, precipitation.copy(), code)

    weather_code = get_weather_code(int(weather_code))
    
    return weather_code, min_temp, max_temp, precip, precip_total


def string_to_export(weather_code, min_temp, max_temp, precip, precip_total) -> str:
    """Uses all relevant information and formats it into a string to export.

    Args:
        weather_code (str): identifier of the overall weather.
        min_temp (float): minimum temperature. 
        max_temp (float): maximum temperature.
        precip (float or tuple): tuple or float. If tuple: ([hours of precipitation], [hourly precipitations in mm], [hourly weather code _str_])
        precip_total (float): sum of all precipitations.
 
    Returns:
        str: information formatted in a string.
    """

    min_temp = str(round(min_temp, 2))
    max_temp = str(round(max_temp, 2))

    text_out = f"Overall: {weather_code}\n❄️ Min temp: {min_temp}°C\n🔥 Max temp: {max_temp}°C"

    if precip_total > 0:

        time, prec = handle_hourly_precipitations(list_hours=precip[0], list_precip=precip[1])

        output_time = []
        output_precip = [] 

        for i in range(len(time)):
            if len(time[i]) > 1: # precipitation during some hours, consecutive
                time_str = f"{int(time[i][0])}h - {int(time[i][-1])}h"
                prec_str = sum(prec[i])
                output_time.append(time_str)
                output_precip.append(prec_str)
            
            else: # precipitation during 1 hour only
                time_str = f"At {time[i]}h"
                prec_str = prec[i]
                output_time.append(time_str)
                output_precip.append(prec_str)

        intermediary_string = "\n - ".join([str(output_time[i])+ ": " + str(output_precip[i]) + "mm." for i in range(len(output_precip))])
        precip_string = f"\n☔️ Precipitations: \n - {intermediary_string}"
        
    else:
        precip_string = f"\n☔️ Precipitation: {precip}mm."

    text_out = text_out + precip_string

    return text_out
    

def order_list_int(numbers:list):
    """Returns list of list containing consecutive integers.
    [24, 19, 25, 14, 15, 17, 18, 27, 26, 23, 16] -> [[14, 15, 16, 17, 18, 19], [23, 24, 25, 26, 27]]
    [24, 25, 27, 26, 23, 16] -> [[16], [23, 24, 25, 26, 27]]"""

    numbers = list(map(lambda x: float(x), numbers))
    
    numbers = sorted(numbers)
    result = []
    temp = [numbers[0]]
    for i in range(1, len(numbers)):
        if numbers[i] - numbers[i-1] == 1:
            temp.append(numbers[i])
        else:
            result.append(temp)
            temp = [numbers[i]]
    result.append(temp)

    return result

def handle_hourly_precipitations(list_hours:list, list_precip:list):
    """ Takes the list of hours of precipitations, and list of hourly amount of precipitation. Creates sublists of consecutive hours, and the corresponding sublists of precipitation.
    Entries: 
    list_hours = [0.0, 1.0, 2.0, 19.0, 20.0, 21.0, 22.0, 23.0]
    list_precip= [0.4, 2.9, 0.6, 1.6, 4.4, 4.0, 3.4, 1.2]

    Output:
    ([[0.0, 1.0, 2.0], [19.0, 20.0, 21.0, 22.0, 23.0]], [[0.4, 2.9, 0.6], [1.6, 4.4, 4.0, 3.4, 1.2]])
"""

    # Consecutive precipitation hours
    sub_lists_hours = order_list_int(list_hours)

    sub_lists_mm = list()

    # Associate the precipitations
    for consecutive in sub_lists_hours:
        sub_lists_mm_round = [list_precip[list_hours.index(x)] for x in consecutive]
        sub_lists_mm.append(sub_lists_mm_round)

    return sub_lists_hours, sub_lists_mm

def get_weather_code(code:int) -> str:
    """Function that takes as input the weather code (int) and uses the table in *weather_code.json* to translate it."""

    path_file = os.path.dirname(os.path.abspath(__file__)) + "/weather_code.json"

    with open(path_file, "r") as f:
        data = json.load(f)
    
    try:
        weather_code = data[str(code)]["day"]["description"]
    except:
        weather_code = "None"

    return weather_code

if __name__ == "__main__":

    ID_USER = settings.get_parameter("ID_MAIN")

    # 1. Get the weather data using user's id
    get_data(ID_USER)

    # 2. Get relevant informations about the weather
    weather_code, min_temp, max_temp, precip, precip_total = summarize(ID_USER)
    print(weather_code, min_temp, max_temp, precip, precip_total, "", sep = "\n")

    # 3. Export the information extracted before in a string
    print(string_to_export(weather_code, min_temp, max_temp, precip, precip_total), "", sep="\n")

    # (4. Convert weather code)
    print(get_weather_code("1"))