import requests
import time as Time
import threading

from forecastio.models import Forecast


def load_forecast(key, lat, lng, time=None, units="auto", lazy=False,
                  callback=None):
    """
        This function builds the request url and loads some or all of the
        needed json depending on lazy is True

        inLat:  The latitude of the forecast
        inLong: The longitude of the forecast
        time:   A datetime.datetime object representing the desired time of
                the forecast
        units:  A string of the preferred units of measurement, "auto" id
                default. also us,ca,uk,si is available
        lazy:   Defaults to false.  The function will only request the json
                data as it is needed. Results in more requests, but
                probably a faster response time (I haven't checked)
    """

    if time is None:
        url = 'https://api.forecast.io/forecast/%s/%s,%s' \
              '?units=%s' % (key, lat, lng, units,)
    else:
        url_time = str(int(Time.mktime(time.timetuple())))
        url = 'https://api.forecast.io/forecast/%s/%s,%s,%s' \
              '?units=%s' % (key, lat, lng, url_time,
              units,)

    if lazy is True:
        baseURL = "%s&exclude=%s" % (url,
                                     'minutely,currently,hourly,'
                                     'daily,alerts,flags')
    else:
        baseURL = url

    return manual(baseURL, callback=callback)


def manual(requestURL, timeout=0, callback=None):
    """
        This fuction is used by load_forecast OR by users to manually
        construct the URL for an API call.
    """

    if callback is None:
        return get_forecast(requestURL, timeout)
    else:
        thread = threading.Thread(target=load_async,
                                  args=(requestURL, callback))
        thread.start()

  
def get_forecast(requestURL, t=0):
    forecastio_reponse = requests.get(requestURL, timeout=t)

    json = forecastio_reponse.json()
    headers = forecastio_reponse.headers

    return Forecast(json, forecastio_reponse, headers)


def load_async(url, callback):
    callback(get_forecast(url))
