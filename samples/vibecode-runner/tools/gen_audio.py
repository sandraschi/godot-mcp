#!/usr/bin/env python3
"""Generate all procedural audio for Vibecoder Runner.

Zero external assets: every sound is synthesized (square/saw/sine/noise)
and written as 16-bit mono WAVs into samples/vibecode-runner/audio/.

Usage:  uv run python tools/gen_audio.py   (or plain python3)

Outputs are committed so Godot can load them at runtime on web exports
(no runtime synthesis needed).
"""

from __future__ import annotations

import math
import os
import random
import struct
import wave

RATE = 22050
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "audio")


def _samples(seconds: float) -> int:
    return int(seconds * RATE)


def _write(name: str, data: list[float], peak: float = 0.9) -> None:
    if peak > 0:
        m = max(1e-9, max(abs(v) for v in data))
        scale = peak / m
        data = [v * scale for v in data]
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        frames = bytearray()
        for v in data:
            v = max(-1.0, min(1.0, v))
            frames += struct.pack("<h", int(v * 32767))
        w.writeframes(bytes(frames))
    print(f"  wrote {name} ({len(data) / RATE:.2f}s, {os.path.getsize(path)} bytes)")


def env(i: int, n: int, attack: float = 0.01, release: float = 0.15) -> float:
    t = i / n
    a = min(1.0, t / max(attack, 1e-6))
    r = min(1.0, (1.0 - t) / max(release, 1e-6))
    return max(0.0, min(a, r))


def tone(freq_from: float, freq_to: float, dur: float, wave_fn, vol=0.5, attack=0.01, release=0.12) -> list[float]:
    n = _samples(dur)
    out = []
    for i in range(n):
        t = i / n
        f = freq_from + (freq_to - freq_from) * t
        phase = 2.0 * math.pi * f * (i / RATE)
        out.append(vol * wave_fn(phase) * env(i, n, attack, release))
    return out


def noise_burst(dur: float, cutoff: float = 0.5, vol=0.4, attack=0.005, release=0.2) -> list[float]:
    n = _samples(dur)
    rng = random.Random(1337)
    low = [rng.uniform(-1, 1) for _ in range(n)]
    # cheap one-pole lowpass
    prev = 0.0
    out = []
    alpha = max(0.0, min(1.0, cutoff))
    for i in range(n):
        prev = prev + alpha * (low[i] - prev)
        out.append(prev * vol * env(i, n, attack, release))
    return out


def mix(*tracks: list[float]) -> list[float]:
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def silence(dur: float) -> list[float]:
    return [0.0] * _samples(dur)


def sq(phase: float) -> float:
    return 1.0 if math.sin(phase) >= 0 else -1.0


def tri(phase: float) -> float:
    return 2.0 / math.pi * math.asin(math.sin(phase))


def saw(phase: float) -> float:
    return 2.0 * ((phase / (2.0 * math.pi)) % 1.0) - 1.0


# ---------------------------------------------------------------- SFX

def gen_jump() -> list[float]:
    return tone(280, 620, 0.14, sq, vol=0.35, release=0.08)


def gen_land() -> list[float]:
    return noise_burst(0.09, cutoff=0.35, vol=0.3, release=0.09)


def gen_drink() -> list[float]:
    notes = [523.25, 659.25, 783.99, 1046.5]  # C5 E5 G5 C6
    out: list[float] = []
    for f in notes:
        out += tone(f, f, 0.09, sq, vol=0.3, release=0.06)
        out += silence(0.015)
    return out


def gen_ship() -> list[float]:
    whoosh = noise_burst(0.35, cutoff=0.7, vol=0.35, release=0.3)
    rise = tone(200, 900, 0.35, saw, vol=0.18, release=0.3)
    return mix(whoosh, rise)


def gen_hit() -> list[float]:
    crash = noise_burst(0.3, cutoff=0.9, vol=0.5, release=0.28)
    drop = tone(220, 55, 0.35, saw, vol=0.3, release=0.3)
    return mix(crash, drop)


def gen_stun() -> list[float]:
    a = tone(520, 300, 0.12, sq, vol=0.3, release=0.08)
    b = tone(300, 180, 0.16, sq, vol=0.3, release=0.1)
    return a + b


def gen_drain() -> list[float]:
    return tone(700, 160, 0.22, saw, vol=0.22, release=0.18)


def gen_coin() -> list[float]:
    return tone(880, 1320, 0.1, tri, vol=0.3, release=0.05)


