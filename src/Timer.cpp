#include "Timer.h"
#include "PythonObjectCache.h"
#include "PyCallable.h"
#include "McRFPy_API.h"
#include "GameEngine.h"

Timer::Timer(PyObject* _target, int _interval, int now, bool _once, bool _start)
: callback(std::make_shared<PyCallable>(_target)), interval(_interval), last_ran(now),
  paused(false), pause_start_time(0), total_paused_time(0), once(_once), stopped(!_start)
{}

Timer::Timer()
: callback(std::make_shared<PyCallable>(Py_None)), interval(0), last_ran(0),
  paused(false), pause_start_time(0), total_paused_time(0), once(false), stopped(true)
{}

Timer::~Timer() {
    if (serial_number != 0) {
        PythonObjectCache::getInstance().remove(serial_number);
    }
}

bool Timer::hasElapsed(int now) const
{
    if (paused || stopped) return false;
    return now >= last_ran + interval;
}

bool Timer::test(int now)
{
    if (!callback || callback->isNone() || stopped) return false;

    if (hasElapsed(now))
    {
        last_ran = now;

        // Get the PyTimer wrapper from cache to pass to callback
        PyObject* timer_obj = nullptr;
        if (serial_number != 0) {
            timer_obj = PythonObjectCache::getInstance().lookup(serial_number);
        }

        // Build args: (timer, runtime) or just (runtime) if no wrapper found
        PyObject* args;
        if (timer_obj) {
            args = Py_BuildValue("(Oi)", timer_obj, now);
        } else {
            // Fallback to old behavior if no wrapper found
            args = Py_BuildValue("(i)", now);
        }

        PyObject* retval = callback->call(args, NULL);
        Py_DECREF(args);

        if (!retval)
        {
            std::cerr << "Timer callback raised an exception:" << std::endl;
            PyErr_Print();
            PyErr_Clear();

            // Check if we should exit on exception
            if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) {
                McRFPy_API::signalPythonException();
            }
        } else if (retval != Py_None)
        {
            std::cout << "Timer returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
            Py_DECREF(retval);
        }

        // Handle one-shot timers: stop but preserve callback for potential restart
        if (once) {
            stopped = true;  // Will be removed from map by testTimers(), but callback preserved
        }

        return true;
    }
    return false;
}

void Timer::pause(int current_time)
{
    if (!paused) {
        paused = true;
        pause_start_time = current_time;
    }
}

void Timer::resume(int current_time)
{
    if (paused) {
        paused = false;
        int paused_duration = current_time - pause_start_time;
        total_paused_time += paused_duration;
        // Adjust last_ran to account for the pause
        last_ran += paused_duration;
    }
}

void Timer::restart(int current_time)
{
    last_ran = current_time;
    paused = false;
    stopped = false;  // Ensure timer is running
    pause_start_time = 0;
    total_paused_time = 0;
}

void Timer::start(int current_time)
{
    // Start/resume the timer - clear stopped flag, reset progress
    stopped = false;
    paused = false;
    last_ran = current_time;
    pause_start_time = 0;
    total_paused_time = 0;
}

void Timer::stop()
{
    // Stop the timer - it will be removed from engine map, but callback is preserved
    stopped = true;
    paused = false;
    pause_start_time = 0;
    total_paused_time = 0;
}

bool Timer::isActive() const
{
    return callback && !callback->isNone() && !paused && !stopped;
}

int Timer::getRemaining(int current_time) const
{
    if (stopped) {
        // When stopped, progress is reset - full interval remaining
        return interval;
    }
    if (paused) {
        // When paused, calculate time remaining from when it was paused
        int elapsed_when_paused = pause_start_time - last_ran;
        return interval - elapsed_when_paused;
    }
    int elapsed = current_time - last_ran;
    return interval - elapsed;
}

int Timer::getElapsed(int current_time) const
{
    if (stopped) {
        // When stopped, progress is reset
        return 0;
    }
    if (paused) {
        return pause_start_time - last_ran;
    }
    return current_time - last_ran;
}

PyObject* Timer::getCallback()
{
    if (!callback) return Py_None;
    return callback->borrow();
}

void Timer::setCallback(PyObject* new_callback)
{
    callback = std::make_shared<PyCallable>(new_callback);
}