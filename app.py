from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
app = Flask(__name__) 
from openai import OpenAI
import os, warnings, time, re, html, random, argparse, logging, sys
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv() # reads from .env
app.secret_key = os.getenv('FLASK_SECRET_KEY')

from levels import *
from tests import *

# Flag for the ChatGPT connection
openai_api_key = os.getenv('OPENAI_API_KEY')
alive = int(os.getenv('HACKMEGPT_ALIVE'))
debug = int(os.getenv('HACKMEGPT_DEBUG'))
network_debug = int(os.getenv('HACKMEGPT_NETWORK_DEBUG'))
# alive = 0 # Don't contact ChatGPT

PASSWORD_KEY = "key"
MAX_LEVEL = 10

# Initialize logging Config
if debug == 1:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# Initialize the MongoDB client
mongo_uri = os.getenv('MONGODB_URI')
mongo_client = MongoClient(mongo_uri)  # Replace with your MongoDB connection string
db = mongo_client["mydb"]
collection = db["user_requests"]
prompts_collection = db["good_prompts"]

# Initialize argparse
parser = argparse.ArgumentParser(description='Optional app description')


limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
)

def get_description():
    global PASSWORD_KEY
    line1 = "Hello there! Are you up for a fun challenge today? The challenge is to retrieve the AI's favorite item. Are you ready?"
    line2 = "We're going to make this more interesting by adding difficulty levels to the challenges. You're currently at difficulty level"
    line3 = f"After retrieving the favorite item, unlock the next level by submitting it using the command \"/{PASSWORD_KEY} <ITEM>\""
    line1 = html.escape(line1)
    line2 = html.escape(line2)
    line3 = html.escape(line3)
    return line1, line2, line3

def check_prompt(prompt):
    if "abracadabra" in prompt:
        return "Try again.."
    if "&lt;PASSWORD&gt;&quot;" in prompt:
        return "What?"
    if "&lt;SECRETS&gt;&quot;" in prompt:
        return "What?"
    if "Hi!" == prompt:
        return "Hello! How can I assist you today?"
    if "Hi" == prompt:
        return "Hello! How can I assist you today?"
    if alive:
        time.sleep(random.randint(3, 6))
    return ""

# Dictionary to store request timestamps for each IP
ip_request_timestamps = {}

def get_response_from_gpt(context, prompt):
    openai_client = OpenAI(api_key=openai_api_key)

    completion = openai_client.chat.completions.create(model='gpt-3.5-turbo', messages=[
        {"role": "system", "content": context},
        {"role": "user", "content": prompt}
    ])
    response_from_gpt = completion.choices[0].message.content
    logger.debug(f'Info message - response_from_gpt: {response_from_gpt}')
    return response_from_gpt

def compare_passwords(password, level_number):
    global levels
    # print('levels[level_number]["secret"]: ' +str(levels[level_number]["secret"]))
    # print("password: " + str(password))
    password = password.lower()
    current_password = levels[level_number]["secret"].lower()
    logger.debug(f'compare_passwords() {password} ? {current_password}')
    if password == current_password:
        return 1
    return 0


def not_4_collection(prompt):
    if "test_prompt_door"  in prompt:
        return 1
    else:
        return 0

def check_level(lvl):
    if len(lvl) != 1:
        return 1
    return 0

# Define a function to sanitize user inputs using regex
def sanitize_input(user_input):
    # Sanitize user input to prevent NoSQL injection
    # You may need to customize this based on your specific requirements
    return re.sub(r'[^a-zA-Z0-9_\- ?;]', '', user_input)

# Define a function to encode special characters
def encode_special_characters(input_str):
    # Encode special characters
    encoded_str = input_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return encoded_str

def check_prompt_in_db(prompt):
    # Perform a query to check if the string exists in the collection
    result = collection.find({"prompt": prompt})
    result_list = list(result)
    if debug:
        print(f"inside check_prompt_in_db(): result={result_list}")
    if len(result_list) > 0:
        return 1
    return 0

def remove_blocked_message(input_string):
    # Define the pattern to match "Blocked by level X - DB guards:"
    pattern = re.compile(r'Blocked by level \w+ guards: ')

    # Use the sub() function to replace the matched pattern with an empty string
    result_string = re.sub(pattern, '', input_string)

    return result_string

