#include "Timer.h"
#include "PythonObjectCache.h"
#include "PyWrap.h"
#include "PyCallable.h"
#include "McRFPy_API.h"
#include "GameEngine.h"

Timer::Timer(PyObject* _target, int _interval, int now, bool _once, bool _start, const std::string& _name)
: callback(std::make_shared<PyCallable>(_target)), interval(_interval), last_ran(now),
  paused(false), pause_start_time(0), total_paused_time(0), once(_once), stopped(!_start), name(_name)
{}

Timer::Timer()
: callback(std::make_shared<PyCallable>(Py_None)), interval(0), last_ran(0),
  paused(false), pause_start_time(0), total_paused_time(0), once(false), stopped(true)
{}

Timer::~Timer() {
    releasePyWrapper();
    if (serial_number != 0) {
        mcrf::unregister_wrapper(serial_number);
    }
}

void Timer::retainPyWrapper(PyObject* wrapper) {
    if (py_wrapper == wrapper) return;  // Already held
    Py_XDECREF(py_wrapper);
    py_wrapper = wrapper;
    Py_XINCREF(py_wrapper);
}

void Timer::releasePyWrapper() {
    // Null first: the wrapper's dealloc can drop the last reference to this Timer.
    PyObject* w = py_wrapper;
    py_wrapper = nullptr;
    if (mcrf::python_alive()) Py_XDECREF(w);  // #468
}

bool Timer::hasElapsed(int now) const
{
    if (paused || stopped) return false;
    return now >= last_ran + interval;
}

bool Timer::test(int now)
{
    // #397 - Catch up: fire once per interval that has elapsed by `now`, each firing
    // stamped with its own deadline. last_ran advances by exactly one interval per firing,
    // so a timer keeps its phase across a wide step or a stalled frame instead of being
    // re-phased to the frame that noticed it (the old `last_ran = now`). The loop re-checks
    // hasElapsed() after every call, so a callback that stops, pauses, restarts or
    // re-intervals the timer takes effect immediately. A raising callback ends this frame's
    // catch-up (one traceback per timer per frame); the remaining deadlines are still owed
    // and fire on the next frame.
    bool fired = false;
    while (callback && !callback->isNone() && hasElapsed(now))
    {
        const int deadline = last_ran + interval;
        last_ran = deadline;

        // The callback receives (timer, runtime). Every Timer is created by PyTimer::init,
        // which registers its wrapper, and a running timer retains it (#251), so a missing
        // wrapper is an engine bug: report it instead of calling with another signature.
        mcrf::PyRef timer_obj(mcrf::live_wrapper(serial_number));
        if (!timer_obj) {
            PyErr_Format(PyExc_RuntimeError, "Timer '%s' fired without its Python object",
                         name.c_str());
            PyErr_Print();
            return fired;
        }
        mcrf::PyRef args(Py_BuildValue("(Oi)", timer_obj.get(), deadline));
        if (!args) {
            PyErr_Print();
            return fired;
        }

        // Hold the callable for the call: the callback may replace timer.callback.
        auto cb = callback;
        mcrf::PyRef retval(cb->call(args.get(), NULL));
        fired = true;

        if (!retval)
        {
            mcrf::print_callback_error("Timer");
            PyErr_Clear();

            // Check if we should exit on exception
            if (McRFPy_API::game && McRFPy_API::game->getConfig().exit_on_exception) {
                McRFPy_API::signalPythonException();
            }
        } else if (retval.get() != Py_None)
        {
            std::cout << "Timer returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
        }

        // Handle one-shot timers: stop but preserve callback for potential restart
        if (once) {
            stopped = true;  // Will be removed from map by testTimers(), but callback preserved
            releasePyWrapper();  // Allow Python GC now (#251)
            break;
        }
        if (!retval) break;
    }
    return fired;
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
    releasePyWrapper();  // Allow Python GC now that timer is inactive (#251)
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

int Timer::visitCallback(visitproc visit, void* arg) const
{
    // Only a callable this timer alone holds: test() copies it for the duration of a call.
    if (!callback || callback.use_count() != 1) return 0;
    PyObject* fn = callback->borrow();
    if (fn && fn != Py_None) Py_VISIT(fn);
    return 0;
}

void Timer::setCallback(PyObject* new_callback)
{
    callback = std::make_shared<PyCallable>(new_callback);
}