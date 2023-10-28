from flask import Flask, request, jsonify
from flask_cors import CORS  # import CORS
import openai
import json
import os
from texttospeech import TextToSpeech
from flask import send_from_directory
from dotenv import load_dotenv
load_dotenv() 
from StoryResponse import StoryResponse

app = Flask(__name__)
CORS(app)  # enable CORS

AUDIO_FILES_DIR = "audio_files"
GENERATE_OUTLINE_PROMPT = "Outline the world that short story will take place in. The short story will have a sole protagonist who is the player. Choose the settings, and key features of the world, any key characters, adversaries, goals, and issues to overcome. The world should be setup such that many different dramatic situations can occur throughout the story. Output max of 300 characters."
START_STORY_PROMPT = "[PROMPT]Write a novel. I am the sole protagonist of this story.You are the narrator. Describe this story in the second person in 200 words. Describe 2-4 options with less than 10 words. The story takes place in the universe described in the following outline. Wait for the user to choose one of the options.Continue the story only after the user has made the choice.  Output in the JSON format in EXAMPLE_OUTPUT.[/PROMPT][OUTLINE]__OUTLINE__[/OUTLINE][EXAMPLE_OUTPUT]{\"story\": \"Story...\",\"options\": [\"Option 1\",\"Option 2\"]}[/EXAMPLE_OUTPUT]"
CONTINUE_STORY_PROMPT = "Prompt: \"\"\" Let's continue a novel we started earlier. I am the sole protagonist of this story. You are the narrator. You will be provided what happened so far in the story in the \"Story so far\" section. Continue the story from there. Write the continued story in the second person. Output the continuation of the story (100 words) and the options the player can choose to take next (10 words each). The story takes place in the universe described in the following outline. Describe 2-4 options.Wait for the user to choose one of the options. Continue the story only after the user has made the choice. The continued story should make the players choice meaningful and impactful to the story, emphasizing an emotional, drama filled story. The story must not end. Output in the JSON format in EXAMPLE_OUTPUT. Story so far: \"\"\" __STORY_SO_FAR__ \"\"\" Outline: \"\"\"__OUTLINE__\"\"\" \"\"\"[EXAMPLE_OUTPUT]{\"story\": \"Story...\",\"options\": [\"Option 1\",\"Option 2\"]}[/EXAMPLE_OUTPUT]"
CHAPTER_IMAGE_PROMPT = "We want to generate an image to represent this chapter. Describe how that image in 30 words or less using as much detail as possible including capturing the setting, emotion, and atmosphere of the scene. Keep it the image description family friendly. Somewhat abstract, no closeup of faces. Chapter text: \"\"\"[CHAPTER_TEXT]\"\"\""
SUMMARIZE_STORY_SO_FAR_PROMPT = "Summarize the following story in 200 words or less. The story so far: \"\"\"__STORY_SO_FAR__\"\"\""
MODEL = "gpt-3.5-turbo"

@app.route('/api/story', methods=['POST'])
def post_story():
    data = request.get_json()
    outline = data.get('outline')
    story_so_far = data.get('storySoFar')
    story = data.get('story')
    option_text = data.get('optionText')
    first_story = (option_text==None or option_text=="")    

    if(first_story):
        # Create World Outline
        prompt = GENERATE_OUTLINE_PROMPT

        messages= [
            {"role": "user", "content": prompt}
        ]
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=messages
        )

        outline = response["choices"][0]["message"]["content"]        

    if(not first_story):
        # Summarize the story so far
        story_so_far = story_so_far + "\n" + story
        prompt = SUMMARIZE_STORY_SO_FAR_PROMPT.replace("__STORY_SO_FAR__",story_so_far)

        messages= [
            {"role": "user", "content": prompt}
        ]
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=messages
        )

        story_so_far = response["choices"][0]["message"]["content"]
        story_so_far = story_so_far + "\n Player's last choice: " + option_text

    prompt = START_STORY_PROMPT.replace("__OUTLINE__",outline)
    if(not first_story):
        prompt = CONTINUE_STORY_PROMPT.replace("__STORY_SO_FAR__",story_so_far).replace("__OUTLINE__",outline)
    
    messages= [
        {"role": "user", "content": prompt}
    ]
    functions= [  
        {
            "name": "handle_story_response",
            "description": "Handles all responses",
            "parameters": StoryResponse.model_json_schema()
        }
    ]  

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=messages,
        functions=functions,
        function_call={"name": "handle_story_response"}
    )        
    response_message = response["choices"][0]["message"]

    # Check if the model wants to call a function
    story = ""
    options = []
    if response_message.get("function_call"):
        # Call the function. The JSON response may not always be valid so make sure to handle errors
        function_name = response_message["function_call"]["name"]

        available_functions = {
                "handle_story_response": handle_story_response,
        }
        function_to_call = available_functions[function_name] 
        function_args = json.loads(response_message["function_call"]["arguments"])
        function_response = function_to_call(**function_args)
        story = function_response.story
        options = function_response.options    

    response = {
        'status': 'success',
        'outline': outline,
        'story': story,
        'options': options,
        'storySoFar': story_so_far
    }
    return jsonify(response), 201

@app.route('/api/read_text', methods=['POST'])
def read_text():
    chapter_text = request.get_json().get('story')
    text_to_speech = TextToSpeech()
    
    audio_file = text_to_speech.generateAudio(chapter_text)
    audio_url = f"{os.environ['BASE_URL']}/audio/{audio_file}"

    response = {
        'status': 'success',
        'audioFilename': audio_url,
    }
    return jsonify(response), 201

@app.route('/api/chapter_image', methods=['POST'])
def post_chapter_image():
    data = request.get_json()
    chapter_text = data.get('story')

    # Create chapter image
    prompt = CHAPTER_IMAGE_PROMPT.replace("[CHAPTER_TEXT]", chapter_text)

    messages= [
        {"role": "user", "content": prompt}
    ]
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=messages
    )

    image_prompt = response["choices"][0]["message"]["content"] + ". Digital art"
    app.logger.info(image_prompt)
    response = openai.Image.create(
        prompt=image_prompt,
        n=1,
        size="1024x1024",
    )
    
    image_url = response["data"][0]["url"]

    response = {
        'status': 'success',
        'image_url': image_url
    }
    return jsonify(response), 201


@app.route('/api/audio/<filename>', methods=['GET'])
def serve_audio_file(filename):
    try:
        # Ensure filename is secure before serving
        safe_filename = os.path.normpath(os.path.join(AUDIO_FILES_DIR, filename))
        
        return send_from_directory(AUDIO_FILES_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

def handle_story_response(story,options):
    story_response = StoryResponse(story=story,options=options)
    return story_response

if __name__ == '__main__':
    app.run(debug=True)