import ac, acsys, sys, time, os, datetime, traceback, pickle, math
from lib.acThreading import worker
# + Path variable for exception log (i "usualy" use caps for global varaibles)
EXC_LOG = os.path.join(os.path.dirname(__file__), 'logs', 'exception.log')

p = os.path.join(os.path.dirname(__file__), 'lib', 'char_spacing.dict')
with open(p, 'rb') as f:
    data = pickle.load(f)

CB_COUNTER=0
appWindow = 0
windowOpacity = 0.3

initialLabelText = "Welcome to VR-Names. Press F1 for settings"
driverInformation = []
labelStorage = []

def acMain(ac_version):
    global appWindow, labelStorage

    appWindow=ac.newApp("VR-Names")
    ac.setTitle(appWindow, "")
    ac.setSize(appWindow, 500, 250)
    ac.drawBorder(appWindow,0)
    ac.setBackgroundOpacity(appWindow, 0.8)
    ac.setIconPosition(appWindow, -9000, 0)

    for x in range(ac.getCarsCount()):
        label = ac.addLabel(appWindow, "")
        ac.setPosition(label, 10, 0 + (20 * x))
        labelStorage.append(label)

    setInitialLabel()
    return "vrnames"

def acUpdate(deltaT):
    global appWindow, windowOpacity
    ac.setBackgroundOpacity(appWindow, windowOpacity)
    getDriverInformation()

def getDriverInformation():
    global labelStorage
    for x in range(ac.getCarsCount()):
        ac.setText(labelStorage[x], ac.getDriverName(x) + " " + str(getRotation(x)))

def getRotation(carId):
    fx1, fy1, fz1 = ac.getCarState(carId, acsys.CS.TyreContactPoint, acsys.WHEELS.FL)
    fx2, fy2, fz2 = ac.getCarState(carId, acsys.CS.TyreContactPoint, acsys.WHEELS.FR)
    #point betweeen wheels is both added together, and halved
    pbwX = (fx1 + fx2) / 2
    pbwZ = (fz1 + fz2) / 2
    #remove world pos
    wpX, wpY, wpZ = ac.getCarState(carId, acsys.CS.WorldPosition)
    pbwX-= wpX
    pbwZ-= wpZ

    #angle between right and this car's direction
    # - parameters for atan2 are swapped here and then result is spun by 90 degrees
    #not entirely sure why I can't use the same way as above to get angle - if you realise, let me know please :D
    rads = math.atan2(pbwZ, pbwX)
    #spin
    angle = math.degrees(rads) - 90 # -90 or +90?
    rads = math.radians(angle)
    return rads

def move_vector(v, angle, anchor):
    x, y = v
    x = x - anchor[0]
    y = y - anchor[1]
    cos_theta = math.cos(angle)
    sin_theta = math.sin(angle)
    nx = x * cos_theta - y * sin_theta
    ny = x * sin_theta + y * cos_theta
    nx = nx + anchor[0]
    ny = ny + anchor[1]
    return [nx, ny]


def setInitialLabel():
    global appWindow, initialLabelText
    beginningLabel = ac.addLabel(appWindow, initialLabelText)
    ac.setPosition(beginningLabel, (500 - getPixelLengthOfText(initialLabelText)) / 2, 125)

def getPixelLengthOfText(text):
    userSpace = 0
    for z in text:
        if z in data:
            userSpace += data[z]
        else:
            userSpace += 10
    return userSpace



# =============================================================================
# >> HELPER FUNCTIONS  (by Hannes)
# =============================================================================
def log_exc(fname):

    # Lines to write to file
    lines = [
        '[{:%Y-%m-%d %H:%M}] > Exception in {}\n'.format(datetime.datetime.now(), fname),
        traceback.format_exc() + '\n',
    ]

    # Write to exception log
    with open(EXC_LOG, 'w', encoding='uft-8') as f:
        f.writelines(lines)

    # Send message to ac console
    ac.console('[AC Driftjunkies Chat] Exception occured in {} check error logs for details'.format(fname))