def gen_boss_alarm() -> list[float]:
    a = tone(392, 392, 0.16, sq, vol=0.35, release=0.1)  # G4
    b = tone(311, 311, 0.16, sq, vol=0.35, release=0.1)  # Eb4
    out: list[float] = []
    for _ in range(2):
        out += a + silence(0.05) + b + silence(0.05)
    return out


def gen_boss_hit() -> list[float]:
    return tone(140, 90, 0.18, sq, vol=0.4, release=0.12)


def gen_over() -> list[float]:
    a = tone(330, 300, 0.3, tri, vol=0.3, release=0.25)
    b = tone(220, 180, 0.45, tri, vol=0.3, release=0.4)
    c = tone(165, 110, 0.7, tri, vol=0.3, release=0.6)
    return a + b + c


def gen_click() -> list[float]:
    return tone(1200, 900, 0.045, sq, vol=0.2, release=0.03)


def gen_start() -> list[float]:
    notes = [261.63, 329.63, 392.0, 523.25]  # C4 E4 G4 C5
    out: list[float] = []
    for f in notes:
        out += tone(f, f, 0.1, sq, vol=0.28, release=0.07)
        out += silence(0.02)
    return out


def gen_powerup() -> list[float]:
    return tone(440, 880, 0.25, tri, vol=0.3, release=0.2)


def gen_teleport() -> list[float]:
    return tone(1400, 300, 0.2, tri, vol=0.22, release=0.18)


# ---------------------------------------------------------------- Music loop

NOTE = 60.0 / 116.0  # 116 BPM


def note_freq(midi: int) -> float:
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def _note(dur: float, midi: int, wave_fn, vol: float, attack=0.02, release=0.3) -> list[float]:
    return tone(note_freq(midi), note_freq(midi), dur, wave_fn, vol=vol, attack=attack, release=release)


def gen_music() -> list[float]:
    """16-bar loop, A minor: bass (A2 G2 F2 E2), hat ticks, arp melody."""
    bar = int(RATE * NOTE * 4)
    total = bar * 8
    bass: list[float] = [0.0] * total
    hats: list[float] = [0.0] * total
    arp: list[float] = [0.0] * total

    prog = [45, 43, 41, 40]  # A2 G2 F2 E2
    rng = random.Random(20260731)
    t = 0
    b = 0
    while t + bar <= total:
        root = prog[b % 4]
        # bass: two half-notes per bar
        for half in range(2):
            n = int(NOTE * 2 * RATE)
            if t + n <= total:
                seg = _note(NOTE * 2, root, sq, 0.22)
                for i, v in enumerate(seg):
                    bass[t + i] += v
            t += n
        # hats: 8th-note noise ticks
        for e in range(8):
            idx = int((b * bar) + e * (bar / 8))
            if idx + int(0.03 * RATE) < total:
                tick = noise_burst(0.03, cutoff=0.85, vol=0.12, release=0.02)
                for i, v in enumerate(tick):
                    hats[idx + i] += v
        b += 1

    # arp: sparse 16th pattern over the loop
    arp_pat = [57, 60, 64, 67, 64, 60, 57, 60, 62, 65, 69, 65, 62, 65, 62, 60]
    steps = 16
    step_len = bar / steps
    for s in range(steps * 8):
        midi = arp_pat[s % len(arp_pat)]
        idx = int(s * step_len * RATE)
        if idx + int(0.12 * RATE) < total and rng.random() < 0.75:
            seg = _note(step_len * 0.9, midi, tri, 0.12, attack=0.01, release=0.1)
            for i, v in enumerate(seg):
                if idx + i < total:
                    arp[idx + i] += v

    return mix(bass, hats, arp)


def main() -> None:
    print("Generating Vibecoder Runner audio...")
    _write("jump.wav", gen_jump())
    _write("land.wav", gen_land())
    _write("drink.wav", gen_drink())
    _write("ship.wav", gen_ship())
    _write("hit.wav", gen_hit())
    _write("stun.wav", gen_stun())
    _write("drain.wav", gen_drain())
    _write("coin.wav", gen_coin())
    _write("boss_alarm.wav", gen_boss_alarm())
    _write("boss_hit.wav", gen_boss_hit())
    _write("over.wav", gen_over())
    _write("click.wav", gen_click())
    _write("start.wav", gen_start())
    _write("powerup.wav", gen_powerup())
    _write("teleport.wav", gen_teleport())
    _write("music.wav", gen_music())
    print("Done.")


if __name__ == "__main__":
    main()
