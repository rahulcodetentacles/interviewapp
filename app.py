from flask import Flask, request, url_for ,render_template , redirect
from twilio.twiml.voice_response import Gather, VoiceResponse
from twilio.rest import Client
from openai import OpenAI
import time

app = Flask(__name__)

class InterviewApp:
    def __init__(self):
        self.account_sid = "AC3c5ee5a0e9bed2bd729dfd69fa3a8420" #SID generated by the twilio
        self.auth_token = "db32e86048fc656f1f1508fe7ab90aa0"  #AUTH token generated by twilio
        self.openai_api_key = "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" # OPEN_AI API key 
        self.openai_client = OpenAI(api_key=self.openai_api_key) #OPEN_AI Client
        self.assistant_id = "asst_7jRqbGVgJasJTE7NRYJXoXDQ" #OPEN_AI Assistant ID
        """
          Note: You can directly paste your keys and tokens in the string format but 
                make sure to remove os.getenv
        """
        self.client = Client(self.account_sid, self.auth_token)
        self.messages = []

    def make_call(self, number):
        """
        Initiates a phone call using the Twilio Client API.

        Args:
            number (str): The phone number to call.

        Returns:
            None
        """
        record_url = url_for("record", _external=True)
        call = self.client.calls.create(
            to="+919561214824",
            from_="+19089230665",
            url=record_url
        )
        print(call.sid)

interview_app = InterviewApp()

# Function to check whether the Run is completed or not
def poll_run(run, thread):
    while run.status != "completed":
        run = interview_app.openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

@app.route('/')
def index():
    """
    Default route that returns a greeting message.

    Returns:
        str: A greeting message.
    """
    return render_template('index.html')

@app.route("/call", methods=['GET', 'POST'])
def call():
    """
    Endpoint to initiate a phone call.

    Returns:
        str: A response message indicating the call has been initiated.
    """
    global number
    global position
    global experience
    if request.method == 'POST':
        try:
            number = request.form.get("number")
            position = request.form.get("position")
            experience = request.form.get("experience")
            interview_app.make_call(number)
            return redirect(url_for('call', message='Call initiated successfully!'))
        except Exception as e:
            return redirect(url_for('call', message='Unable to initialize the call'))
    
    message = request.args.get('message')
    return render_template('call.html', message=message)

@app.route("/record", methods=['GET', 'POST'])
def record():
    """
    Endpoint for recording a voice message.

    Returns:
        str: The TwiML response to prompt the user to leave a message.
    """
    response = VoiceResponse()
    response.say('Please answer')
    response.gather(action='/handle-recording', input='speech')
    return str(response)

@app.route("/handle-recording", methods=['GET', 'POST'])
def handle_recording():
    """
    Endpoint to handle the recorded voice message.

    Returns:
        str: The TwiML response based on the transcription and AI-generated response.
    """
    speech_result = request.args.get('SpeechResult')
    print("SpeechResult: ", speech_result)
    if not speech_result:
        response = VoiceResponse()
        response.redirect(url_for("record"), method='POST')
        return str(response)

    instruction = f"You are Jarvis, an AI assistant acting as an HR representative " \
        f"for conducting phone interviews. Today, you are interviewing " \
        f"candidates for the position of a {position} with {experience} years of experience. " \
        f"Your task is to ask relevant questions about their experience, " \
        f"technical skills, and problem-solving abilities in a conversational " \
        f"manner. After the interview, provide a summary of the candidate's " \
        f"qualifications, give a rating on a scale of 1 to 5 based on their " \
        f"responses, and if they seem suitable, inquire about their availability " \
        f"for a second interview. Remember to maintain a professional and unbiased " \
        f"tone throughout the call. You should not answer anything irrelevant to the interview."
    assistant = interview_app.openai_client.beta.assistants.update(
        interview_app.assistant_id,
        instructions=instruction
    )
    thread = interview_app.openai_client.beta.threads.create()
    message = interview_app.openai_client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=speech_result
    )
    run = interview_app.openai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=interview_app.assistant_id
    )
    run = poll_run(run, thread)
    messages = interview_app.openai_client.beta.threads.messages.list(thread_id=thread.id)
    result_text = ""
    for m in messages:
        if m.role == "assistant":
            result_text = m.content[0].text.value
            print(result_text)

    interview_app.messages.append({
        "role": "assistant",
        "content": result_text
    })

    response = VoiceResponse()
    gather = Gather(action='/record', method='GET')
    gather.say(result_text)
    response.append(gather)
    response.redirect(url_for("record"), method='POST')
    return str(response)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
