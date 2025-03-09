import os
from datetime import datetime
import json
import re
from scripts.create_audio import create_audio_from_text
from scripts.create_subtitles import create_subtitles_from_audio
from scripts.create_video import create_final_video

def get_available_stories():
    """Temporarily read stories from json file"""
    json_files = [f for f in os.listdir('.') if f.startswith('creepypasta_stories_') and f.endswith('.json')]
    if not json_files:
        return []
    
    # Use the most recent json file
    latest_file = sorted(json_files)[-1]
    print(f"Loading stories from: {latest_file}")
    with open(latest_file, 'r') as f:
        stories = json.load(f)
    return stories

def clean_filename(filename):
    """Clean string to make it safe for filenames"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    return filename

def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = ['stories', 'audio', 'subtitles', 'videos', 'final_videos']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created/verified directory: {directory}")

def select_from_list(items, prompt):
    """Generic function to select an item from a list"""
    if not items:
        print("No items available.")
        return None
    
    print(f"\n{prompt}:")
    for i, item in enumerate(items, 1):
        print(f"{i}. {item['title']}")
    
    while True:
        try:
            choice = int(input("\nSelect a number: "))
            if 1 <= choice <= len(items):
                return items[choice - 1]
            print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

def main():
    print("BrainRot Factory")
    print("=" * 50)
    
    # Setup directories
    setup_directories()
    
    # 1. Get available stories
    stories = get_available_stories()
    selected_story = select_from_list(stories, "Available stories")
    if not selected_story:
        return
    
    # Debug: Print story structure
    print("\nStory structure:")
    for key in selected_story.keys():
        print(f"- {key}")
    
    # Get story content (try different possible keys)
    story_content = selected_story.get('content') or selected_story.get('selftext') or selected_story.get('text')
    if not story_content:
        print("\nError: Could not find story content. Available keys:", list(selected_story.keys()))
        return
    
    # Clean the story title for use in filenames
    safe_title = clean_filename(selected_story['title'])
    
    # 2. Create audio if it doesn't exist
    audio_dir = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(audio_dir, exist_ok=True)
    audio_path = f"{audio_dir}/story_{safe_title}.mp3"
    
    if not os.path.exists(audio_path):
        print("\nGenerating audio...")
        create_audio_from_text(story_content, audio_path)
    else:
        print("\nAudio file already exists.")
    
    # 3. Create subtitles
    subtitle_dir = f"subtitles/subtitles_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(subtitle_dir, exist_ok=True)
    subtitle_path = f"{subtitle_dir}/{safe_title}_subs.srt"
    
    if not os.path.exists(subtitle_path):
        print("\nGenerating subtitles...")
        create_subtitles_from_audio(audio_path, subtitle_path)
    else:
        print("\nSubtitles already exist.")
    
    # 4. Select background video
    video_files = [f for f in os.listdir('videos') if f.endswith('.mp4')]
    selected_video = select_from_list([{'title': f} for f in video_files], "Available background videos")
    if not selected_video:
        return
    
    video_path = os.path.join('videos', selected_video['title'])
    
    # 5. Create final video
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"final_videos/final_{safe_title}_{timestamp}.mp4"
    
    print("\nCreating final video...")
    create_final_video(
        video_path=video_path,
        audio_path=audio_path,
        srt_path=subtitle_path,
        output_path=output_path
    )
    
    print("\nProcess completed!")
    print(f"Final video saved to: {output_path}")

if __name__ == "__main__":
    main() 