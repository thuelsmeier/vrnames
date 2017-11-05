import ac, acsys, sys, time, os, datetime, traceback, pickle
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

def acMain(ac_version):
    global appWindow

    appWindow=ac.newApp("VR-Names")
    ac.setTitle(appWindow, "")
    ac.setSize(appWindow, 500, 250)
    ac.drawBorder(appWindow,0)
    ac.setBackgroundOpacity(appWindow, 0.8)
    ac.setIconPosition(appWindow, -9000, 0)

    setInitialLabel()
    ac.addRenderCallback(appWindow , acUpdate)

    return "vrnames"

def acUpdate(deltaT):
    global appWindow, windowOpacity
    ac.setBackgroundOpacity(appWindow, windowOpacity)
    getDriverInformation()

def getDriverInformation():
    totalDriver = ac.getCarsCount()
    for x in range(totalDriver):
        label = ac.addLabel(appWindow, ac.getCarName(x))
        ac.setPosition(label, 10, 0 + (20 * x))

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