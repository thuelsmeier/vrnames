# >> Make _Worker more like a thread pool instance creator. old "worker" will use this as current but will
#    add more functionallity for private pools? all having common out queue
#
# =============================================================================
# >> IMPORTS
# =============================================================================
# Python Imports
import time
import threading
import queue

# =============================================================================
# >> CLASSES
# =============================================================================
class _Worker:

    def __init__(self):
        self.active = False
        self.out_queue = queue.Queue()
        self.in_queue = queue.Queue()

        # self.index = 0
        # self.out_queues = [queue.Queue() for i in range(4)]

    def start(self, threads=3):
        self.active = True
        self.spawn(self._delay)
        offset = 0.1 / threads
        for i in range(threads):
            self.spawn(self.run, offset * i)

    def spawn(self, fn, *args, daemon=True, **kw):
        t = threading.Thread(target=fn, args=args, kwargs=kw)
        t.daemon = daemon
        t.start()
        return t

    def queue(self, fn, *fn_args, cb=None, cb_args=(), cb_kw={}, **fn_kw):

        # Make sure arguments is iterable
        if not isinstance(cb_args, (list, tuple)):
            cb_args = (cb_args,)

        # Add to queue
        self.in_queue.put_nowait((fn, fn_args, fn_kw, cb, cb_args, cb_kw))

    def main_thread(self, cb, *args, **kw):
        self.out_queue.put((cb, args, kw))

        # q = self.out_queues[self.index]
        # q.put((cb, args, kw))

        # self.index += 1
        # if self.index > 3:
        #     self.index = 0

    def main_thread_return(self, fn, *args, _timeout=None, **kw):
        q = queue.Queue()

        def do_in_main(fn, *args, **kw):
            result = fn(*args, **kw)
            q.put_nowait(result)

        self.main_thread(do_in_main, fn, *args, **kw)
        return q.get(block=True, timeout=_timeout)

    def repeat(self, interval, cb, *cb_args, offset=0, repeats=-1, offset_call=False, start=True, threaded=False, **cb_kw):
        return Delay(offset, interval, cb, *cb_args, repeats=repeats, is_repeat=True, offset_call=offset_call, start=start, threaded=threaded, **cb_kw)

    def delay(self, delay, cb, *cb_args, start=True, threaded=False, **cb_kw):
        return Delay(0, delay, cb, *cb_args, start=start, threaded=threaded, **cb_kw)

    def _delay(self):
        while self.active:

            # Get current timer
            now = time.perf_counter()

            # Loop over active delays
            for d in list(Delay.active):

                # Has delay run out?
                if now >= d.time_end:  # Can this be passed multiple times (if repeat)

                    # Call done
                    d.done()

            # Resolution
            time.sleep(0.01)

    def check_queue(self):  # deltat
        # fps = 1 / deltat
        # v = int(0.25 * fps)
        # if not self.c % v:
        #      ...check queue
        #      self.c = 1
        # self.c += 1
        try:

            # Check queue for functions to be called in main thread
            fn, args, kw = self.out_queue.get_nowait()

            # Call function
            fn(*args, **kw)

        except queue.Empty:
            pass

        # # Loop thru out queues
        # for q in self.out_queues:
        #     try:

        #         # Check queue for functions to be called in main thread
        #         fn, args, kw = q.get_nowait()

        #         # Call function
        #         fn(*args, **kw)

        #     except queue.Empty:
        #         pass

    def run(self, offset):
        # time.sleep(offset)
        while self.active:
            try:
                fn, fn_args, fn_kw, cb, cb_args, cb_kw = self.in_queue.get(timeout=1)
                result = fn(*fn_args, **fn_kw)
                if cb:
                    if not isinstance(result, tuple):
                        result = (result,)
                    self.main_thread(cb, *result + cb_args, **cb_kw)
            except queue.Empty:
                pass

            except Exception as e:
                self.main_thread(re_raise, e)

            # finally:
            #     self.in_queue.task_done() will hang everything

    def is_main_thread(self):
        return True if threading.current_thread().name == 'MainThread' else False

