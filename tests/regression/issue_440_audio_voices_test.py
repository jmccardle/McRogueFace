#!/usr/bin/env python3
"""
Audio ownership: fire-and-forget playback, audio off, and device teardown.

  #440  Sound/Music had no tp_dealloc, so every one leaked, and that leak was the only
        thing keeping `Sound(...).play()` playing. The engine now retains a playing
        sound until it stops, and frees it then.
  #407  play_varied() set the drawn pitch/volume, played, and restored them at once;
        OpenAL applies both live, so the variation never sounded. It now plays on its
        own voice and leaves the object's settings alone.
  #406  --audio-off (and --headless, which implies it) was never read: audio played
        anyway. Now no device is opened at all, and play() is a no-op.
  #400  An audio device was always left open at exit (an unused sf::Music member on
        GameEngine opened one at startup, and sys.exit() skips engine teardown), so
        OpenAL's own exit cleanup raced its mixer thread and sometimes aborted.

Each scenario runs in a child engine (sys.executable is the mcrogueface binary),
because audio-on vs audio-off is a command-line choice and #400 is about the exit.
"""
import os
import subprocess
import sys
import tempfile
import wave

failures = []


def check(cond, msg):
    print(("  ok: " if cond else "FAIL: ") + msg)
    if not cond:
        failures.append(msg)


PRELUDE = r'''
import mcrfpy, os, sys, time
def metrics():
    m = mcrfpy.get_metrics()
    return m["audio_sources"], m["audio_playing"]
def threads():
    return len(os.listdir("/proc/self/task"))
def run_until_quiet(limit=3.0):
    t0 = time.monotonic()
    while metrics()[1] and time.monotonic() - t0 < limit:
        time.sleep(0.01)
        mcrfpy.step(0.01)
def report(**kw):
    for k, v in kw.items():
        print("R %s=%r" % (k, v))
'''


def run(body, *flags, wav=None):
    """Run PRELUDE+body in a child engine; return (returncode, stderr, results)."""
    with tempfile.TemporaryDirectory() as d:
        script = os.path.join(d, "child.py")
        with open(script, "w") as f:
            f.write(PRELUDE + "WAV = %r\n" % wav + body + "\nsys.exit(0)\n")
        env = dict(os.environ, ALSOFT_DRIVERS="null")
        p = subprocess.run([sys.executable, *flags, "--exec", script],
                           capture_output=True, text=True, timeout=60, env=env)
    results = {}
    for line in p.stdout.splitlines():
        if line.startswith("R "):
            k, _, v = line[2:].partition("=")
            results[k] = eval(v)
    if p.returncode != 0:
        print(p.stdout[-2000:], p.stderr[-2000:])
    return p.returncode, p.stderr, results


def make_wav(path, seconds=0.2, rate=22050):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x10" * int(seconds * rate))


FIRE_AND_FORGET = r'''
b = mcrfpy.SoundBuffer.tone(440, 0.2)
mcrfpy.Sound(b).play()
playing_after_drop = metrics()
run_until_quiet()
report(playing_after_drop=playing_after_drop, after_finish=metrics())
'''

VARIED = r'''
b = mcrfpy.SoundBuffer.tone(440, 0.2)
s = mcrfpy.Sound(b)
s.pitch, s.volume = 1.0, 50.0
drawn = s.play_varied(pitch_range=0.3, volume_range=10.0)
voices = metrics()[1]
s.play_varied(); s.play_varied()
report(drawn=drawn, pitch=s.pitch, volume=s.volume, main_playing=s.playing, voices=voices)
s.stop()
mcrfpy.step(0.01)
report(after_stop=metrics()[1])
'''

EXIT_WHILE_PLAYING = r'''
s = mcrfpy.Sound(mcrfpy.SoundBuffer.tone(440, 0.2))
s.loop = True
s.play(); s.play_varied()
m = mcrfpy.Music(WAV); m.loop = True; m.play()
report(playing=metrics()[1])
'''

