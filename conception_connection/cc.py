import re
import requests
from bs4 import BeautifulSoup
from bottle import (
    route,
    run,
    template,
    )
from datetime import (
    date,
    timedelta,
    )

ONE_DAY = timedelta(days=1)
#EVENTS_URL = 'http://www.historyorb.com/today/search.php'
EVENTS_URL = 'http://en.wikipedia.org/w/api.php'
PAYLOAD = {
    'format': 'json',
    'action': 'query',
    'prop': 'extracts',
    }

@route('/')
def home():
    return template('homepage')

@route('/date', method='POST')
@route('/date/<date_string>')
def view_date(date_string=None):
    """ Return list of historical dates that happened 9 months before <date>
    """
    if date_string is None:
        date_string = request.forms.get('date_string')

    year, month, day = [int(x) for x in date_string.split('-', 2)]
    birthdate = date(year, month, day)
    gestation_period = time_period(
        birthdate,
        timedelta(weeks=39),
        timedelta(weeks=41),
        )

    events = []

    for c_date in gestation_period:
        events_on_date = get_events_for_date(c_date)
        events.extend(events_on_date)

    return template('date_template', events=events)

def time_period(alpha, begin, end, delta=ONE_DAY):
    while begin < end:
        yield alpha - begin
        begin += delta

def get_events_for_date(event_date):
    month_string = event_date.strftime('%B')
    payload = PAYLOAD.copy()
    payload['titles'] = "{month}_{year}".format(
        year=event_date.year,
        month=month_string,
        )
    events = []

    req = requests.get(EVENTS_URL, params=payload)
    page_json = req.json()
    for page_id in page_json['query']['pages']:
        page_html = page_json['query']['pages'][page_id]['extract']
        page_soup = BeautifulSoup(page_html)
        try:
            event_list = page_soup.find(
                name='h2',
                text=re.compile(r"{month} {day}, {year}".format(
                    month=month_string,
                    day=event_date.day,
                    year=event_date.year,
                    ))
                ).find_next_sibling('ul')
        except AttributeError:
            continue

        for li in event_list.find_all('li'):
            if not li.text.startswith('Born:'):
                events.append(li.text)

    return events

if __name__ == '__main__':
    run(host='localhost', port=8080, debug=True, reloader=True)
