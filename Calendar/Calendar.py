from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event
from datetime import timedelta, datetime

import os
import sys
import copy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils import settings

CREDENTIAL_PATH = os.path.dirname(os.path.abspath(__file__)) + "/credential.json"
TODAY = datetime.now() + timedelta(days=0)
# ID = "7169943565"


def get_calendars_user(user_id: str) -> dict:
    """Goes to the setting file and returns all the calendars associated to the user id and their time offset values.
    Args:
        user_id (str): user id (telegram identifier)

    Returns:
        dict: the key is the calendar id, and the value is the tine offset.
    """
    try:
        calendars_user = settings.get_parameter(user_id)["CALENDARS"]
    except:
        raise ValueError(f"User {user_id!r} could not be find in the setting file.")

    return calendars_user

def check_existence(calendar_ID: str) -> bool:
    """Make sure the requested calendar IDs (from the setting file) is indeed available."""
    
    list_calendars_id = settings.get_parameter(calendar_ID)["CALENDARS"] # All calendar id specified by the user in the setting file

    gc = GoogleCalendar(credentials_path=CREDENTIAL_PATH) 

    match = [calendar for calendar in list_calendars_id if calendar in [elem.id for elem in gc.get_calendar_list()]] # Match
    fails = [calendar for calendar in list_calendars_id if calendar not in match]

    if (len(match) == len(list_calendars_id)) and (len(fails) == 0):
        return True
    else:
        return False

def get_all_events(calendars_user: dict, credential_path: str=CREDENTIAL_PATH):

    all_events = {}
    
    for calendar in list(calendars_user.keys()):
        gc = GoogleCalendar(default_calendar=calendar, credentials_path=credential_path)
        events = [event for event in gc]
        all_events[calendar] = events

    return all_events

def offset_time(calendars_user: dict, calendar_events: dict) -> dict:
    """Takes the events extracted from the calendar and adjusts the datetime as some are not correctly exported (from iCloud).

    Args:
        calendars_user (dict): from the settings. Dict: key is the calendar id; calue is the time offset.
        calendar_events (dict): dict. Key is the calendar id, value is the list of the events.

    Returns:
        dict: same object as calendar_events, but times of the events are offset.
    """

    levent = copy.deepcopy(calendar_events)

    for calendar in levent:
        offset = calendars_user[calendar]
        if offset != 0:
            for i in levent[calendar]:
                i.start = i.start + timedelta(hours = offset)
                i.end = i.end + timedelta(hours = offset)

    return levent


def get_list_events_time(calendar_events: dict) -> dict:
    """Given a dict of calendars, returns it with events ordered by starting time."""
    
    for calendar in calendar_events:
        list_events_raw = copy.deepcopy(calendar_events[calendar])
        list_event_ordered = sorted(list_events_raw, key=lambda elem: elem.start)
        calendar_events_offset[calendar] = copy.deepcopy(list_event_ordered)

    return calendar_events_offset


def get_events_tomorrow(calendar_events: dict, days_forward: int= 1) -> dict:    
    """Only keeps the events that will occur the next day (or for a later day).

    Args:
        calendar_events (dict): dict. Key is the calendar id, value is the list of the events.
        days_forward (int, optional): number of day after today to select the events from. Defaults to 1 (tomorrow).

    Returns:
        dict: dict. Key is the calendar id, value is the list of the events.
    """
    calendar_events_tomorrow = {}

    for cal in calendar_events:
        tomorrow = [copy.deepcopy(event) for event in calendar_events[cal] if event.start.day == (TODAY + timedelta(days=days_forward)).day]
        calendar_events_tomorrow[cal] = copy.deepcopy(tomorrow)

    return calendar_events_tomorrow

#TODO: create a function to create a fancy string to export to Telegram.py with the day's events

#TODO: create a function to get the first event of tomorrow
def get_first_event_day(calendar_events_tomorrow: dict) -> Event:
    """From a dictionnary of all the events of a specific day, it returns the first event of the day.

    Args:
        calendar_events_tomorrow (dict): dict. Key is the calendar id, value is the list of the events.

    Returns:
        Event: first event of the day. Returns None if no event on specified day.
    """

    list_min = []
    
    for cal in calendar_events_tomorrow:
        try:
            first_event = min(calendar_events_tomorrow[cal], key = lambda event: event.start)
            list_min.append(copy.deepcopy(first_event))
        except:
            continue

    if len(list_min) == 0:
        return None
    else:
        first = min(list_min, key = lambda event: event.start)
        return first


def check_address(event: Event):
    """Check if the event has an address associated.

    Args:
        event (Event): event.

    Returns:
        str or bool: if the event has an address, it returns the address, otherwise it return False. 
    """
    try:
        address = event.location

    except:
        address = False

    return address

#TODO: create a fancy string to inform user before they go to bed

if __name__ == "__main__":

    USER = settings.get_parameter("ID_MAIN")
    
    # 1. Get the calendar settings associated to USER in settings.json: dictionnary, key: calendar_id, value: offset value
    calendars_user = get_calendars_user(user_id=USER)
    print(calendars_user, "", sep = "\n")

    # 2. Get all the events from all the calendars of USER: dictionnary, key: calendar_id, value: list of the events
    events_user = get_all_events(calendars_user=calendars_user)
    print(events_user, "", sep = "\n")

    # 3. Offsetting the time of the events: same format as events_user but the events from the calendar needing offset are changed
    calendar_events_offset = offset_time(calendars_user = calendars_user, calendar_events= events_user)
    print(calendar_events_offset, "", sep = "\n")

    # 4. Order the events by starting time
    ordered_events = get_list_events_time(calendar_events_offset)
    print(ordered_events, "", sep = "\n")

    # 5. Filter to keep only the events of tomorrow
    calendar_tomorrow = get_events_tomorrow(calendar_events= calendar_events_offset)
    print(calendar_tomorrow, "", sep = "\n")

    # 5.2 Or the event 2 days ahead
    calendar_later = get_events_tomorrow(calendar_events= calendar_events_offset, days_forward=2)
    print(calendar_later, "", sep = "\n")

    # 6. Get the first element of tomorrow
    first_event_tomorrow = get_first_event_day(calendar_tomorrow)
    print(first_event_tomorrow, "", sep = "\n")