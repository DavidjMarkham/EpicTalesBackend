import os
import hashlib
import azure.cognitiveservices.speech as speechsdk

class TextToSpeech:
    def __init__(self):
        pass

    def generateAudio(self,inputText):        
        # This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
        speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

        # The language of the voice that speaks.
        speech_config.speech_synthesis_voice_name='en-US-RyanMultilingualNeural'

        # Compute hash of the inputText for the filename
        hashed_text = hashlib.sha256(inputText.encode('utf-8')).hexdigest()
        file_name = f"{hashed_text}.mp3"
        full_file_name = f"audio_files/{file_name}"

        file_config = speechsdk.audio.AudioOutputConfig(filename=full_file_name)  
        
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=file_config)  

        speech_synthesis_result = speech_synthesizer.speak_text_async(inputText).get()

        if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("Speech synthesized for text [{}]".format(inputText))
        elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = speech_synthesis_result.cancellation_details
            print("Speech synthesis canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                if cancellation_details.error_details:
                    print("Error details: {}".format(cancellation_details.error_details))
                    print("Did you set the speech resource key and region values?")

        return file_name