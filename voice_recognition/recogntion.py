import sounddevice as sd
import soundfile as sf
import torch
from qdrant_client import QdrantClient, models
from icecream import ic
import numpy as np
from pyannote.audio import Pipeline, Inference
import os
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env file

# Using os.getenv()
huggingface = os.getenv("HUGGING_FACE")



# Record 5 seconds audio
duration = 5  # seconds
sample_rate = 16000
filename = "temp.wav"

print("Recording for 5 seconds...")
audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")
sd.wait()
sf.write(filename, audio, sample_rate)
print("Audio saved to", filename)


# diarization pipeline (if you still want diarization)
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-community-1",
    token=huggingface,
)

device = torch.device(
    "mps" if torch.backends.mps.is_available()
    else "cuda" if torch.cuda.is_available()
    else "cpu"
)
pipeline.to(device)
audiopath = "temp.wav"
speakername = audiopath.split(".")[0]
# run diarization and get one embedding per speaker
output = pipeline(audiopath, return_embeddings=True)  # returns (diarization, np.ndarray)[web:9]

embedding = output.speaker_embeddings[0]

ic(embedding.shape)

# Convert embedding to list for Qdrant query
embedding_vector = embedding.tolist()

# Setup Qdrant client
client = QdrantClient("http://localhost:6333")




# Query Qdrant with the generated embedding
collection_name = "voicesinmyhead"

try:
        client.create_collection(
        collection_name="{collection_name}",
        vectors_config=models.VectorParams(size=100, distance=models.Distance.COSINE),
    )
except Exception as e:
    print("Collection might already exist:", e)
    


query_result = client.query_points(
    collection_name=collection_name,
    query=embedding_vector,
    limit=5  # top 5 nearest neighbors
)

ic(query_result)
