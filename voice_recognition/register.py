import torch
from pyannote.audio import Pipeline, Inference
from icecream import ic
from qdrant_client import QdrantClient, models
import uuid
import os
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env file

# Using os.getenv()
huggingface = os.getenv("HUGGING_FACE")


client = QdrantClient("http://localhost:6333")


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
audiopath = "sahitya.wav"
speakername = audiopath.split(".")[0]
# run diarization and get one embedding per speaker
output = pipeline(audiopath, return_embeddings=True)  # returns (diarization, np.ndarray)[web:9]


ic(output.speaker_embeddings)  # prints dict {speaker_label: embedding_array}

ic(len(output.speaker_embeddings[0]))  # prints number of unique speakers detected

speaker_id = str(uuid.uuid4())

operation_info = client.upsert(
    collection_name="voicesinmyhead",
    points=[
        models.PointStruct(
            id=speaker_id,
            vector=output.speaker_embeddings[0].tolist(),
            payload={"speaker": speakername},
        )
    ]
)
print("Upserted:", operation_info)