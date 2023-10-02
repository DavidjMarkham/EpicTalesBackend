from flask import Flask, request, jsonify
from flask_cors import CORS  # import CORS
import openai
import json
import os
from dotenv import load_dotenv
load_dotenv() 
from StoryResponse import StoryResponse

app = Flask(__name__)
CORS(app)  # enable CORS

GENERATE_OUTLINE_PROMPT = "Outline the world that short story will take place in. The short story will have a sole protagonist who is the player. Choose the settings, and key features of the world, any key characters, adversaries, goals, and issues to overcome. The world should be setup such that many different dramatic situations can occur throughout the story. Output max of 300 characters."
START_STORY_PROMPT = "[PROMPT]Let's play a game. I am the sole protagonist of this story.You are the narrator. Describe this story in the second person in 50 words. Describe 2-4 options with less than 10 words. The story takes place in the universe described in the following outline. Wait for the user to choose one of the options.Continue the story only after the user has made the choice.[/PROMPT][OUTLINE]__OUTLINE__[/OUTLINE]"
CONTINUE_STORY_PROMPT = "Prompt: \"\"\" Let's continue a game we started earlier. I am the sole protagonist of this story. You are the narrator. You will be provided what happened so far in the story in the \"Previous Story\" section. Continue what would happen in the story. Write the continued story in the second person in up to 100 words. The story takes place in the universe described in the following outline. Describe 2-4 options in less than 10 words.Wait for the user to choose one of the options. Continue the story only after the user has made the choice. The story must not end. Outline: \"\"\"__OUTLINE__\"\"\" \"\"\" Previous chapter: \"\"\" __PREVIOUS_STORY__ \"\"\""
CHAPTER_IMAGE_PROMPT = "We want to generate an image to represent this chapter. Describe how that image in 1-2 sentences using as much detail as possible including capturing the setting, emotion, and atmosphere of the scene. Keep it the image description family friendly. Somewhat abstract, no closeup of faces. Chapter text: \"\"\"[CHAPTER_TEXT]\"\"\""
MODEL = "gpt-4"

@app.route('/api/story', methods=['POST'])
def post_story():
    data = request.get_json()
    outline = data.get('outline')
    story = data.get('story')
    option_text = data.get('optionText')    

    if(option_text==None or option_text==""):
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

    prompt = START_STORY_PROMPT.replace("__OUTLINE__",outline)
    if(option_text==None or option_text!=""):
        prompt = CONTINUE_STORY_PROMPT.replace("__PREVIOUS_STORY__",story + "\n\n Player chose: " + option_text).replace("__OUTLINE__",outline)

    app.logger.info(prompt)
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

    # Create chapter image
    """
    prompt = CHAPTER_IMAGE_PROMPT.replace("[CHAPTER_TEXT]", story)

    messages= [
        {"role": "user", "content": prompt}
    ]
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=messages
    )

    image_prompt = response["choices"][0]["message"]["content"]
    response = openai.Image.create(
        prompt=image_prompt,
        n=1,
        size="256x256",
    )
    
    image_url = response["data"][0]["url"]
    """
    image_url=""
    response = {
        'status': 'success',
        'outline': outline,
        'story': story,
        'options': options,
        'image_url': image_url
    }
    return jsonify(response), 201

def handle_story_response(story,options):
    story_response = StoryResponse(story=story,options=options)
    return story_response

if __name__ == '__main__':
    app.run(debug=True)