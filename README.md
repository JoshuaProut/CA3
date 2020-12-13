# CA3 Covid Clock
#### Joshua Prout

## Introduction
This is a smart alarm clock which can also help keep track of the coronavirus situation in your area.
This program is event driven, using Flask and an HTML template. The user has the option to create an
alarm, and a choice of announcing the news and or weather. This alarm is announced using PyTTsx3. 
The top news stories for the day are given as notifications.

Python Version 3.8
Docs can be found in ./docs/_build/html/index.html

## Prerequisites
### Requirements
Requires Python 3.8 or above, you will also need PIP installed.

Download a release of this project or clone the repository, then navigate to the folder.
Type pip install -r requirements.txt to get all the requirements at once.

### API keys
You will need an API Key for openweathermap.org and newsapi.org, coronavirus.data.gov.uk does not 
need a key, but you will need the code for your city, eg Exeter has the code: E07000041 

## Getting Started
Make sure you have the requirements installed and have your API keys

Enter your api keys, coronavirus area code, city, county and area population into the config.json file
This program works as a local client server system, using an HTML page to interact with, and a python
program as the backend. To start the program, run main.py and then open a browser and go to page:
#### http://127.0.0.1:5000/index

Alarms can be entered by choosing a date and time, entering a description, choosing whether news or weather
should be displayed, then pressing submit. Notifications will be updated automatically and silently.

## License
[MIT](https://choosealicense.com/licenses/mit/)