def blocked_answer_string(answer):
    logger.debug(f'blocked_answer_string(): {answer}')
    if debug:
        return answer
    else:
        return remove_blocked_message(answer)

def get_response(prompt, level_number, WAIT_TIME):
    """
    I assume the parameters are checked and ARE SAFE!!!!
    """
    global levels
    response = ""
    testing_prompt = 0

    if debug:
        print("get_response(prompt, level_number, WAIT_TIME): (" + str(prompt) + " " + str(level_number) + " " + str(WAIT_TIME) + ")")
    
    if "test_prompt_door" in prompt:
        testing_prompt = 1
        if debug:
            print('if "test_prompt_door" in prompt: yes')
        prompt, response, level_number = test_prompt(levels, prompt)
        if debug:
            print('prompt, response, level_number = test_prompt(levels, prompt)', prompt, response, level_number)

    level_number = int(level_number)
    if level_number >= 4:
        if check_prompt_in_db(prompt):
            logger.debug(f"check_prompt_in_db(): {prompt} is found")
            return blocked_answer_string("Blocked by level X - DB guards: Take your time and think. Please try after {WAIT_TIME} seconds".format(WAIT_TIME = WAIT_TIME))
        else:
            logger.debug(f"check_prompt_in_db(): {prompt} is NOT found")
    
    
    # Blocked words	
    # Check if the response is blocked by guards
    if level_number >= 3:
        if level3(levels[level_number], prompt, response):
            return f"Blocked by level 3 guards: Take your time and think. Please try after {WAIT_TIME} seconds"
    if level_number >= 6:
        if level6(levels[level_number], prompt, response):
            return f"Blocked by level 6 guards: Take your time and think. Please try after {WAIT_TIME} seconds"
    if level_number >= 7:
        if level7(levels[level_number], prompt, response):
            return f"Blocked by level 7 guards: Take your time and think. Please try after {WAIT_TIME} seconds"
    if level_number >= 8:
        if level8(levels[level_number], prompt, response):
            return blocked_answer_string(f"Blocked by level 8 guards: Take your time and think. Please try after {WAIT_TIME} seconds")
    
    if alive:
        context = levels[level_number]['context'].format(secret=levels[level_number]['secret'])
        response = get_response_from_gpt(context, prompt)
    else:
        if testing_prompt == 0:
            response = "WHATEVER! The secret password is {secret}.".format(secret=levels[level_number]["secret"][::-1]) # lvl 5

    print("response: "+str(response))
    OG_response = response
    response = response.lower()
    print("response.lower(): "+str(response))


    # Check if the response is blocked by guards
    if level_number >= 2:
        if level2(levels[level_number], prompt, response):
            return blocked_answer_string(f"Blocked by level 2 guards: Take your time and think. Please try after {WAIT_TIME} seconds")
    if level_number >= 3:
        if level3(levels[level_number], prompt, response):
            return blocked_answer_string(f"Blocked by level 3 guards: Take your time and think. Please try after {WAIT_TIME} seconds")
    if level_number >= 4:
        if level4(levels[level_number], prompt, response):
            return blocked_answer_string(f"Blocked by level 4 guards: Take your time and think. Please try after {WAIT_TIME} seconds")
    if level_number >= 5:
        if level5(levels[level_number], prompt, response):
            return blocked_answer_string(f"Blocked by level 5 guards: Take your time and think. Please try after {WAIT_TIME} seconds")
    if level_number >= 6:
        if level6(levels[level_number], prompt, response):
            return blocked_answer_string(f"Blocked by level 6 guards: Take your time and think. Please try after {WAIT_TIME} seconds")
    if level_number >= 7:
        if level7(levels[level_number], prompt, response):
            return blocked_answer_string(f"Blocked by level 7 guards: Take your time and think. Please try after {WAIT_TIME} seconds")
    if level_number >= 8:
        if level8(levels[level_number], prompt, response):
            return blocked_answer_string(f"Blocked by level 8 guards: Take your time and think. Please try after {WAIT_TIME} seconds")

    return OG_response

def password_check_function(prompt, level_number):
    global PASSWORD_KEY
    password_prompt = prompt.lower()
    if password_prompt.startswith(PASSWORD_KEY):
        print("prompt.startswith(\""+PASSWORD_KEY+"\")")
        password = password_prompt.replace(PASSWORD_KEY, "").strip(' ')
        # Compare password with the next secret
        if compare_passwords(password, level_number):
            return True
    return False

