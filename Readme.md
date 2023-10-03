# About

This is an interactive story generator. It uses AI (OpenAI GPT) to create endless stories that the player can influence the direction of by choosing what happens next.
![Example](images/example.gif)
- This is the back-end (Python/Flask) for the interactive story generator, in order to run the app locally you will need to setup the front-end (HTML, Javascript, css) as well: https://github.com/DavidjMarkham/InteractiveStoryGeneratorFrontend
- This python-based web api was created with Flask
- App runs on port 5000 by default

## Installation
- Get an OpenAI API key (they have a free trial)
    - Goto [OpenAI's official platform website](https://platform.openai.com/).
    - Create an account and sign into it
    - Once you've created an account or have logged into an existing account, you'll see your name and your profile icon at the top-right corner of OpenAI's platform homepage.
    - To get an API Key, click on your name in the top-right corner to bring up a dropdown menu. Then, click the "View API keys" option.
    - Click "Create new secret key"
- Fill in your Open API key in the .env file
- `source venv/Scripts/activate`
- `pip install -r requirements.txt`
- `python app.py`