import torch
from pyannote.audio import Inference, Model
from qdrant_client import QdrantClient, models
import uuid
import os
from dotenv import load_dotenv
import numpy as np
import argparse

# Load environment variables
load_dotenv()
HUGGINGFACE_TOKEN = os.getenv("HUGGING_FACE")

# Setup device
device = torch.device(
    "mps" if torch.backends.mps.is_available()
    else "cuda" if torch.cuda.is_available()
    else "cpu"
)

# Initialize Qdrant client
client = QdrantClient("http://localhost:6333")

# Initialize embedding model
embedding_model = Model.from_pretrained("pyannote/embedding", token=HUGGINGFACE_TOKEN).to(device)
embedder = Inference(embedding_model, window="whole")

def embed_and_store(audio_path: str, collection_name: str = "speaker_embeddings"):
    speaker_name = os.path.splitext(os.path.basename(audio_path))[0]

    # Compute embedding
    with torch.no_grad():
        embedding = embedder(audio_path)

    if isinstance(embedding, torch.Tensor):
        emb = embedding.detach().cpu().numpy().reshape(-1)
    else:
        emb = np.asarray(embedding, dtype=np.float32).reshape(-1)

    emb = np.nan_to_num(emb, nan=0.0)
    embedding_vector = emb.tolist()
    speaker_id = str(uuid.uuid4())

    # Create collection if it doesn't exist
    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=len(embedding_vector), distance=models.Distance.COSINE),
        )
    except Exception as e:
        print("Collection might already exist:", e)

    # Upsert embedding
    operation_info = client.upsert(
        collection_name=collection_name,
        points=[models.PointStruct(id=speaker_id, vector=embedding_vector, payload={"speaker": speaker_name})]
    )
    print("Upserted into the database ✅:", operation_info)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embed a WAV file and store the speaker embedding in Qdrant.")
    parser.add_argument("wav_file", type=str, help="Path to the WAV file to embed")
    args = parser.parse_args()

    embed_and_store(args.wav_file)
