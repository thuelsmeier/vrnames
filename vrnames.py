import ac, acsys, sys, time, os, datetime, traceback, pickle, math
from lib.acThreading import worker
# + Path variable for exception log (i "usualy" use caps for global varaibles)
EXC_LOG = os.path.join(os.path.dirname(__file__), 'logs', 'exception.log')

p = os.path.join(os.path.dirname(__file__), 'lib', 'char_spacing.dict')
with open(p, 'rb') as f:
    data = pickle.load(f)

CB_COUNTER = 0
appWindow = 0
windowOpacity = 0.3
windowSizeX = 1920
windowSizeY = 1080

initialLabelText = "Welcome to VR-Names."
driverInformation = []
labelStorage = []

show_name = 0
spinner_y_offset = 0
scale_factor = 0
fov_setting = 0
def acMain(ac_version):
    global appWindow, labelStorage, spinner_y_offset, scale_factor, fov_setting

    appWindow=ac.newApp("VR-Names")
    ac.setTitle(appWindow, "VR-names")
    ac.setSize(appWindow, 200, 200)
    ac.drawBorder(appWindow,0)
    ac.setBackgroundOpacity(appWindow, 0)

    # ac.setIconPosition(appWindow, -9000, 0)


    spinner_y_offset = ac.addSpinner(appWindow, "Name Height Offset")
    ac.setRange(spinner_y_offset, -100, 100)
    ac.setValue(spinner_y_offset, 0)
    ac.setStep(spinner_y_offset, 1)
    ac.setPosition(spinner_y_offset, 10, 90)
    ac.setSize(spinner_y_offset, 180, 20)

    scale_factor = ac.addSpinner(appWindow, "scale text factor")
    ac.setRange(scale_factor, 1, 30)
    ac.setValue(scale_factor, 10)
    ac.setStep(scale_factor, 1)
    ac.setPosition(scale_factor, 10, 135)
    ac.setSize(scale_factor, 180, 20)

    fov_setting = ac.addSpinner(appWindow, "scale text factor")
    ac.setRange(fov_setting, 0, 360)
    ac.setValue(fov_setting, 110)
    ac.setStep(fov_setting, 1)
    ac.setPosition(fov_setting, 10, 180)
    ac.setSize(fov_setting, 180, 20)

    button_toggle_name = ac.addButton(appWindow,"Toggle name")
    ac.addOnClickedListener(button_toggle_name, toggle_name)
    ac.setSize(button_toggle_name,180,20)
    ac.setPosition(button_toggle_name, 10, 40)

    for x in range(ac.getCarsCount()):
        label = ac.addLabel(appWindow, "")
        ac.setPosition(label, 10, 0 + (20 * x))
        labelStorage.append(label)

    setInitialLabel()
    return "vrnames"
def toggle_name(v1,v2):
    global show_name
    if show_name == 0:
        show_name = 1
    else:
        show_name = 0
def acUpdate(deltaT):
    global appWindow, windowOpacity,appPosX,appPosY,labelStorage,show_name
    if show_name == 1:
        appPosX,appPosY = ac.getPosition(appWindow)
        ac.setBackgroundOpacity(appWindow, windowOpacity)
        detectionArea = getDetectionArea()
        #ac.console(detectionArea)
        getDriverInformation(detectionArea)
    else:
        for x in range(ac.getCarsCount()):
            ac.setPosition(labelStorage[x], 0, 0)
            ac.setText(labelStorage[x], "")
def getDetectionArea():
    global fov_setting
    posX, posZ, posY = ac.getCarState(0, acsys.CS.WorldPosition)
    rads = getRotation(0)
    fov_angle = ac.getValue(fov_setting)
    PointTopLeftX, PointTopLeftY = move_vector((posX, posY + 200), rads - math.radians(fov_angle/2), (posX, posY))
    PointTopRightX, PointTopRightY = move_vector((posX, posY + 200), rads + math.radians(fov_angle/2), (posX, posY))

    return ((posX, posY), (PointTopLeftX, PointTopLeftY), (PointTopRightX, PointTopRightY))