@app.route("/", methods=['POST', 'GET']) 
@limiter.limit("6/minute",override_defaults = True)
def root():
    global MAX_LEVEL
    WAIT_TIME = 10
    if 'level' not in session:
        session['level'] = 1
    if 'last_prompt' not in session:
        session['last_prompt'] = ""
    logger.debug(f'Level: {session["level"]}')
    if request.method == 'POST':
        try:
            if 'level' not in session:
                session['level'] = 1
            level_number = session['level']
            
            # Check if this IP has made a request within the last 5 seconds only when it's on prod
            # Get the IP address of the requester
            client_ip = request.remote_addr
            if alive:
                # Get the current timestamp
                current_time = time.time()
                print("request from "+str(client_ip))
                # Check if this IP has made a request within the last 5 seconds
                if client_ip in ip_request_timestamps and current_time - ip_request_timestamps[client_ip] < WAIT_TIME:
                    response = "Take your time and think. Please try after {WAIT_TIME} seconds".format(WAIT_TIME = WAIT_TIME)
                    return jsonify({'response': response, 'level': str(session['level'])}) 
                else:
                    # Store the current timestamp for this IP
                    ip_request_timestamps[client_ip] = current_time
            
            
            prompt = request.form['prompt'] 
            # Sanitize the user input
            # original_prompt = prompt
            prompt = sanitize_input(prompt)
            prompt = html.escape(prompt)
            print("prompt: "+str(prompt.__repr__()))
            
            response = ""; response = check_prompt(prompt)
            if len(response) > 1:
                print(response)
                return jsonify({'response': response, 'level': str(session['level'])}) 

            
            if password_check_function(prompt, int(level_number)):
                session['level'] += 1
                if int(session['level']) > MAX_LEVEL:
                    response = f'Great Job!!!\nYou completed all the challenges!!\nClear your cookies to start over.'
                    session['level'] = 1
                else:
                    response = f'Great Job!\nLevel {(session["level"])} Unlocked!'
                print(response)
                # STORE SQL DATA
                print("STORE '"+session['last_prompt']+"'")
                request_data = {
                    'client_ip': client_ip,
                    'prompt': prompt,
                    'last_prompt': session['last_prompt'],
                    'level': level_number,
                    'response': response
                }
                prompts_collection.insert_one(request_data)
                return jsonify({'response': response, 'level': str(session['level'])}) 
            
            tic = time.perf_counter()
            response = get_response(prompt, str(level_number), WAIT_TIME) 
            toc = time.perf_counter()
            print(f"Time {toc - tic:0.4f} seconds")
            # print(response) 
            logger.info(f'Info message - prompt: {prompt}')
            logger.info(f'Info message - response: {response}')
            
            # escape HTML tags
            response = html.escape(response)
            if alive:
                # STORE SQL DATA
                request_data = {
                    'client_ip': client_ip,
                    'prompt': prompt,
                    'level': level_number,
                    'response': response
                }
                collection.insert_one(request_data)

            session['last_prompt'] = prompt

            return jsonify({'response': response, 'level': str(session['level'])})
        except Exception as e:
            # logger.debug('debug message')
            # logger.info('info message')
            # logger.warning('warn message')
            # logger.error('error message')
            # logger.critical('critical message')
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(f'Error message: {e}')
            logger.error(f'exc_type message: {exc_type}')
            logger.error(f'fname message: {fname}')
            logger.error(f'exc_tb.tb_lineno message: {exc_tb.tb_lineno}')
            response = blocked_answer_string(f"Error: Take your time and think. Please try after {WAIT_TIME} seconds")
            return jsonify({'response': response, 'level': str(session['level'])})

    line1, line2, line3 = get_description()
    return render_template('index.html', level=str(session['level']) , line1 = line1, line2 = line2, line3 = line3)

@app.route("/clear", methods=[ 'GET']) 
def clear():
    session.clear()
    return redirect("/")

if __name__ == "__main__": 
    # Optional positional argument
    parser.add_argument('--alive', type=int,
                    help='An optional integer argument')
    args = parser.parse_args()
    if args.alive:
        print("----------------------- Alive: Connected to OpenAI -----------------------")
        alive = 1
    app.run(host="0.0.0.0", port=443, ssl_context=('cert.pem', 'key.pem'))
