import sounddevice as sd
import soundfile as sf

duration = 5  # seconds
sample_rate = 16000
output_file = "anish.wav"

print("Recording...")
audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
sd.wait()
print("Done.")
sf.write(output_file, audio, sample_rate)
