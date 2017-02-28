import daemon
import daemon.pidfile
import lockfile
import signal
import sys
import os
import nogui_weather

pidfile = '/var/run/weather.pid'

def start():
    if os.getuid() != 0:
        print "Please run as root"
        return

    logfile = open("/home/pi/Desktop/weather.log", "a")

    context = daemon.DaemonContext(
        working_directory='/home/pi/Desktop',
        umask=0o002,
        pidfile = daemon.pidfile.PIDLockFile(pidfile),
        stdout=logfile,
        stderr=logfile,
        )

    context.signal_map = {
        signal.SIGTERM: nogui_weather.terminate,
        signal.SIGHUP: 'terminate',
        }

    context.open()

    with context:
        nogui_weather.main()

def stop():
    pid = get_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as exc:
            print "Unable to kill process"
    else: 
        print "Weather is not running"

def get_pid():
    try:
        pf = file(pidfile, 'r')
        pid = int(pf.read().strip())
        pf.close()
    except IOError:
        pid = None
    except SystemExit:
        pid = None
    return pid

if __name__ == "__main__":
    if len(sys.argv) == 2:
        if sys.argv[1] == 'status':
            pid = get_pid()

            if pid:
                print 'Weather is running as pid %s' % pid
            else:
                print 'Weather is not running.'
        elif sys.argv[1] == 'start':
            start()
	elif sys.argv[1] == 'stop':
            stop()
	else:
            start()

