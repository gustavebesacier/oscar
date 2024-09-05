# Oscar
Oscar is a Python-based virtual assistant designed to simplify and automate information gathering from various sources.

## 🎯Current Features
Currently, it handles operations such as:
- Retrieving real-time data of nearby public transport
- Providing information on upcoming events
- Suggesting departure times to ensure timely arrival for calendar events
- Offering a weather summary for the end of the day
More functions are currently in development.


## 👷 Setup
Several components need to be set up.


### 🔐 API Keys and Credentials
#### Google Calendar API Credentials
Follow the steps outlined on the [Getting started page](https://google-calendar-simple-api.readthedocs.io/en/latest/getting_started.html) of the ```gcsa``` API. Obtain the ```credential.json``` file and save it in the [Calendar](Calendar) folder. 

#### Google Maps API Key
Follow the instructions on the [Get Started with Google Maps Platform](https://developers.google.com/maps/get-started). Once ready, save the API key in the [settings.json](Utils/settings.json) file, under ```API_KEY_GOOGLEMAPS```.

#### Openrouteservice API Key
Obtain your Openrouteservice API key from the [openrouteservice.org](https://openrouteservice.org) website and save it in [settings.json](Utils/settings.json)file, under ```API_KEY_OPENROUTESERVICE```.

#### Create a Telegram Bot
Follow the instructions in the Telegram [BotFather](https://core.telegram.org/bots/tutorial) guide to create your bot. Then, get the bot token and save it in the [settings.json](Utils/settings.json) file, under ```BOT_TOKEN```.

### 🤖 Getting Users' Telegram IDs
You will need to specify each user who will use Oscar. For each user, create an entry in [settings.json](Utils/settings.json) like this: 

```json
"telegram_user_id:":{
    "ID": "telegram_user_id",
    "COORDINATES": {
        "LAT": "0.00000",
        "LON": "0.00000",
    },
    "STOP": "closest_transport_stop", 
        "CALENDARS": {
            "calendar_id_1@import.calendar.google.com": 0, 
            "calendar_id_2@import.calendar.google.com": 0, 
            "calendar_id_3@import.calendar.google.com": 0
        }
}
```

### 🔧 Libraries
Install the necessary libraries, which are listed in the [requirements.txt](requirements.txt) file.

## 📫 Usage
All communication with Oscar is done via Telegram and requires the program to be running on a computer (or preferably, on a server). Run the [Oscar.py](Oscar.py) file and then interact through the Telegram chat.


### ⌨️ Commands
Communication with Oscar is simple. Send keywords via chat to trigger its features. The keywords are:

- ```weather```: Provides the weather summary for the day
- ```calendar```: Displays the first event of the next day, ways to arrive on time, and recommended departure times
- ```calendar list```: Shows a list of upcoming calendar events
- ```transport```: Provides the next departures from the closest public transport stop


### 📆 Google Calendar usage
For each calendar you want Oscar to access, either create it using the Google account that hosts the project or share external calendars with that account. For each calendar, add the ```calendar_id``` in [settings.json](Utils/settings.json) as the key of the ```CALENDARS``` dictionary. The associated value should be the time offset for each event's start time (this may be necessary for iCloud calendars and others).

## Note
The project is still under development and may have issues or bugs. 🤓