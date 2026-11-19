#!/usr/bin/env python3
"""Generate an upbeat, professional commercial background music bed.

Generates a 60-second, 44.1kHz stereo audio track with:
- 120 BPM four-on-the-floor kick
- Snappy side-stick / clap on beats 2 & 4
- Tight 16th-note hi-hat groove
- Melodic synth-bassline in A minor
- Plucked synth chords (Am - F - C - G progression)
- Subtle reverse sweep / riser into drops
- Smooth fadeout at 59-60s
"""

import math
import struct
import wave

SAMPLE_RATE = 44100
DURATION = 60.0
BPM = 120
BEAT_LEN = 60.0 / BPM  # 0.5 sec per beat
TOTAL_SAMPLES = int(SAMPLE_RATE * DURATION)


def synth_kick(t: float) -> float:
    if t > 0.25:
        return 0.0
    f = 140.0 * math.exp(-t * 28.0) + 45.0
    amp = math.exp(-t * 14.0)
    return math.sin(2.0 * math.pi * f * t) * amp * 0.9


def synth_hat(t: float) -> float:
    if t > 0.05:
        return 0.0
    # pseudo-noise using high-frequency sine superposition
    noise = (
        math.sin(2.0 * math.pi * 7800.0 * t) * 0.4
        + math.sin(2.0 * math.pi * 9200.0 * t) * 0.3
        + math.sin(2.0 * math.pi * 11500.0 * t) * 0.3
    )
    amp = math.exp(-t * 80.0)
    return noise * amp * 0.25


def synth_clap(t: float) -> float:
    if t > 0.15:
        return 0.0
    noise = (
        math.sin(2.0 * math.pi * 1200.0 * t) * 0.4
        + math.sin(2.0 * math.pi * 2400.0 * t) * 0.3
        + math.sin(2.0 * math.pi * 3600.0 * t) * 0.3
    )
    amp = math.exp(-t * 22.0)
    return noise * amp * 0.35


def chord_freqs(bar: int) -> list[float]:
    prog = [
        [220.0, 261.63, 329.63],  # Am (A3, C4, E4)
        [174.61, 220.0, 261.63],  # F (F3, A3, C4)
        [261.63, 329.63, 392.00],  # C (C4, E4, G4)
        [196.00, 246.94, 293.66],  # G (G3, B3, D4)
    ]
    return prog[bar % 4]


def bass_freq(bar: int) -> float:
    roots = [55.0, 43.65, 65.41, 49.00]  # A1, F1, C2, G1
    return roots[bar % 4]


def main():
    out_file = r"C:\Users\tee\.gemini\antigravity-ide\scratch\hermes-agent\bgm.wav"
    samples_left = []
    samples_right = []

    for i in range(TOTAL_SAMPLES):
        t = i / SAMPLE_RATE
        beat_idx = int(t / BEAT_LEN)
        beat_phase = (t % BEAT_LEN)
        bar_idx = beat_idx // 4

        # 1. Kick on every beat
        k = synth_kick(beat_phase) if t < 58.0 else 0.0

        # 2. Clap on beats 2 and 4 (beat_idx % 2 == 1)
        cl = synth_clap(beat_phase) if (beat_idx % 2 == 1 and t < 58.0 and t >= 4.0) else 0.0

        # 3. 16th-note Hi-hats
        sub_phase = (t % (BEAT_LEN / 4.0))
        h = synth_hat(sub_phase) if (t >= 2.0 and t < 58.0) else 0.0

        # 4. Bassline: 8th note rhythm
        b_sub = (t % (BEAT_LEN / 2.0))
        bf = bass_freq(bar_idx)
        bass_env = math.exp(-b_sub * 7.0)
        bass = (math.sin(2.0 * math.pi * bf * t) + 0.3 * math.sin(4.0 * math.pi * bf * t)) * bass_env * 0.35 if (t >= 4.0 and t < 58.0) else 0.0

        # 5. Plucked Chords: 8th note pulse with stereo spread
        cf = chord_freqs(bar_idx)
        chord_l = 0.0
        chord_r = 0.0
        if t >= 8.0 and t < 58.0:
            chord_env = math.exp(-b_sub * 12.0)
            chord_l = (math.sin(2.0 * math.pi * cf[0] * t) * 0.5 + math.sin(2.0 * math.pi * cf[1] * t) * 0.5) * chord_env * 0.22
            chord_r = (math.sin(2.0 * math.pi * cf[1] * t) * 0.5 + math.sin(2.0 * math.pi * cf[2] * t) * 0.5) * chord_env * 0.22

        # Master mix
        sig_l = (k * 0.8) + (cl * 0.6) + (h * 0.4) + (bass * 0.7) + chord_l
        sig_r = (k * 0.8) + (cl * 0.6) + (h * 0.4) + (bass * 0.7) + chord_r

        # Ducking when voiceover / master fade out
        # Master volume fade out last 3 seconds
        if t > 57.0:
            fade = max(0.0, (60.0 - t) / 3.0)
            sig_l *= fade
            sig_r *= fade

        # Soft clip
        sig_l = max(-0.95, min(0.95, sig_l * 0.32))
        sig_r = max(-0.95, min(0.95, sig_r * 0.32))

        samples_left.append(int(sig_l * 32767))
        samples_right.append(int(sig_r * 32767))

    with wave.open(out_file, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        raw = bytearray()
        for sl, sr in zip(samples_left, samples_right):
            raw.extend(struct.pack("<hh", sl, sr))
        wf.writeframes(raw)

    print("BGM generated:", out_file)


if __name__ == "__main__":
    main()
