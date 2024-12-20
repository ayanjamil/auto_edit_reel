def make_script(openai_client, output_path):
    scripts = []
    prompt = (
        "Give me one script of 1 minute with no emoji, only text, "
        "on recent tech updates. Add some hooks at the opening and closing. "
        "I want to make a reel from it, so give me only the text."
    )

    try:
        # Call OpenAI's API
        response = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="gpt-4o-mini",  # Use the correct model

        )
        # Extract the content of the response
        # script = response['choices'][0]['message']['content']

        script = response.choices[0].message.content
        clean_script = re.sub(r"\[.*?\]", "", script).strip()
        clean_script += " That's it for today, see you later and keep finding your niche."
        scripts.append({"script": script,"Cleaned Script ":clean_script})
    except Exception as e:
        print(f"Error generating script: {e}")
        scripts.append({"script": "Error in generating script"})

    # Save the scripts to a CSV file
    try:
        summary_df = pd.DataFrame(scripts)
        summary_df.to_csv(output_path, index=False)
        print(f"Scripts saved to {output_path}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")
