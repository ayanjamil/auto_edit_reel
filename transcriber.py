import whisper


def transcribe_with_timestamps_clean(video_path):
    """
    Transcribe a video and return timestamps and text.

    Args:
        video_path (str): Path to the input video file.

    Returns:
        list: A list of dictionaries containing 'start', 'end', and 'text'.
    """
    # Load the Whisper model
    model = whisper.load_model("base")

    # Transcribe the video
    result = model.transcribe(video_path, verbose=True)

    # Collect segments
    segments = []
    for segment in result["segments"]:
        start = f"{segment['start']:.2f}"  # Start time in seconds
        end = f"{segment['end']:.2f}"  # End time in seconds
        text = segment["text"]

        # Append to the list
        segments.append({"start": start, "end": end, "text": text})

    return segments


def save_transcription_to_file(segments, output_file):
    """
    Save the transcription segments to a file.

    Args:
        segments (list): A list of transcription segments.
        output_file (str): Path to the output .txt file.
    """
    with open(output_file, "w") as f:
        for segment in segments:
            f.write(f"{segment['start']} {segment['end']} {segment['text']}\n")

    print(f"Cleaned transcript with timestamps saved to {output_file}")


# Example usage
video_path = "/home/ayan/fn/script/vid_automation/input/raw_video/iu.mp4"  # Replace with the path to your video file
output_file = "/home/ayan/fn/script/vid_automation/input/script/timestamps.txt"  # Replace with the desired output .txt file path

# Get the transcription segments
transcription_segments = transcribe_with_timestamps_clean(video_path)

# Save them to a file
save_transcription_to_file(transcription_segments, output_file)
