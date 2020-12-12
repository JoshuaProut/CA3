"""Main module for the CA3 Smart Alarm Clock"""

import sched
import threading
import time
from datetime import datetime
import json
import logging
import pyttsx3
import requests
from flask import Flask, render_template, request, Markup

app = Flask(__name__)
s = sched.scheduler(time.time, time.sleep)

# Arrays of dictionaries to contain active notifications and alarms.
alarms = []
notifications = []
used_articles = []

# Displays whether the alarm was created successfully, passed to template as "title"
alarm_status = "CovidClock"

# implements logger
logging.basicConfig(filename='errors.log', format='%(name)s - %(levelname)s - %(message)s', level=logging.WARNING)


@app.route('/index')
def index():
    """Takes args from the main form, returns an updated template with notifications and alarms

    URL Parameters:
    ---------------
    alarm_time: YYYY-MM-DD HH:MM
    two Description of alarm
    alarm_item: Title of alarm to be removed by the user
    news: If "news" then news and covid data announced with alarm
    weather: If "weather" then current weather is announced with alarm

    Returns
    -------
    index.html: Returns rendered HTML template with alarms, notifications and alarm status

    """

    alarm_time = request.args.get('alarm')  # gets selected alarm time
    alarm_description = request.args.get('two')  # gets description of alarm
    alarm_to_remove = request.args.get('alarm_item')  # if alarm closed, get title of alarm to close
    news = request.args.get('news')
    weather = request.args.get('weather')
    notification_to_remove = request.args.get('notif')

    if alarm_time and alarm_description:
        create_alarm(alarm_time, alarm_description, news, weather)
    elif alarm_to_remove:
        remove_alarm(alarm_to_remove)
    elif notification_to_remove:
        remove_notification(notification_to_remove)

    create_notifications()

    # Template is generated and returned to /index, alarms and notifications list are passed to
    # the template to be built into notifications.
    return render_template('index.html', alarms=alarms, notifications=notifications, title=alarm_status)


def create_alarm(alarm_time: str, description: str, news: str = None, weather: str = None):
    """Appends to the list of active alarms

    Appends the following dictionary to the alarms list
    Starts a background daemon function to wait to announce alarm
    alarm_dict = {
            "title": alarm_title,
            "content": description,
            "time": alarm_datetime,
            "news": news,
            "weather": weather
        }

    Parameters
    ----------
    global alarm_status: str
        error message or success message to be shown to user
    alarm_time : str
        Time for the alarm in format in the format: YYYY-MM-DD HH:MM
    description: str
        Description for the alarm
    news: str
        if not None, news will be announced with alarm
    weather: str
        if not None, weather will be announced with alarm

    """

    global alarm_status
    alarm_valid = True

    alarm_title = alarm_time.replace("T", " ")  # Makes alarm_title more readable
    # Casts to datetime variable for scheduling
    alarm_datetime = datetime.strptime(alarm_title, '%Y-%m-%d %H:%M')

    # Input checks
    for alarm in alarms:
        # Checks that an alarm has not already been set at chosen time
        if alarm_datetime == alarm["time"]:
            alarm_status = "ERROR: Alarm is already set for this time"
            logging.warning("User set alarm for current time")
            alarm_valid = False

        # Checks that alarm is not in the past
        elif alarm_datetime < datetime.now():
            alarm_status = "ERROR: Alarm is set in the past"
            logging.warning("User set alarm in the past")
            alarm_valid = False

    if alarm_valid:
        # Create dictionary of alarm data
        alarm_dict = {
            "title": alarm_title,
            "content": description,
            "time": alarm_datetime,
            "news": news,
            "weather": weather
        }
        alarms.append(alarm_dict)
        alarm_status = "Alarm created successfully"

        # Starts alarm daemon to announce alarm at specified time.
        alarm_daemon = threading.Thread(target=alarm_monitor, daemon=True,
                                        args=(alarm_dict,))
        alarm_daemon.start()


def alarm_monitor(alarm: dict):
    """Within the new daemon, starts the scheduler for alarm to be announced at specified time

    When the alarm time is reached, announce_alarm is called.

    Parameters
    ----------
    alarm: dict
     {
            "title": alarm_title,
            "content": description,
            "time": alarm_datetime,
            "news": news,
            "weather": weather
        }

    """

    time_secs = alarm['time'].timestamp()  # calculates alarm time in seconds since epoch

    # Adds alarm to queue, eventID is added to alarm dict for future use in cancelling the alarm
    alarm['eventID'] = s.enterabs(time_secs, 1, announce_alarm, argument=(alarm,))
    s.run()


