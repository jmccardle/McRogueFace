#include "Audio.h"
#include "Common.h"
#include "Python.h"
#include <algorithm>
#include <unordered_set>
#include <vector>

namespace mcrf::audio {

namespace {

struct Registry {
    bool enabled = true;
    bool shut_down = false;
    bool atexit_registered = false;
    std::unordered_set<Source*> live;
    std::vector<std::shared_ptr<Source>> retained;
};

// Never destroyed: a static destructor would run after Py_Finalize, and releasing a
// retained Sound frees its SoundBuffer, which touches the (finalized) wrapper cache.
Registry& reg()
{
    static Registry* r = new Registry();
    return *r;
}

void shutdown_atexit() { shutdown(); }

} // namespace

Source::Source()
{
    Registry& r = reg();
    r.live.insert(this);
    // Sources are only made from Python, so the interpreter is up. Py_AtExit covers
    // both exits: api_shutdown()'s Py_Finalize, and sys.exit() in an --exec script,
    // which Py_Exit()s straight past `delete engine`.
    if (!r.atexit_registered) {
        r.atexit_registered = true;
        Py_AtExit(shutdown_atexit);
    }
}

Source::~Source()
{
    reg().live.erase(this);
}

void configure(bool enabled)
{
    reg().enabled = enabled;
}

bool enabled()
{
    const Registry& r = reg();
    return r.enabled && !r.shut_down;
}

void retain(std::shared_ptr<Source> src)
{
    if (!src) return;
    auto& v = reg().retained;
    if (std::find(v.begin(), v.end(), src) == v.end()) v.push_back(std::move(src));
}

void sweep()
{
    auto& v = reg().retained;
    if (v.empty()) return;
    // Move the stopped ones out first: destroying a Source erases it from `live`,
    // and must not happen while `retained` is mid-erase.
    std::vector<std::shared_ptr<Source>> done;
    auto keep = std::partition(v.begin(), v.end(),
                               [](const std::shared_ptr<Source>& s) { return s->active(); });
    std::move(keep, v.end(), std::back_inserter(done));
    v.erase(keep, v.end());
}

std::size_t live_count() { return reg().live.size(); }
std::size_t retained_count() { return reg().retained.size(); }

void shutdown()
{
    Registry& r = reg();
    if (r.shut_down) return;
    r.shut_down = true;
    // Release device resources only. The Sources themselves (and the retained
    // references) are left alone: freeing them could run Python-side cleanup
    // after the interpreter is gone, and the process is exiting anyway.
    for (Source* s : r.live) s->releaseDevice();
}

bool probe_file(const std::string& path, float& seconds)
{
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
    // sf::InputSoundFile only decodes; unlike SoundBuffer/Sound/Music it is not an
    // AlResource, so it never opens the device.
    sf::InputSoundFile file;
    if (!file.openFromFile(path)) return false;
    seconds = file.getDuration().asSeconds();
    return true;
#else
    // These backends have no AlResource: their SoundBuffer opens no device.
    sf::SoundBuffer buffer;
    if (!buffer.loadFromFile(path)) return false;
    seconds = buffer.getDuration().asSeconds();
    return true;
#endif
}

} // namespace mcrf::audio