def getDriverInformation(detectionArea):
    global labelStorage,appPosX,appPosY,spinner_y_offset,fov_setting
    triangle = Triangle(detectionArea[0], detectionArea[1], detectionArea[2])
    setLabel = 0
    for x in range(ac.getCarsCount()):
        posX, posZ, posY = ac.getCarState(x, acsys.CS.WorldPosition)
        if triangle.isInside((posX, posY)) and x != 0:
            vect_x = posX - detectionArea[0][0]
            vect_y = posY - detectionArea[0][1]
            distance = math.sqrt(math.pow(vect_x,2) + math.pow(vect_y,2))
            newPosition = getRenderPosition(x, detectionArea, (posX, posY))
            ac.setText(labelStorage[setLabel], ac.getDriverName(x))
            fov_angle = ac.getValue(fov_setting)
            xPos = (((newPosition * windowSizeX) / fov_angle) - appPosX)
            yOffset = ac.getValue(spinner_y_offset)
            yPos = (((windowSizeY / 2) - 20) - appPosY) + int(yOffset)
            fontSize = (10 * (1 / (distance / 100))) * (ac.getValue(scale_factor)/10)
            ac.setPosition(labelStorage[setLabel], xPos, yPos)
            ac.setFontSize(labelStorage[setLabel], fontSize)
            setLabel += 1

    for z in range(ac.getCarsCount() - setLabel):
        ac.setText(labelStorage[setLabel + z], "")

def getRenderPosition(carId, detectionArea, carPosition):
    vect_x = detectionArea[1][0] - detectionArea[0][0]
    vect_y = detectionArea[1][1] - detectionArea[0][1]

    triangleAngle = math.atan2(vect_y, vect_x)

    carVect_x = carPosition[0] - detectionArea[0][0]
    carVect_y = carPosition[1] - detectionArea[0][1]

    carAngle = math.atan2(carVect_y, carVect_x)

    return math.degrees(carAngle - triangleAngle)


def getRotation(carId):
    fx1,fy1,fz1 = ac.getCarState(carId, acsys.CS.TyreContactPoint, acsys.WHEELS.FL)
    fx2,fy2,fz2 = ac.getCarState(carId, acsys.CS.TyreContactPoint, acsys.WHEELS.FR)
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
    # beginningLabel = ac.addLabel(appWindow, initialLabelText)
    # ac.setPosition(beginningLabel, (500 - getPixelLengthOfText(initialLabelText)) / 2, 125)

def getPixelLengthOfText(text):
    userSpace = 0
    for z in text:
        if z in data:
            userSpace += data[z]
        else:
            userSpace += 10
    return userSpace

class Triangle:
    def __init__(self, p1, p2, p3):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3

        # optimisation
        self.precalcs1 = self.p1[1] * self.p3[0] - self.p1[0] * self.p3[1]
        self.precalcs2 = (self.p3[1] - self.p1[1])
        self.precalcs3 = (self.p1[0] - self.p3[0])

        self.precalct1 = self.p1[0] * self.p2[1] - self.p1[1] * self.p2[0]
        self.precalct2 = (self.p1[1] - self.p2[1])
        self.precalct3 = (self.p2[0] - self.p1[0])

        self.precalcA = -self.p2[1] * self.p3[0] + self.p1[1] * (self.p3[0] - self.p2[0]) + self.p1[0] * (
        self.p2[1] - self.p3[1]) + self.p2[0] * self.p3[1]

    def isInside(self, pt):
        s = self.precalcs1 + self.precalcs2 * pt[0] + self.precalcs3 * pt[1]
        t = self.precalct1 + self.precalct2 * pt[0] + self.precalct3 * pt[1]

        if ((s < 0) != (t < 0)):
            return False

        A = self.precalcA
        if (A < 0.0):
            s = -s
            t = -t
            A = -A
        return ((s > 0) and (t > 0) and ((s + t) <= A))

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