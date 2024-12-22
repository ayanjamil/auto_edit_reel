import whisper


def transcribe_with_timestamps_clean(video_path, output_file):
    """
    Transcribe a video and save timestamps and text to a .txt file without extra labels.

    Args:
        video_path (str): Path to the input video file.
        output_file (str): Path to the output .txt file.
    """
    # Load the Whisper model
    model = whisper.load_model("base")

    # Transcribe the video
    result = model.transcribe(video_path, verbose=True)

    # Extract segments and save to file
    with open(output_file, "w") as f:
        for segment in result["segments"]:
            start = f"{segment['start']:.2f}"  # Start time in seconds
            end = f"{segment['end']:.2f}"  # End time in seconds
            text = segment["text"]

            # Write to the .txt file in the desired format
            f.write(f"{start} {end} {text}\n")

    print(f"Cleaned transcript with timestamps saved to {output_file}")



video_path = "/home/ayan/fn/script/vid_automation/input/raw_video/iu.mp4"  # Replace with the path to your video file
output_file = "/home/ayan/fn/script/vid_automation/input/script/timestamps.txt"  # Replace with the desired output .txt file path
transcribe_with_timestamps_clean(video_path, output_file)
