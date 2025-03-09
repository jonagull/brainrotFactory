import json
from gtts import gTTS
import os
from datetime import datetime
import glob
import time
from pathlib import Path
try:
    import edge_tts
except ImportError:
    print("Error: edge-tts package not found. Installing...")
    os.system('pip install edge-tts')
    import edge_tts

def text_to_speech(text, filename):
    """Convert text to speech and save as MP3"""
    try:
        tts = gTTS(text=text, lang='en')
        tts.save(filename)
        print(f"Created audio file: {filename}")
    except Exception as e:
        print(f"Error creating audio for {filename}: {e}")

def select_json_file():
    """Show available JSON files and let user select one"""
    json_files = glob.glob("creepypasta_stories_*.json")
    
    if not json_files:
        print("No story files found!")
        return None
    
    print("\nAvailable story files:")
    for i, file in enumerate(json_files, 1):
        print(f"{i}. {file}")
    
    while True:
        try:
            choice = int(input("\nSelect a file number (or 0 to exit): "))
            if choice == 0:
                return None
            if 1 <= choice <= len(json_files):
                return json_files[choice - 1]
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

def select_stories(stories):
    """Let user select which stories to convert to audio"""
    print("\nAvailable stories:")
    for i, story in enumerate(stories, 1):
        print(f"{i}. {story['title']} (by {story['author']}, {len(story['content'])} chars)")
    
    while True:
        try:
            selection = input("\nEnter story numbers to convert (e.g., '1,3,4' or 'all'): ").lower()
            if selection == 'all':
                return list(range(len(stories)))
            
            # Parse comma-separated numbers
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            if all(0 <= i < len(stories) for i in indices):
                return indices
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter valid numbers separated by commas or 'all'")

def process_stories_to_audio(json_file):
    """Read stories from JSON and convert them to audio files"""
    # Read JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        stories = json.load(f)
    
    # Let user select stories
    selected_indices = select_stories(stories)
    if not selected_indices:
        return
    
    # Create audio directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_dir = f"audio_{timestamp}"
    os.makedirs(audio_dir, exist_ok=True)
    
    # Process selected stories
    for i in selected_indices:
        story = stories[i]
        if story['content']:
            print(f"\nProcessing: {story['title']}")
            audio_text = f"{story['title']}. By {story['author']}. {story['content']}"
            audio_filename = f"{audio_dir}/story_{i+1}_{story['title'][:30]}.mp3"
            # Replace invalid filename characters
            audio_filename = "".join(c for c in audio_filename if c.isalnum() or c in (' ', '-', '_', '.', '/'))
            text_to_speech(audio_text, audio_filename)

async def generate_speech(text, output_path):
    """Generate speech from text using Edge TTS"""
    try:
        voice = "en-US-ChristopherNeural"
        tts = edge_tts.Communicate(text=text, voice=voice)
        await tts.save(output_path)
    except Exception as e:
        print(f"Error generating speech: {str(e)}")
        raise

def create_audio_from_text(text, output_path):
    """Create audio file from text using Edge TTS"""
    print(f"Generating audio to: {output_path}")
    
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Run the async function
        import asyncio
        asyncio.run(generate_speech(text, output_path))
        
        # Verify the file was created
        if os.path.exists(output_path):
            print("Audio generation completed!")
            return output_path
        else:
            raise Exception("Audio file was not created")
            
    except Exception as e:
        print(f"Error in create_audio_from_text: {str(e)}")
        raise

if __name__ == "__main__":
    print("Text-to-Speech Story Converter")
    print("-" * 30)
    
    json_file = select_json_file()
    if json_file:
        process_stories_to_audio(json_file)
    else:
        print("No file selected. Exiting.") 