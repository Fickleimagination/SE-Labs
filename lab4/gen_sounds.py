import wave
import struct
import math

def make_beep(filename, freq, duration, volume=0.5, sample_rate=44100):
    n_samples = int(sample_rate * duration)
    with wave.open(filename, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            envelope = 1.0 - (i / n_samples)
            sample = volume * envelope * math.sin(2 * math.pi * freq * t)
            f.writeframes(struct.pack("<h", int(sample * 32767)))

make_beep("sounds/whack.wav", freq=880, duration=0.12)
make_beep("sounds/miss.wav", freq=220, duration=0.15)
make_beep("sounds/round_end.wav", freq=440, duration=0.6)

print("Generated sounds/whack.wav, sounds/miss.wav, sounds/round_end.wav")
