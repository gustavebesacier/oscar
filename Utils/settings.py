import json
import os

PATH_SETTINGS = os.path.dirname(os.path.abspath(__file__)) + '/settings.json'

def get_parameter(param:str) -> str:
    
    if not os.path.exists(PATH_SETTINGS):
        raise FileNotFoundError(f"{PATH_SETTINGS!r} file not found")
    
    with open(PATH_SETTINGS, 'r') as f:
        data = json.load(f)
    
    if str(param) in list(data.keys()):
        return data[str(param)]
    else:
        raise KeyError(f"[{__name__}] Parameter {param!r} not found in 'settings.json' file")
    
if __name__ == "__main__":
    print(get_parameter("URL_OPEN_METEO"))