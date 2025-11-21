import assemblyai as aai
import os

# --- Configuration ---
# ⚠️ UPDATE THIS: Set the path or public URL of your Hindi audio file
# Example: Use a public URL
AUDIO_FILE_PATH = "agents/vendor-agent/uploads/vendor_voice.mp3" 
# Example: Use a local file path
# AUDIO_FILE_PATH = "./my_hindi_speech.mp3" 

OUTPUT_FILENAME = "transcribed_hindi_output.txt"
HINDI_LANGUAGE_CODE = "hi" # Set for Hindi Transcription

# --- Script ---
def transcribe_and_save():
    """Transcribes Hindi audio using AssemblyAI and saves the Hindi text to a file."""
    try:
        if not os.getenv("ASSEMBLYAI_API_KEY"):
            print("ERROR: ASSEMBLYAI_API_KEY environment variable not set.")
            return

        print(f"Starting transcription for: {AUDIO_FILE_PATH}...")
        print(f"**Target Language: Hindi (Code: {HINDI_LANGUAGE_CODE})**")
        
        transcriber = aai.Transcriber()
        
        # Configure transcription to specifically use the Hindi language model
        config = aai.TranscriptionConfig(
            language_code=HINDI_LANGUAGE_CODE
        )

        transcript = transcriber.transcribe(AUDIO_FILE_PATH, config=config)

        if transcript.status == aai.TranscriptStatus.error:
            print(f"Transcription failed: {transcript.error}")
        else:
            transcribed_text = transcript.text
            with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
                f.write(transcribed_text)
            
            print("--- Transcription Complete ---")
            print(f"Status: {transcript.status.value}")
            print(f"Hindi Text saved to: **{OUTPUT_FILENAME}**")
            print("-" * 30)
            print(f"Preview: {transcribed_text[:200]}" + ("..." if len(transcribed_text) > 200 else ""))

    except Exception as e:
        print(f"An error occurred during transcription: {e}")

if __name__ == "__main__":
    transcribe_and_save()