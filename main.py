#!/usr/bin/python3

"""
Copyright (C) 2024  https://github.com/bbaster

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import requests
import urllib
import getpass
import re
import json
import os
import sys

from dotenv import load_dotenv
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


#Assumes to be working with a "website-main.html" file
def get_jsessionid(soup_main: BeautifulSoup) -> str:
    extract = soup_main.find_all("script")[1].contents[0]
    pattern = re.compile(r"jsessionid=([A-Z0-9]+)")
    return(re.search(pattern, extract).group(1))

def get_person_id(soup_main: BeautifulSoup) -> str:
    extract = soup_main.find_all("ul")[2]
    pattern = re.compile(r"idosoby=([0-9]+)")
    return(re.search(pattern, str(extract)).group(1))

def get_round_number(soup_main: BeautifulSoup) -> str:
    extract = soup_main.find_all("ul")[2]
    pattern = re.compile(r"nrtury=([0-9]+)")
    return(re.search(pattern, str(extract)).group(1))


#Assumes to be working with a "website-timetable.html" file
def get_semester_id(soup_timetable: BeautifulSoup) -> str:
    text = soup_timetable.find_all("div")[50].find("script").contents[0]
    pattern = re.compile(r"idsemestru : (\d+),")
    return(re.search(pattern, text).group(1))

class Tile():
    def __init__(self, lecture: str):
        self.lecture = json.loads(lecture)
        self.start_timestamp = self.lecture["dataRozpoczecia"]/1000
        self.end_timestamp = self.lecture["dataZakonczenia"]/1000
        self.subject_name = self.lecture["nazwaPelnaPrzedmiotu"]
        self.locations = [ sale["nazwaSkrocona"] for sale in self.lecture["sale"]]
        self.lecturers = [ wykladowcy["stopienImieNazwisko"] for wykladowcy in self.lecture["wykladowcy"]]

    def __str__(self):
        return f"""
{datetime.fromtimestamp(self.start_timestamp).strftime("%H:%M")} - {datetime.fromtimestamp(self.end_timestamp).strftime("%H:%M")}
{self.subject_name}
{', '.join(self.locations)}
{', '.join(self.lecturers)}
"""

load_dotenv()

if os.getenv("DOMAIN"):
    domain = os.getenv("DOMAIN")
else:
    print("Error: DOMAIN unset!", file=sys.stderr)
    exit(1)

if os.getenv("SCHOOL_CODE"):
    school_code = os.getenv("SCHOOL_CODE")
else:
    print("Error: SCHOOL_CODE unset!", file=sys.stderr)
    exit(1)


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.7,pl;q=0.3',
    'Referer': f'https://{domain}/{school_code}-stud-app/ledge/view/stud.StartPage',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': f'https://{domain}/',
    'DNT': '1',
    'Sec-GPC': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Priority': 'u=0, i',
}

params = {
    'action': 'security.authentication.ImapLogin',
}

if os.getenv('LOGIN') != None:
    username=os.getenv('LOGIN')
else:
    username = input("Username: ")

if os.getenv('PASSWORD') != None:
    password=os.getenv('PASSWORD')
else:
    password = getpass.getpass(prompt="Password: ", stream=None)

if len(sys.argv) > 1:
    date_range = ' '.join(sys.argv[1:])
else:
    date_range = input("Specify a timetable date range (eg. \"04.11.2024 - 09.11.2024\", or nothing to fetch current day, or \"week\" for current week): ")
pattern = (
    r"^(?:(?P<start_day>[1-9]|[0-2][0-9]|3[01])\."
    r"(?P<start_month>1[0-2]|0?[1-9])?\.?"
    r"(?P<start_year>2[0-9]{3})?"
    r"(?: - )?"
    r"(?:(?P<end_day>[1-9]|[0-2][0-9]|3[01])?\.)?"
    r"(?P<end_month>1[0-2]|0?[1-9])?\.?"
    r"(?P<end_year>2[0-9]{3})?)?"
)


date_start = datetime(
    int(re.search(pattern, date_range).group("start_year") or ((datetime.today() - timedelta(days=datetime.today().weekday())).year if date_range == "month" else datetime.now().year)),
    int(re.search(pattern, date_range).group("start_month") or ((datetime.today() - timedelta(days=datetime.today().weekday())).month if date_range == "week" else datetime.now().month)),
    int(re.search(pattern, date_range).group("start_day") or ((datetime.today() - timedelta(days=datetime.today().weekday())).day if date_range == "week" else datetime.now().day))

)

date_end = datetime(
    int(re.search(pattern, date_range).group("end_year") or ((datetime.today() - timedelta(days=datetime.today().weekday() - 4)).year if date_range == "week" else datetime.now().year)),
    int(re.search(pattern, date_range).group("end_month") or ((datetime.today() - timedelta(days=datetime.today().weekday() - 4)).month if date_range == "week" else datetime.now().month)),
    int(re.search(pattern, date_range).group("end_day") or ((datetime.today() - timedelta(days=datetime.today().weekday() - 4)).day if date_range == "week" else date_start.day if re.search(pattern, date_range).group("start_day") else datetime.now().day)),
    23,
    59,
    59
)
'''
print(date_start, date_end, sep='\n')
print("group start day: ", re.search(pattern, date_range).group("start_day"))
print("group end day: ", re.search(pattern, date_range).group("end_day"))
exit()
'''
cookies = {
    f'locale.{username}': 'en_US',
}

data = {
        'login' : f'{username}',
        'password' : f'{password}'
}

for key, value in data.items():
    if not value:
        print("Wrong login or password!")
        exit(1)

data = urllib.parse.urlencode(data)

response = requests.post(
    f'https://{domain}/{school_code}-stud-app/ledge/view/stud.StartPage',
    params=params,
    cookies=cookies,
    headers=headers,
    data=data,
)


soup_main = BeautifulSoup(response.text, "lxml")
if soup_main.find_all(class_="bad-pasword-wiki"):
    print("Wrong login or password!", file=sys.stderr)
    exit(1)
else:
    print("Authentication successful!", file=sys.stderr)


cookies["JSESSIONID"] = get_jsessionid(soup_main)
headers["Referer"] = f"https://{domain}/{school_code}-stud-app/ledge/view/stud.schedule.SchedulePage?idosoby={get_person_id(soup_main)}&nrtury={get_round_number(soup_main)}"
params["idosoby"] = get_person_id(soup_main)
params["nrtury"] = get_round_number(soup_main)

response = requests.post(
    f'https://{domain}/{school_code}-stud-app/ledge/view/stud.schedule.SchedulePage',
    params=params,
    cookies=cookies,
    headers=headers,
    data=data,
)

soup_timetable = BeautifulSoup(response.text, "lxml")

headers["X-Requested-With"] = "XMLHttpRequest"
headers["Sec-Fetch-Dest"] = "empty"
headers["Sec-Fetch-Mode"] = "cors"
headers["Sec-Fetch-Site"] = "same-origin"
headers["Pragma"] = "no-cache"
headers["Cache-Control"] = "no-cache"


def fetch_and_parse_timetable(start_timestamp: int) -> dict:

    timetable = {}

    data = {
        "service": "Planowanie",
        "method": "getUlozoneTerminyOsoby",
        "params": {
            "idOsoby":get_person_id(soup_main),"idSemestru":get_semester_id(soup_timetable),"poczatekTygodnia":start_timestamp*1000
        }
    }
    
    response = requests.post(
        f'https://{domain}/{school_code}-stud-app/ledge/view/AJAX',
        params=params,
        cookies=cookies,
        headers=headers,
        data=json.dumps(data)
    )
  
    lectures=json.loads(response.text)

    for i in range(int(lectures["returnedValue"]["numRows"])-1, -1, -1):
        tile = Tile(json.dumps(lectures["returnedValue"]["items"][i]))
        if date_start.timestamp() <= tile.start_timestamp <= date_end.timestamp():
            date_key = datetime.fromtimestamp(tile.start_timestamp).strftime("%d.%m.")
            timestamp = tile.start_timestamp
            text = str(tile)
            if not date_key in timetable:
                timetable[date_key] = {}
            if not i in timetable[date_key]:
                timetable[date_key][i] = {}
            timetable[date_key][i]["timestamp"] = timestamp
            timetable[date_key][i]["text"] = text
    
    timetable = {
        date: dict(
            sorted(
                lectures.items(),
                key = lambda item: item[1]["timestamp"]
            )
        )
        for date, lectures in timetable.items()
    }

    for date, lectures in timetable.items():
        print(f'\n\n{date}')
        for i in lectures:
            print(timetable[date][i]["text"])
    return timetable


current_start_date = (date_start - timedelta(days=date_start.weekday()))
timetable = fetch_and_parse_timetable(start_timestamp=int(current_start_date.timestamp()))

if not timetable:
    last_timestamp = current_start_date.timestamp()
else:
    last_timestamp = max(lecture["timestamp"] for lecture in timetable[max(timetable.keys())].values())

while datetime.fromtimestamp(last_timestamp).replace(hour=23, minute=59, second=59).timestamp() < date_end.timestamp():
    current_start_date = current_start_date - timedelta(days=current_start_date.weekday()-7)
    timetable = fetch_and_parse_timetable(start_timestamp=int(current_start_date.timestamp()))
    if not timetable:
        last_timestamp = (datetime.fromtimestamp(last_timestamp) - timedelta(days=datetime.fromtimestamp(last_timestamp).weekday()-7)).timestamp()
    else:
        last_timestamp = max(lecture["timestamp"] for lecture in timetable[max(timetable.keys())].values())