STOPPED = 0
STARTED = 1
PAUSED = 2
DONE = 3

class Delay:
    active = []
    stopped = []

    def __init__(self, offset, interval, cb, *args, repeats=1, is_repeat=False, offset_call=False, start=True, threaded=False, **kw):
        self.offset = offset
        self.interval = interval
        self.cb = cb
        self.args = args
        self.kw = kw
        self.repeats = repeats
        self.is_repeat = is_repeat
        self.offset_call = offset_call  # Should we call the callback once the offset time expires?
        self.threaded = threaded
        self.status = STOPPED
        self.time_started = 0
        self.time_end = 0
        self.time_paused = 0
        self.time_stopped = 0

        if start:
            self.start()
        else:
            if self not in Delay.stopped:
                Delay.stopped.append(self)

    def start(self):
        if self.status in (STOPPED, DONE):

            # If repeat and is stopped add its offset time
            if self.status == STOPPED and self.is_repeat:
                self.time_end = time.perf_counter() + self.offset

            # Just put the interval to end time
            else:
                self.time_end = time.perf_counter() + self.interval

            self.status = STARTED
            self.time_started = time.perf_counter()

            if self in Delay.stopped:
                Delay.stopped.remove(self)

            if self not in Delay.active:
                Delay.active.append(self)

    def stop(self, call=False):
        if self.status in (STARTED, DONE):
            self.status = STOPPED
            self.time_stopped = time.perf_counter()

            if self in Delay.active:
                # worker.main_thread(print, 'Removed from active')
                Delay.active.remove(self)

            if self not in Delay.stopped:
                # worker.main_thread(print, 'Added to stopped')
                Delay.stopped.append(self)

            if call:
                if self.threaded:
                    worker.queue(self.cb, *self.args, **self.kw)
                else:
                    worker.main_thread(self.cb, *self.args, **self.kw)
            # worker.main_thread(print, 'Delayed stopped. Deltat: {:.4f}'.format(self.time_stopped - self.time_started))

    def done(self):
        self.status = DONE

        # Callback
        if self.threaded:
            worker.queue(self.cb, *self.args, **self.kw)
        else:
            worker.main_thread(self.cb, *self.args, **self.kw)

        if self.is_repeat:
            if self.repeats == -1:
                # worker.main_thread(print, 'Repeat is infinite. Deltat: {:.4f}'.format(time.perf_counter() - self.time_started))
                self.start()
            else:
                self.repeats -= 1
                if self.repeats:
                    # worker.main_thread(print, '{} Repeats left. Deltat: {:.4f}'.format(self.repeats, time.perf_counter() - self.time_started))
                    self.start()
                else:
                    # worker.main_thread(print, 'No repeats left')
                    self.stop()
        else:
            self.stop()

    # Set time
    def set(self, seconds=0, minutes=0, hours=0):
        pass

    # Add time
    def add(self, seconds=0, minutes=0, hours=0):
        pass

    @property
    def timeleft(self):
        if self.status == STARTED:
            return int(self.time_end - time.perf_counter())  # cast to int?
        return 0

def threaded(fn):
    threaded.callback = lambda *x: None
    threaded.exc_handler = lambda *x: None

    def run(*args, **kw):
        try:
            fn(*args, **kw)
            # result = fn(*args, **kw)
            # worker.main_thread(threaded.callback, result)
        except Exception as e:
            threaded.exc_handler(e, fn.__name__)
            # worker.main_thread()

    def wrapper(*args, **kw):
        worker.queue(run, *args, **kw)

        # if worker.is_main_thread():
        #     worker.queue(run, *args, **kw)
        # else:
        #     run(*args, **kw)
    return wrapper

# =============================================================================
# >> FUNCTIONS
# =============================================================================
def re_raise(exception):
    raise exception

# Get instance to use as singleton
worker = _Worker()

# if __name__ == '__main__':
#     def do_nonsense():
#         print('lol')

#     worker.start(threads=1)
#     worker.repeat(1, do_nonsense, repeats=2, offset=0)
#     worker.delay(2, print, 'hahaha')

#     while True:
#         worker.check_queue()
#         time.sleep(0.01)
