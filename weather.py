# https://github.com/ZeevG/python-forecast.io

from time import sleep
import forecastio, datetime, serial, pygame, requests, sys, subprocess
from pygame.locals import *

api_key = "495b661368a3b709f8bba459f6ef1c7d"
lat = 51.454563
lng = -0.400965

#url = "https://api.forecast.io/forecast/495b661368a3b709f8bba459f6ef1c7d/51.454563,-0.400965?exclude=minutely,daily,alerts,flags,currently"
url = "https://api.darksky.net/forecast/495b661368a3b709f8bba459f6ef1c7d/51.454563,-0.400965?exclude=minutely,daily,alerts,flags,currently"

non_physical = False
try:
	ser = serial.Serial("/dev/ttyUSB0", 9600)
except OSError: 
	non_physical = True

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

#Pygame stuff
WINDOWWIDTH = 350
WINDOWHEIGHT = 1000
BOXSIZE = 850 /24

def main():
	global FPSCLOCK, DISPLAYSURF, BASICFONT
	# Set up the GUI
	pygame.init()
	FPSCLOCK = pygame.time.Clock()
	DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
	BASICFONT = pygame.font.Font('freesansbold.ttf', 18)
	pygame.display.set_caption('Weather Clock')
	
	previousHour = -1
	while True:
		for event in pygame.event.get():
			if event.type == QUIT:
				terminate()

		updatePygameScreen()
		hourNow = datetime.datetime.now().hour
		if hourNow != previousHour:
			previousHour = hourNow
			updateClockWithWeather()
		FPSCLOCK.tick(1)

# Code that is ran every hour to get the new weather status, and send it to the clock
def updateClockWithWeather():
	# If it's a new day, delete yesterdays data
	hourNow = datetime.datetime.now().hour
	if hourNow == 0:
		weather_for_day.clear()
	
	print "Updating weather: ", hourNow
	# Get the weather
	readWholeDay = False
	try:
		weather = getHourlyWeather()
	except requests.exceptions.Timeout:
		print "Woops, timed out!"
		sleep(10)
		updateClockWithWeather()
		return;
	except requests.exceptions.ConnectionError, e:
		print e
		print "Lost the connection"
		#subprocess.call(['sudo /sbin/ifdown eth0 && sleep 10 && sudo /sbin/ifup --force eth0'], shell=True)
		sleep(60)
		updateClockWithWeather()
		return;
	except:
		print "Woops, something went wrong:", sys.exc_info()[0]
		sleep(300)
		updateClockWithWeather()
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

	if not non_physical:
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

def getHourlyWeather():
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
	return;

def sendCode1(red, green, blue):
	string = "1," + str(red) + "," + str(green) + "," + str(blue)
	rec = ""
	while rec != string:
		ser.write(string)
		sleep(1.0)
		rec = ser.readline().rstrip('\r\n')
		sleep(0.2)
	return;

def sendCode2():
	string = "2"
	rec = ""
	ser.write(string)
	sleep(1.0)
	while rec != string:
		rec = ser.readline().rstrip('\r\n')
		print rec
		sleep(0.2)
	return;

def updatePygameScreen():
	DISPLAYSURF.fill((255, 255, 255));
	for i in range(0, 24):
		rect = pygame.Rect(250, (i * (BOXSIZE + 5)) + 25, BOXSIZE + 10, BOXSIZE + 10)
		pygame.draw.rect(DISPLAYSURF, (0, 0, 0), rect)
	for i in range(0, 24):
		rect = pygame.Rect(255, (i * BOXSIZE) + 25 + ((i+1)*5), BOXSIZE, BOXSIZE)
		pygame.draw.rect(DISPLAYSURF, (255, 255, 255), rect)
	for k in weather_for_day:
		clr = weather_for_day.get(k)
		rect = pygame.Rect(255, (k * BOXSIZE) + 25 + ((k+1)*5), BOXSIZE, BOXSIZE)
		pygame.draw.rect(DISPLAYSURF, (clr[0], clr[1], clr[2]), rect)
		for description, colour in weather_dict.iteritems():
			if colour == clr:
				text = BASICFONT.render(description, True, (0, 0, 0))
				textRect = text.get_rect()
				textRect.topleft = (50, (k * BOXSIZE) + 25 + ((k+1)*5))
				DISPLAYSURF.blit(text, textRect)
				break;
	pygame.display.update()

def terminate():
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
	main()