AUDIO_OFF = r'''
before = threads()
b = mcrfpy.SoundBuffer.tone(440, 0.25)
s = mcrfpy.Sound(b)
fs = mcrfpy.Sound(WAV)
fb = mcrfpy.SoundBuffer(WAV)
m = mcrfpy.Music(WAV)
s.play(); fs.play(); m.play()
drawn = s.play_varied()
s.volume = 30.0; m.position = 0.1
report(new_threads=threads() - before, playing=(s.playing, fs.playing, m.playing),
       retained=metrics()[1], drawn=drawn, volume=s.volume, music_pos=m.position,
       durations=(round(s.duration, 3), round(fs.duration, 3), round(fb.duration, 3),
                  round(m.duration, 3)))
del s, fs, m
report(sources_after_del=metrics()[0])
'''

AUDIO_ON_OPENS = r'''
before = threads()
s = mcrfpy.Sound(mcrfpy.SoundBuffer.tone(440, 0.1))
s.play()
report(new_threads=threads() - before, playing=s.playing)
'''


def main():
    with tempfile.TemporaryDirectory() as d:
        wav = os.path.join(d, "clip.wav")
        make_wav(wav)

        print("#440 fire-and-forget plays to the end, then is freed")
        rc, err, r = run(FIRE_AND_FORGET, "--headless", "--audio-on")
        check(rc == 0, "child exited cleanly")
        check(r.get("playing_after_drop") == (1, 1),
              "Sound(...).play() is retained after its wrapper is dropped: %r"
              % (r.get("playing_after_drop"),))
        check(r.get("after_finish") == (0, 0),
              "and released and freed once it finished: %r" % (r.get("after_finish"),))

        print("#407 play_varied plays its own voice")
        rc, err, r = run(VARIED, "--headless", "--audio-on")
        check(rc == 0, "child exited cleanly")
        check(r.get("pitch") == 1.0 and r.get("volume") == 50.0,
              "the object's pitch/volume are untouched: %r/%r" % (r.get("pitch"), r.get("volume")))
        check(r.get("main_playing") is False and r.get("voices") == 1,
              "the varied voice is playing on its own, not as the object's voice")
        d_pitch, d_vol = r.get("drawn", (1.0, 50.0))
        check(abs(d_pitch - 1.0) <= 0.3 + 1e-6 and abs(d_vol - 50.0) <= 10.0 + 1e-6,
              "the drawn values are in range: %r" % (r.get("drawn"),))
        check(r.get("after_stop") == 0, "stop() also stops the varied voices")

        print("#400 exit with sounds and music still playing closes the device")
        for i in range(5):
            rc, err, r = run(EXIT_WHILE_PLAYING, "--headless", "--audio-on", wav=wav)
            if rc != 0 or "AL lib" in err:
                break
        check(r.get("playing") == 2, "a looping Sound and Music were playing at exit")
        check(rc == 0 and "AL lib" not in err,
              "5 exits via sys.exit(): no OpenAL complaint (%r)" % (err.strip()[-200:],))

        print("#406 audio off opens no device and plays nothing")
        rc, err, r = run(AUDIO_OFF, "--headless", wav=wav)
        check(rc == 0, "child exited cleanly")
        check(r.get("new_threads") == 0,
              "no audio device thread was started: +%r" % (r.get("new_threads"),))
        check(r.get("playing") == (False, False, False) and r.get("retained") == 0,
              "play() is a no-op: %r" % (r.get("playing"),))
        check(isinstance(r.get("drawn"), tuple), "play_varied still draws from the AUDIO stream")
        check(r.get("volume") == 30.0 and abs(r.get("music_pos", 0) - 0.1) < 1e-6,
              "settings are kept on the object")
        check(r.get("durations") == (0.25, 0.2, 0.2, 0.2),
              "metadata loads without a device: %r" % (r.get("durations"),))
        check(r.get("sources_after_del") == 0, "dropped Sound/Music objects are freed")

        print("#406 --audio-on wins over --headless in either order")
        for flags in (("--headless", "--audio-on"), ("--audio-on", "--headless")):
            rc, err, r = run(AUDIO_ON_OPENS, *flags)
            check(r.get("playing") is True and r.get("new_threads", 0) > 0,
                  "%s: audio is on (%r)" % (" ".join(flags), r))
        rc, err, r = run(AUDIO_ON_OPENS, "--audio-off")
        check(r.get("playing") is False and r.get("new_threads") == 0,
              "--audio-off without --headless: audio is off (%r)" % (r,))

    if failures:
        print("FAIL: %d check(s) failed" % len(failures))
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
