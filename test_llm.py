from ollama import Client

# --- Configuration ---
INPUT_FILENAME = "transcribed_hindi_output.txt"
OUTPUT_FILENAME = "translated_english_output.txt"
OLLAMA_MODEL = 'llama3.2' # Requires 'ollama pull llama3.2'
OLLAMA_HOST = 'http://localhost:11434' # Default Ollama host

# --- Script ---
def translate_text_from_file():
    """Reads a file, translates its Hindi content to English using Ollama, and saves the result."""
    try:
        # 1. Read the transcribed Hindi text
        with open(INPUT_FILENAME, "r", encoding="utf-8") as f:
            transcribed_text = f.read()

        if not transcribed_text.strip():
            print(f"Error: **{INPUT_FILENAME}** is empty. Nothing to translate.")
            return
            
        print(f"Read {len(transcribed_text)} characters of Hindi text from **{INPUT_FILENAME}**.")
        print(f"Connecting to Ollama server at {OLLAMA_HOST}...")

        # 2. Setup Ollama Client and Prompt
        client = Client(host=OLLAMA_HOST)
        
        # Craft a clear translation prompt for the LLM
        prompt = (
            "The following text is in Hindi. Translate it into clear, natural, and modern English. "
            "Only return the final translated English text. Do not include any introductory or concluding phrases.\n\n"
            f"HINDI TEXT:\n---\n{transcribed_text}"
        )

        # 3. Generate Translation
        response = client.generate(
            model=OLLAMA_MODEL, 
            prompt=prompt,
            stream=False 
        )
        
        translated_text = response['response'].strip()

        # 4. Save the translated text
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write(translated_text)

        print("--- Translation Complete ---")
        print(f"English Translation saved to: **{OUTPUT_FILENAME}**")
        print("-" * 30)
        print(f"Preview: {translated_text[:200]}" + ("..." if len(translated_text) > 200 else ""))

    except FileNotFoundError:
        print(f"Error: Input file **{INPUT_FILENAME}** not found. Did you run `transcribe_audio.py` first?")
    except Exception as e:
        print(f"An error occurred during translation (Is Ollama running and is the model '{OLLAMA_MODEL}' pulled?): {e}")

if __name__ == "__main__":
    translate_text_from_file()