def announce_alarm(alarm: dict):
    """Announces the alarm and news/weather if chosen using pyttsx3

    Parameters
    ----------
    alarm: dict
     {
            "title": alarm_title,
            "content": description,
            "time": alarm_datetime,
            "news": news,
            "weather": weather
        }

    """

    engine = pyttsx3.init()
    engine.say(alarm['content'])

    if alarm['weather']:
        weather_data = get_weather()
        # Retrieves current weather and description from the dict
        try:
            main = weather_data["main"]
            temp = main['temp']
            temp = str(round(temp - 273.15))  # Converts Kelvin to Celsius
            weather_section = weather_data['weather'][0]
            weather_description = weather_section["description"]

            weather_string = "The temperature is " + temp + " degrees Celsius and the weather is " \
                             + weather_description
            engine.say(weather_string)

        except (IndexError, KeyError):
            engine.say("Could not retrieve weather data")
            logging.error("Weather data error " + str(weather_data))

    if alarm['news']:
        news_data = get_news()
        try:
            engine.say("Today's top news stories are ")
            for article in news_data["articles"]:
                engine.say(article['title'])
        except (IndexError, KeyError):
            engine.say("News could not be retrieved")
            logging.error("News data error " + str(news_data))
            print(news_data)

        corona_data = get_corona_data()
        try:
            engine.say("There have been " + str(
                corona_data["body"][0]['newCasesByPublishDate']) +
                       " coronavirus cases in your area yesterday")

        except (IndexError, KeyError):
            engine.say("Coronavirus data could not be retrieved")
            logging.error("Corona data error " + str(corona_data))
            print(corona_data)

    engine.runAndWait()

    # Removes alarm from the list so it is no longer displayed on the web form
    remove_alarm(alarm["title"], True)


def create_notifications():
    """Provides top news articles as notifications

    Appends the following dictionary to the global notifications array

    notif_dict{
    title: str
        The headline title of the article
    content: html link
        The description of the article, linked to the full article using the URL provided
    """
    news_data = get_news()
    try:
        for article in news_data["articles"]:
            notif_dict = {"title": article["title"]}
            markup_url = "<a href=\"" + article["url"] + "\"" + "/>"
            notif_dict["content"] = Markup(markup_url) + article["description"]

            # Checks that notification is not currently being shown, and hasnt been removed
            # by the user before
            if notif_dict["title"] not in used_articles and notif_dict not in notifications:
                # Article added to front of queue so newest articles are shown first
                notifications.insert(0, notif_dict)

    except IndexError:
        print("error getting news")
        logging.error("Error ")
        print(news_data)


def remove_notification(notification_title: str):
    """Removes notification when X button pressed

    Removes notification from the global notifications list and adds it to the global used
    articles list so it will not be shown again

    Parameters
    ----------
    notification_title: str
        title of the notification to be removed
    """

    # Matches notification title to notification dictionary in the list
    for notification in notifications:
        if notification["title"] == notification_title:
            # Removes notification dict from list
            notifications.pop(notifications.index(notification))
            # The article will not be shown again when the news api refreshes.
            used_articles.append(notification['title'])


def get_weather() -> dict:
    """Returns temperature and weather description for current weather

    Uses the openweathermap.org API to get the current weather for the user's city defined in the
    config.JSON file, also in this file is the API key.

    Returns
    -------
    weather_data: dict
        Dict converted from full JSON obj from openweathermap.org
    """

    base_url = 'http://api.openweathermap.org/data/2.5/weather?'
    with open('config.json') as keys_file:
        data = json.load(keys_file)
    api_key = data["weather_key"]
    location = data["city"]
    url = base_url + "q=" + location + "&appid=" + api_key

    weather_data = requests.get(url).json()

    return weather_data


def remove_alarm(alarm_time: str, alarm_called=False):
    """Removes alarm from the alarm array

    If the alarm is in the future and needs to be removed from the schedule queue as well then
    alarm_called should be true. If the alarm has been announced, it will have been removed by
    the sched queue automatically.

    Parameters
    ----------
    alarm_time: str
        format: YYYY-MM-DD HH:MM
    alarm_called: Bool
    """

    # Matches the alarm time string to an alarm dictionary in the array
    for alarm in alarms:
        if alarm["title"] == alarm_time:
            alarms.pop(alarms.index(alarm))  # Removes alarm dictionary from array
            # If alarm has not been announced, removes from scheduler
            if not alarm_called:
                s.cancel(alarm['eventID'])


def get_news() -> dict:
    """Returns the top news stories

    Uses newsapi.org and returns the top headlines from BBC news
    API key stored in config.json

    Returns
    -------
    news_data: dict
        dict from full JSON obj returned from newsapi
    """

    with open('config.json') as config:
        config_data = json.load(config)
    api_key = config_data["news_key"]
    url = "https://newsapi.org/v2/top-headlines?sources=bbc-news&apiKey=" + api_key

    news_data = requests.get(url).json()
    return news_data


def get_corona_data() -> dict:
    """Retrieves coronavirus data from the official UK government tracking site

    Requests the new cases by publish date for the lower tier local authority code stored in
    config.json

    Returns
    -------
    corona_data: dict
        Full dict from JSON obj returned from coronavirus.data.gov.uk
    """
    with open('config.json') as config:
        config_data = json.load(config)
    area_code = config_data["city_code"]
    corona_data = requests.get(
        'https://api.coronavirus.data.gov.uk/v2/data?'
        'areaType=ltla&areaCode=' + area_code +
        '&metric=newCasesByPublishDate&format=json').json()

    return corona_data


if __name__ == '__main__':
    app.run()
