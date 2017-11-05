import ac, acsys, sys, time, os, datetime, traceback, pickle

# + Path variable for exception log (i "usualy" use caps for global varaibles)
EXC_LOG = os.path.join(os.path.dirname(__file__), 'logs', 'exception.log')

p = os.path.join(os.path.dirname(__file__), 'lib', 'char_spacing.dict')
with open(p, 'rb') as f:
    data = pickle.load(f)

CB_COUNTER=0
appWindow=0

def acMain(ac_version):
    global appWindow

    appWindow=ac.newApp("AC Driftjunkies Chat")
    ac.setTitle(appWindow, "")
    ac.setSize(appWindow,500,250)
    ac.drawBorder(appWindow,0)
    ac.setBackgroundOpacity(appWindow, 0.8)
    ac.setIconPosition(appWindow, -9000, 0)

    return "vrnames"

def acUpdate(deltaT):
    global appWindow

    worker.check_queue()
    ac.setBackgroundOpacity(appWindow, 0.8)



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