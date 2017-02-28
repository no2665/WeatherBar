# https://github.com/ZeevG/python-forecast.io

from time import sleep
import forecastio, datetime, serial, requests, sys, subprocess, os, random

api_key = "495b661368a3b709f8bba459f6ef1c7d"
lat = 51.454563
lng = -0.400965

#url = "https://api.forecast.io/forecast/495b661368a3b709f8bba459f6ef1c7d/51.454563,-0.400965?exclude=minutely,daily,alerts,flags,currently"
url = "https://api.darksky.net/forecast/495b661368a3b709f8bba459f6ef1c7d/51.454563,-0.400965?exclude=minutely,daily,alerts,flags,currently"

numRequests = 0

ser = serial.Serial()

clr_clear_day = [153, 153, 0] # Yellow
clr_clear_night = clr_clear_day
clr_rain = [27, 162, 248] # Blue
clr_snow = [167, 208, 255] # Light Blue
clr_sleet = [195, 200, 199] # Grey (probably white)
clr_wind = [146, 183, 58] # Green
clr_fog = [204, 153, 204] # Purple
clr_cloudy = [102, 45, 25] # Dark red
clr_partly_cloudy_day = [255, 231, 76] # Dirty yellow
clr_partly_cloudy_night = clr_partly_cloudy_day

weather_dict = {"clear-day": clr_clear_day,
		"clear-night": clr_clear_night,
		"rain": clr_rain,
		"snow": clr_snow,
		"sleet": clr_sleet,
		"wind": clr_wind,
		"fog": clr_fog,
		"cloudy": clr_cloudy,
		"partly-cloudy-day": clr_partly_cloudy_day,
		"partly-cloudy-night": clr_partly_cloudy_night,
		}

weather_for_day = {}

def main():
	global numRequests
	global weather_for_day

	log("Starting program")

	# Read saved weather and requests
	try:
		with open('weather_data.pdict', 'r') as save_file:
			saved_data = save_file.read()
			saved_data = eval(saved_data)
			weather_for_day = saved_data['weather']
			numRequests = saved_data['requests']
			log("Successfully read data")
	except:
		log("No weather data to read")

	ser.baudrate = 9600
	ser.port = "/dev/ttyUSB0"
	ser.timeout = 5
	ser.open()

	random.seed()

	previousMinutes = -1
	every = 5 # Every 5 minutes
	quotient = -1
	bigUpdate = False
	shouldUpdate = False
	flipFlop = True

	while True:

		minutes = datetime.datetime.now().minute
		currentQuotient = minutes / every

		if currentQuotient != quotient:
			quotient = currentQuotient
			shouldUpdate = True
			bigUpdate = False

		if ( (previousMinutes < 30 and minutes >= 30)
			or (previousMinutes >=30 and minutes < 30)
			or (previousMinutes == -1) ):
			previousMinutes = minutes
			shouldUpdate = True
			bigUpdate = True

		if shouldUpdate:
			shouldUpdate = False
			flipFlop = not flipFlop
			updateClockWithWeather(bigUpdate)

		if flipFlop:
			specialMode()
		else:
			 sleep(60)

# Code that is ran every hour to get the new weather status, and send it to the clock
def updateClockWithWeather(bigUpdate = False):
	global numRequests

	# If it's a new day, delete yesterdays data
	hourNow = datetime.datetime.now().hour
	if hourNow == 0:
		numRequests = 0
		weather_for_day.clear()

	if numRequests > 950:
		sendCode0(0, 255, 0, 0)
		log("Daily requests used up")
		return;

	# Get the weather
	readWholeDay = False
	try:
		weather = getHourlyWeather()
	except requests.exceptions.Timeout:
		log("Woops, timed out!")
		if bigUpdate:
			sleep(30)
			updateClockWithWeather(bigUpdate)
		return;
	except requests.exceptions.ConnectionError, e:
		log(e)
		log("Lost the connection")
		#subprocess.call(['sudo /sbin/ifdown eth0 && sleep 10 && sudo /sbin/ifup --force eth0'], shell=True)
		sleep(60)
		updateClockWithWeather(bigUpdate)
		return;
	except:
		log("Woops, something went wrong: " + sys.exc_info()[0])
		sleep(300)
		updateClockWithWeather(bigUpdate)
		return;

	for hourlyData in weather.data:
		hour = hourlyData.time.hour
		# If it's data for the next day stop reading
		if hour == 0:
			if hourNow == 23:
				clr = weather_dict.get(hourlyData.icon, [0, 0, 0])
				weather_for_day[hour] = clr
				break;
			elif hourNow == 0:
				if readWholeDay == True:
					break;
				readWholeDay = True
			else:
				break;
		clr = weather_dict.get(hourlyData.icon, [0, 0, 0])
		weather_for_day[hour] = clr

	if bigUpdate:
		# Now lets send all our data
        	# First lets clear all the other colours
		sendCode1(0, 0, 0)
	for k in weather_for_day:
		clr = weather_for_day.get(k)
		sendCode0(k, clr[0], clr[1], clr[2])

	##### DEBUG #####
	## Lets check the values ##
	#sendCode2();
	### END DEBUG ###

	log("Updated")

	# Save data to file
	save_data = {
		"weather": weather_for_day,
		"requests": numRequests
	}
	try:
		with open('weather_data.pdict', 'w') as save_file:
			save_file.write(str(save_data))
	except:
		log("Could not save data")

def getHourlyWeather():
	global numRequests
	numRequests = numRequests + 1
	forecast = forecastio.manual(url, 60)
	byHour = forecast.hourly()
	return byHour;

def sendCode0(hour, red, green, blue):
	string = "0," + str(hour) + "," + str(red) + "," + str(green) + "," + str(blue)
	rec = ""
	while rec != string:
		ser.write(string)
		sleep(1.0)
		rec = ser.readline().rstrip('\r\n')
		sleep(0.2)

def sendLazyCode0(hour, red, green, blue):
	string = "0," + str(hour) + "," + str(red) + "," + str(green) + "," + str(blue)
	rec = ""
	ser.write(string)
	sleep(1.0)
	rec = ser.readline()
	sleep(0.2)

def sendCode1(red, green, blue):
	string = "1," + str(red) + "," + str(green) + "," + str(blue)
	rec = ""
	while rec != string:
		ser.write(string)
		sleep(1.0)
		rec = ser.readline().rstrip('\r\n')
		sleep(0.2)

def sendCode2():
	string = "2"
	rec = ""
	ser.write(string)
	sleep(1.0)
	while rec != string:
		rec = ser.readline().rstrip('\r\n')
		log(rec)
		sleep(0.2)

def terminate(a, b):
	ser.close()
	sys.exit()

def log(message):
	message = str(datetime.datetime.now()) + ': ' + str(message)
	print message
	sys.stdout.flush()

def specialMode():
	now = datetime.datetime.now()
	if (now.month == 12 and now.day == 25):
		christmas_colours = [
			[255, 0, 0],
			[0, 255, 0],
			[0, 0, 255],
			[255, 255, 0],
			[0, 255, 255],
			[255, 0, 255],
			[255, 255, 255],
			[111, 87, 221],
			[234, 179, 74],
			[232, 77, 208],
			[72, 236, 183],
			[167, 208, 255]
		]
		# IT'S CHRISTMAS!!
		rndcolour = christmas_colours[random.randint(0, len(christmas_colours)-1)];
		sendLazyCode0(random.randint(0, 23), rndcolour[0], rndcolour[1], rndcolour[2])
	else:
		sleep(60)

if __name__ == "__main__":
	main()
