import os
import httpx
from io import BytesIO
from pydub import AudioSegment
import uuid

# Configuration constants
SAMPLE_RATE = 16000
CHANNELS = 1
AUDIO_FORMAT = "wav" # We normalize everything to PCM WAV

class AudioProcessor:
    def __init__(self, meta_access_token: str):
        self.meta_access_token = meta_access_token
        self.output_dir = os.path.join(os.getcwd(), "storage", "audio")
        os.makedirs(self.output_dir, exist_ok=True)

    async def download_from_meta(self, media_url: str) -> BytesIO:
        """
        Downloads the media file from Meta WhatsApp Cloud API
        """
        headers = {
            "Authorization": f"Bearer {self.meta_access_token}"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(media_url, headers=headers)
            response.raise_for_status()
            return BytesIO(response.content)

    def normalize_audio(self, input_bytes: BytesIO, input_format: str = "ogg") -> str:
        """
        FR-AUD-005: Normalizes audio to linear PCM 16-bit, mono channel, 16,000 Hz.
        Returns the path to the normalized file.
        """
        # Load audio from memory
        audio = AudioSegment.from_file(input_bytes, format=input_format)
        
        # Apply normalization transformations
        audio = audio.set_frame_rate(SAMPLE_RATE)
        audio = audio.set_channels(CHANNELS)
        audio = audio.set_sample_width(2) # 16-bit
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.{AUDIO_FORMAT}"
        output_path = os.path.join(self.output_dir, filename)
        
        # Export as WAV (PCM)
        audio.export(output_path, format=AUDIO_FORMAT)
        return output_path

    def apply_noise_suppression(self, filepath: str) -> str:
        """
        FR-AUD-003: Applies DeepFilterNet to remove ambient environmental noise.
        This is a placeholder for the actual deep learning inference.
        In a real scenario, we'd invoke the DeepFilterNet ONNX model or binary here.
        """
        print(f"[Placeholder] Applying DeepFilterNet to {filepath}")
        # Stub: normally returns a new filepath to the cleaned audio
        return filepath

    def apply_vad(self, filepath: str) -> bool:
        """
        FR-AUD-004: Silero VAD to segment speech intervals.
        Returns False if less than 1.0 second of valid voice data exists.
        This is a placeholder.
        """
        print(f"[Placeholder] Running Silero VAD on {filepath}")
        # Stub: Assume the file has valid speech for now
        return True

    async def process_pipeline(self, media_url: str, input_format: str = "ogg") -> str:
        """
        Orchestrates the full audio ingestion and pre-processing pipeline.
        """
        # 1. Download
        audio_bytes = await self.download_from_meta(media_url)
        
        # 2. Normalize
        normalized_path = self.normalize_audio(audio_bytes, input_format)
        
        # 3. Suppress Noise
        clean_path = self.apply_noise_suppression(normalized_path)
        
        # 4. Voice Activity Detection
        has_speech = self.apply_vad(clean_path)
        if not has_speech:
            raise ValueError("Audio file contains less than 1.0 second of valid voice.")
            
        return clean_path
