from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.tools.subtitles import SubtitlesClip
import os
import glob
from datetime import datetime
import re
import whisper
import torch

# Directories
VIDEO_DIR = "videos"
SUBTITLE_DIR = "subtitles"
OUTPUT_DIR = "final_videos"

def setup_directories():
    """Create necessary directories if they don't exist"""
    for directory in [VIDEO_DIR, OUTPUT_DIR]:
        os.makedirs(directory, exist_ok=True)
        print(f"Created/verified directory: {directory}")

def select_file(file_pattern, prompt):
    """Generic file selector"""
    files = glob.glob(file_pattern)
    
    if not files:
        print(f"\nNo files found matching pattern: {file_pattern}")
        return None
    
    print(f"\n{prompt}:")
    for i, file in enumerate(files, 1):
        print(f"{i}. {os.path.basename(file)}")
    
    while True:
        try:
            choice = int(input("\nSelect a file number: "))
            if 1 <= choice <= len(files):
                return files[choice - 1]
            print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")

def split_into_words(text):
    """Split text into words and clean up"""
    # Remove extra spaces and split
    words = text.strip().split()
    # Clean each word
    return [re.sub(r'[^\w\'-]', '', word) for word in words if re.sub(r'[^\w\'-]', '', word)]

def create_word_timing(start_time, end_time, words):
    """Create snappy word timings"""
    if not words:
        return []
    
    # Make it snappier by reducing gaps between words
    total_duration = end_time - start_time
    word_duration = min(0.4, total_duration / len(words))  # Max 0.4s per word
    gap_duration = min(0.1, word_duration * 0.2)  # Small gap between words
    
    timings = []
    current_time = start_time
    
    for word in words:
        # Adjust duration based on word length
        duration = min(word_duration * (len(word) / 5), word_duration)
        timings.append((current_time, current_time + duration))
        current_time += duration + gap_duration
    
    return timings

def parse_srt(srt_path):
    """Parse SRT file and return list of subtitle entries"""
    subtitles = []
    current_sub = None
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
            
        if line.isdigit():
            if current_sub:
                subtitles.append(current_sub)
            current_sub = {'number': int(line)}
            i += 1
            continue
            
        if '-->' in line:
            start, end = line.split(' --> ')
            current_sub['start'] = convert_timestamp_to_seconds(start)
            current_sub['end'] = convert_timestamp_to_seconds(end)
            i += 1
            continue
            
        if current_sub and 'text' not in current_sub:
            current_sub['text'] = line
        i += 1
    
    if current_sub:
        subtitles.append(current_sub)
    
    return subtitles

def convert_timestamp_to_seconds(timestamp):
    """Convert SRT timestamp to seconds"""
    hours, minutes, seconds = timestamp.replace(',', '.').split(':')
    return float(hours) * 3600 + float(minutes) * 60 + float(seconds)

def transcribe_audio(audio_path):
    """Transcribe audio file using Whisper and get word-level timings"""
    print("\nTranscribing audio for precise word timings...")
    model = whisper.load_model("base")
    result = model.transcribe(
        audio_path,
        word_timestamps=True,
        language="en"
    )
    return result["segments"]

def create_final_video(video_path, audio_path, srt_path, output_path, test_duration=None):
    """Combine video, audio, and subtitles into final video"""
    try:
        print("\nLoading video file...")
        video = VideoFileClip(video_path)
        if test_duration:
            video = video.subclip(0, test_duration)
            print(f"Video duration (test): {test_duration} seconds")
        else:
            print(f"Video duration: {video.duration} seconds")

        print("\nLoading audio file...")
        audio = AudioFileClip(audio_path)
        if test_duration:
            audio = audio.subclip(0, test_duration)
        print(f"Audio duration: {audio.duration} seconds")

        print("\nLoading subtitles...")
        subtitles = parse_srt(srt_path)
        if test_duration:
            subtitles = [sub for sub in subtitles if sub['start'] < test_duration]
        print(f"Loaded {len(subtitles)} subtitle entries")

        # Create word-by-word subtitle clips
        print("\nCreating word-by-word subtitle clips...")
        subtitle_clips = []
        
        for sub in subtitles:
            words = split_into_words(sub['text'])
            timings = create_word_timing(sub['start'], sub['end'], words)
            
            for word, (start, end) in zip(words, timings):
                if test_duration and start >= test_duration:
                    break
                    
                try:
                    clip = TextClip(
                        word,
                        fontsize=40,  # Bigger font for impact
                        color='white',
                        bg_color='rgba(0,0,0,0.6)',  # More opaque background
                        stroke_color='black',
                        stroke_width=2,
                        method='label',
                        size=(video.w, None)
                    )
                    
                    clip = (clip
                        .set_position(('center', 'center'))
                        .set_start(start)
                        .set_end(end))
                    
                    subtitle_clips.append(clip)
                except Exception as e:
                    print(f"Error creating subtitle clip for word '{word}': {e}")
                    continue

        # Create final composite
        print("\nCombining video and subtitles...")
        final = CompositeVideoClip(
            [video] + subtitle_clips,
            size=video.size
        )
        
        # Add audio
        print("Adding audio...")
        final = final.set_audio(audio)

        # Set duration to match audio
        final_duration = min(video.duration, audio.duration)
        if test_duration:
            final_duration = min(final_duration, test_duration)
        final = final.set_duration(final_duration)

        print(f"\nRendering video to: {output_path}")
        print("This may take a while...")
        final.write_videofile(
            output_path, 
            fps=video.fps, 
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='medium'
        )

        # Clean up
        video.close()
        audio.close()
        for clip in subtitle_clips:
            clip.close()
        final.close()
        
        print("\nVideo creation completed!")
        
    except Exception as e:
        print(f"\nError creating video: {str(e)}")
        raise

def main():
    print("Video Combiner (Test Mode)")
    print("-" * 30)
    
    # Setup directories
    setup_directories()
    
    # Select files
    video_path = select_file(f"{VIDEO_DIR}/*.mp4", "Available video files")
    if not video_path:
        return
    
    audio_path = select_file("audio_*/*.mp3", "Available audio files")
    if not audio_path:
        return
    
    srt_path = select_file(f"{SUBTITLE_DIR}/*/*.srt", "Available subtitle files")
    if not srt_path:
        return
    
    # Create output filename with test indicator
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"test_video_{timestamp}.mp4"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Create test video (60 seconds)
    create_final_video(video_path, audio_path, srt_path, output_path, test_duration=60)

if __name__ == "__main__":
    main() 