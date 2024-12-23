from openai import OpenAI

class ChatGPTHandler:
    def __init__(self, api_key):
        """
        Initialize the ChatGPT handler with the OpenAI API key.

        Args:
            api_key (str): OpenAI API key.
        """
        self.client = OpenAI(api_key=api_key)

    def generate_keywords(self, script, max_keywords=15):
        """
        Generate keywords using GPT based on the provided script.

        Args:
            script (str): The script of the video.
            max_keywords (int): Maximum number of keywords to extract.

        Returns:
            list: A list of keywords.
        """
        try:
            prompt = (
                f"The following is the script of a video: {script}. "
                f"Select the top {max_keywords} most relevant keywords from the script provided for finding stock images or videos. "
                "Provide them in a comma-separated list."
            )

            # Call the ChatGPT API
            response = self.client.chat.completions.create(
                model="gpt-4",  # Updated model name
                messages=[
                    {"role": "system", "content": "You are an assistant for refining keyword selection for finding out stock images for short form content."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=100,
                temperature=0.7
            )
            refined_keywords = response.choices[0].message.content
            return [word.strip() for word in refined_keywords.split(",")]
        except Exception as e:
            print(f"Error refining keywords: {e}")
            return []

    def map_transcription_to_images_with_script(self, transcription_segments, script, images):
        """
        Maps transcription segments to stock images using GPT.

        Args:
            transcription_segments (list): List of transcription segments with start, end, and text.
            script (str): The entire script of the video.
            images (list): List of available image data.

        Returns:
            list: List of dictionaries with transcription segments and mapped image URLs.
        """
        mapped_results = []
        for segment in transcription_segments:
            segment_text = segment["text"]
            image_data = self.select_relevant_image(segment_text, script, images)
            if image_data:
                images.remove(image_data)  # Avoid reusing the same image
            mapped_results.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment_text,
                "image_url": image_data["url"] if image_data else None,
                "alt": image_data.get("alt", None) if image_data else None
            })
        return mapped_results

    def select_relevant_image(self, segment_text, script, images):
        """
        Select the most relevant image for a transcription segment using GPT.

        Args:
            segment_text (str): The text of the transcription segment.
            script (str): The entire script of the video.
            images (list): List of available image data.

        Returns:
            dict: The selected image data or None if no suitable image is found.
        """
        if not images:
            return None

        try:
            image_descriptions = "\n".join(
                [f"Image {i+1}: {img.get('alt', 'No description')}" for i, img in enumerate(images)]
            )
            prompt = (
                f"The following is the script of the video:\n\n{script}\n\n"
                f"Here is the transcription segment: \"{segment_text}\".\n"
                f"Select the most contextually relevant image for this segment "
                f"from the following options:\n\n{image_descriptions}\n\n"
                "Reply with the number of the most relevant image."
            )

            # Call the ChatGPT API
            response = self.client.chat.completions.create(
                model="gpt-4",  # Updated model name
                messages=[
                    {"role": "system", "content": "You are an assistant for selecting the most contextually relevant image."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=50,
                temperature=0.5
            )
            response_text = response.choices[0].message.content.strip()

            # Validate the response and convert to integer
            if response_text.isdigit():
                selected_image_index = int(response_text) - 1
                if 0 <= selected_image_index < len(images):
                    return images[selected_image_index]
                else:
                    print(f"No relevant image selected for segment: \"{segment_text}\".")
                    return None
            else:
                print(f"Invalid GPT response for segment: \"{segment_text}\": {response_text}")
                return None

        except Exception as e:
            print(f"Error selecting image via GPT: {e}")
            return None