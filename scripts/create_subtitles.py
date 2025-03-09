import json
import os
import glob
from datetime import datetime
import whisper

# Directories
VIDEO_DIR = "videos"
SUBTITLE_DIR = "subtitles"

def setup_directories():
    """Create necessary directories if they don't exist"""
    for directory in [VIDEO_DIR, SUBTITLE_DIR]:
        os.makedirs(directory, exist_ok=True)
        print(f"Created/verified directory: {directory}")

def select_video_file():
    """Show available video files and let user select one"""
    video_files = glob.glob(f"{VIDEO_DIR}/*.mp4")
    
    if not video_files:
        print(f"\nNo video files found in {VIDEO_DIR}!")
        print(f"Please add your videos to the '{VIDEO_DIR}' directory.")
        return None
    
    print("\nAvailable video files:")
    for i, file in enumerate(video_files, 1):
        print(f"{i}. {os.path.basename(file)}")
    
    while True:
        try:
            choice = int(input("\nSelect a video file number: "))
            if 1 <= choice <= len(video_files):
                return video_files[choice - 1]
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

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
            choice = int(input("\nSelect a file number: "))
            if 1 <= choice <= len(json_files):
                return json_files[choice - 1]
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

def format_timestamp(seconds):
    """Convert seconds to SRT timestamp format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def create_subtitles_from_audio(audio_path, output_path):
    """Create SRT subtitles from audio file using Whisper"""
    print(f"Transcribing audio from: {audio_path}")
    print(f"Saving subtitles to: {output_path}")
    
    try:
        # Load Whisper model
        print("Loading Whisper model...")
        model = whisper.load_model("base")
        
        # Transcribe audio
        print("Transcribing audio...")
        result = model.transcribe(
            audio_path,
            word_timestamps=True,
            language="en"
        )
        
        # Create subtitle segments
        print("Creating subtitle file...")
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result["segments"], 1):
                # Write subtitle number
                f.write(f"{i}\n")
                
                # Write timestamps
                start_time = format_timestamp(segment["start"])
                end_time = format_timestamp(segment["end"])
                f.write(f"{start_time} --> {end_time}\n")
                
                # Write text
                f.write(f"{segment['text'].strip()}\n\n")
        
        print("Subtitle generation completed!")
        return output_path
        
    except Exception as e:
        print(f"Error creating subtitles: {str(e)}")
        raise

def save_srt(subtitles, output_path):
    """Save subtitles in SRT format"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for sub in subtitles:
            f.write(f"{sub['index']}\n")
            f.write(f"{sub['start']} --> {sub['end']}\n")
            f.write(f"{sub['text']}\n\n")

def main():
    print("Subtitle Generator for Stories")
    print("-" * 30)
    
    # Setup directories
    setup_directories()
    
    # Select video file
    video_path = select_video_file()
    if not video_path:
        return
    
    # Select JSON file with stories
    json_path = select_json_file()
    if not json_path:
        return
    
    # Load stories from JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        stories = json.load(f)
    
    # Show available stories
    print("\nAvailable stories:")
    for i, story in enumerate(stories, 1):
        print(f"{i}. {story['title']}")
    
    # Select story
    while True:
        try:
            choice = int(input("\nSelect a story number: "))
            if 1 <= choice <= len(stories):
                story = stories[choice - 1]
                break
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")
    
    # Create subtitles from story text
    full_text = f"{story['title']}. By {story['author']}. {story['content']}"
    subtitles = create_srt_from_text(full_text)
    
    # Save subtitles
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(SUBTITLE_DIR, f"subtitles_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, 
        f"{os.path.basename(video_path).replace('.mp4', '')}_subs.srt")
    save_srt(subtitles, output_path)
    print(f"\nSubtitles saved to: {output_path}")

if __name__ == "__main__":
    main() 