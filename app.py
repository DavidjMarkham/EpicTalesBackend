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

START_STORY_PROMPT = "[PROMPT]Let's play a game. I am the sole protagonist of this story.You are the narrator.This story is made up of different genres, fantasy, horror and science fiction, cleverly mixed together.Describe this story in the second person in 50 words.Describe two options 1 and 2 with less than 20 words.Wait for the user to choose one of the two options.Continue the story only after the user has made the choice.Continue the story description in 50 words.Go on with the choice system.The story must not end.Output should follow similar format to example, ONLY output JSON matching the example, no additional output.[/PROMPT][EXAMPLE]{\"story\": \"You find yourself lost in a dark forest. Strange whispers fill the air, and your heart races with fear. Suddenly, a creature appears before you: half-man, half-machine, it offers you a choice.\",\"options\": [\"Follow the creature to a secret lab where you discover an incredible technology, but soon realize the horrors it hides.\",\"Run away from the creature and find a magical portal that leads to a kingdom in ruins, where you must face a powerful sorceress.\"]}[/EXAMPLE][OUTPUT]{\"story\": \"You wake up in a surreal world. A strange voice whispers in your ear, urging you to explore. As you wander, you encounter a creepy mansion: it was abandoned for years, but today the door is open. You have a choice.\",\"options\": [\"Enter the mansion and uncover its secrets, but be aware of the ancient curse that lurks within.\",\"Ignore the mansion and continue walking until you reach a glowing portal that transports you to an unknown planet full of danger.\"]}[/OUTPUT]"
CONTINUE_STORY_PROMPT = "Prompt: \"\"\" Let's continue a game we started earlier. I am the sole protagonist of this story. You are the narrator. You will be provided what happened so far in the story. Continue what would happen in the story. Write the continued story in the second person in 40-60 words. Describe two options 1 and 2 with less than 20 words.Wait for the user to choose one of the two options. Continue the story only after the user has made the choice. Continue the story with 40-60 words. Go on with the choice system. The story must not end.Output should follow similar format to example, ONLY fill in and output the JSON in OUTPUT, no additional output. \"\"\" Example: \"\"\" {\"story\":\"You hesitantly follow the creature through the twisted undergrowth, eventually arriving at a hidden laboratory concealed within the forest. As you explore the facility, you uncover advanced technology beyond your wildest imagination. However, your fascination turns to dread when you stumble upon the dark truth: the machines are powered by human souls, trapped and tormented in an endless cycle of pain. You realize the terrible price of progress and must decide whether to destroy the lab or seek a way to free the imprisoned souls.\",\"options\": [\"Sabotage the lab's power source, risking your life to destroy the machines and end the suffering.\",\"Search for a method to release the trapped souls, hoping to save them and expose the lab's dark secrets.\"]} \"\"\"Story so far: \"\"\" __PREVIOUS_STORY__ \"\"\"Output:"

START_STORY_PROMPT = "Write a story, you should also provide 2-4 very concise options for the player to choose for the story to go next."

@app.route('/api/story', methods=['POST'])
def post_story():
    data = request.get_json()
    story = data.get('story')
    option_text = data.get('optionText')

    app.logger.info("In API")

    prompt = START_STORY_PROMPT
    if(option_text==None or option_text!=""):
        prompt = CONTINUE_STORY_PROMPT.replace("__PREVIOUS_STORY__",story + "\n\n Player chose: " + option_text)
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
        model="gpt-3.5-turbo",
        messages=messages,
        functions=functions,
        function_call={"name": "handle_story_response"}
    )    
    
    response_message = response["choices"][0]["message"]

    # Check if the model wants to call a function
    app.logger.info(response_message)
    if response_message.get("function_call"):
        # Call the function. The JSON response may not always be valid so make sure to handle errors
        function_name = response_message["function_call"]["name"]

        available_functions = {
                "handle_story_response": handle_story_response,
        }
        function_to_call = available_functions[function_name] 
        app.logger.info("calling function")
        function_args = json.loads(response_message["function_call"]["arguments"])
        function_response = function_to_call(**function_args)

    response = {
        'status': 'success',
        'story': function_response.story,
        'options': function_response.options
    }
    return jsonify(response), 201

def handle_story_response(story,options):
    app.logger.info(story)
    app.logger.info("Options")
    app.logger.info(options)

    story_response = StoryResponse(story=story,options=options)
    return story_response

if __name__ == '__main__':
    app.run(debug=True)