import os
import time
import requests
from typing import Optional

class AssemblyAISTT:
    """
    Speech-to-Text using AssemblyAI API
    Much more accurate than Whisper for Hindi/Marathi
    Free tier: 100 minutes/month
    Requires: ASSEMBLYAI_API_KEY environment variable
    """
    
    def __init__(self, language: str = "hi"):
        """
        Initialize AssemblyAI STT
        Args:
            language: Language code (e.g., "hi" for Hindi, "mr" for Marathi, "en" for English)
        """
        api_key = os.getenv("ASSEMBLYAI_API_KEY")
        if not api_key:
            raise ValueError("[AssemblyAISTT] ERROR: ASSEMBLYAI_API_KEY environment variable not set")
        
        self.api_key = api_key
        self.language = language
        self.base_url = "https://api.assemblyai.com/v2"
        print(f"[AssemblyAISTT] Initialized with language: {language}")
    
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe audio file to text using AssemblyAI
        Returns text in the source language (e.g., Hindi input returns Hindi text)
        The app.py LLM service will handle translation to English
        Args:
            audio_path: Path to audio file (.mp3, .wav, .ogg, etc.)
            language: Optional language code to override default
        Returns:
            Transcribed text in source language
        """
        lang = language or self.language
        print(f"[AssemblyAISTT] Transcribing: {audio_path} (Language: {lang})")
        
        try:
            # Upload file
            print("[AssemblyAISTT] Uploading audio file...")
            headers = {"Authorization": self.api_key}
            
            with open(audio_path, "rb") as f:
                response = requests.post(
                    f"{self.base_url}/upload",
                    headers=headers,
                    data=f,
                    timeout=60
                )
            
            response.raise_for_status()
            upload_url = response.json()["upload_url"]
            print(f"[AssemblyAISTT] File uploaded")
            
            # Request transcription
            print("[AssemblyAISTT] Requesting transcription...")
            transcript_request = {
                "audio_url": upload_url,
                "language_code": lang,
                "language_detection": False,  # Use specified language
            }
            
            response = requests.post(
                f"{self.base_url}/transcript",
                headers=headers,
                json=transcript_request,
                timeout=30
            )
            
            response.raise_for_status()
            transcript_id = response.json()["id"]
            print(f"[AssemblyAISTT] Transcript ID: {transcript_id}")
            
            # Poll for completion
            print("[AssemblyAISTT] Processing...")
            max_retries = 120  # 10 minutes max wait
            retry_count = 0
            
            while retry_count < max_retries:
                response = requests.get(
                    f"{self.base_url}/transcript/{transcript_id}",
                    headers=headers,
                    timeout=30
                )
                
                response.raise_for_status()
                result = response.json()
                
                if result["status"] == "completed":
                    text = result.get("text", "")
                    print(f"[AssemblyAISTT] Transcribed ({lang}): {text[:100]}...")
                    return text
                elif result["status"] == "error":
                    error_msg = result.get("error", "Unknown error")
                    raise Exception(f"[AssemblyAISTT] Transcription error: {error_msg}")
                
                print(f"[AssemblyAISTT] Status: {result['status']}... waiting ({retry_count+1}s)")
                time.sleep(1)
                retry_count += 1
            
            raise TimeoutError("[AssemblyAISTT] Transcription timed out after 10 minutes")
        
        except Exception as e:
            print(f"[AssemblyAISTT] Error: {e}")
            raise RuntimeError(f"AssemblyAI transcription failed: {e}")


# Factory function to create STT service with default language (Hindi)
def get_stt_service(language: str = "hi") -> AssemblyAISTT:
    """
    Create and return an AssemblyAISTT instance with specified language.
    Default is Hindi ("hi").
    Requires ASSEMBLYAI_API_KEY environment variable to be set.
    """
    return AssemblyAISTT(language=language)
