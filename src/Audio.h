#pragma once
// Audio.h -- the engine's ownership of audio playback (#440, #406, #400).
//
// Three jobs, all of which used to be nobody's:
//
//   * Fire-and-forget playback. `mcrfpy.Sound("hit.wav").play()` drops its only
//     wrapper at once. A playing Sound or Music is retained here until it stops, so
//     the C++ object (and its device resources) outlives the wrapper exactly as long
//     as it is audible. Released by sweep(), once per simulation frame.
//   * Audio off (--audio-off, --headless). No device resource is ever created: Sound,
//     Music and SoundBuffer load and report metadata, and play() is a no-op.
//   * Closing the device. Every object holding device resources is tracked, and
//     shutdown() (registered with Py_AtExit, so it runs on sys.exit() too) destroys
//     them all, so OpenAL's own atexit cleanup finds no open device to race on.

#include <memory>
#include <string>

namespace mcrf::audio {

// An object that may hold device resources (an sf::Sound or sf::Music).
class Source {
public:
    Source();
    virtual ~Source();
    Source(const Source&) = delete;
    Source& operator=(const Source&) = delete;

    // True while any of its voices is audible. Paused does not count: a paused,
    // otherwise unreferenced object could never be resumed, so it is not retained.
    virtual bool active() const = 0;
    // Destroy every device resource (stops playback). Called by shutdown().
    virtual void releaseDevice() = 0;
};

// Set from McRogueFaceConfig::audio_enabled before any Python runs.
void configure(bool enabled);

// May a Source create device resources? False when audio is off, and after shutdown().
bool enabled();

// Keep `src` alive until it stops playing. Idempotent. Call after starting playback.
void retain(std::shared_ptr<Source> src);

// Release retained sources that have stopped. Runs where Python may run (the GIL is
// held): dropping the last reference can free a SoundBuffer, whose destructor
// touches the wrapper cache.
void sweep();

// get_metrics(): Sound/Music objects alive, and those of them retained by playback.
std::size_t live_count();
std::size_t retained_count();

// Destroy every Source's device resources and refuse new ones.
void shutdown();

// Check that `path` is a readable audio file and read its duration, without
// creating any device resource. For loading while audio is off.
bool probe_file(const std::string& path, float& seconds);

} // namespace mcrf::audio
