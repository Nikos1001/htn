from flask import Flask, jsonify, request
from flask_cors import CORS
from psycopg2 import OperationalError
import psycopg2
import cohere
import html2text
from urllib.request import urlopen

co = cohere.Client('66dAWH9FogjnzRBEt8NT0sWp0m8lOZmbnFN83Rgv')
db = psycopg2.connect('postgresql://hiatus:zK8yCsqmKmIdEKSn0_8WYA@pet-indri-3361.g95.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full')

def build_deck(text):
    # Generate prompt based on text from body
    prompt = """This is a bot that generates questions and answers for a flashcard based on the text input. 
                Example (FOLLOW THIS FORMAT): 
                Question: What is X  
                Answer: X is ...
                
                Text input: 
                """ 

    prompt += text
    prompt += "\n List of questions and answers: \n"

    response = co.generate(
        model="command-nightly", 
        prompt=prompt,
        max_tokens=600
    )

    # Raw data from cohere
    rawData = ""

    # iterate through the generations
    for generation in response.generations:
        rawData += generation.text


    # Split the data into lines to parse the questions
    lines = rawData.splitlines()

    # Create the json 
    json = {
        "cards": [],
        "title": "temptitle"
    }
    #TODO ADD DECK TITLE

    print(lines)

    # Iterate through the lines
    for line in lines:
        # If the line contains question, then it is a question card
        if "question" in line.lower():
            # Add the question card to the deck
            print("Question: " + line)
            # Iterate to the next line to find the answer
            print("Answer: " + lines[lines.index(line) + 1])
            # Add the answer card to the deck
            json["cards"].append({
                "question": line.replace("Question", "").replace(": ", "").replace("question", ""),
                "answer": lines[lines.index(line) + 1].replace("Answer", "").replace(":", "").replace("answer", "")
            })
    return json 

def sql(query):
    db.autocommit = True
    cursor = db.cursor()
    try:
        print(f"Query {query} successful")
        cursor.execute(query)
    except OperationalError as err:
        print(f"Error {err}")

db.autocommit = True #disgusting line of code, figure this out!

def execute_query(query):
    cursor = db.cursor()
    try:
        cursor.execute(query)
        print("Query success")
    except OperationalError as err:
        print(f"Error {err}")

execute_query("CREATE TABLE IF NOT EXISTS deck_list (id SERIAL PRIMARY KEY, deck JSON)")

def add_to_db(deck):
    add_query = f"INSERT INTO deck_list (deck) VALUES ('" + f"{deck}".replace('"', "\\\"").replace('\'', '"') + "')"
    print(deck) #DA!!! print statement
    execute_query(add_query)

def retrieve_db():
    deck_list = []

    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM deck_list")
        for deck in cursor.fetchall():
            deck_list.append(deck[1])
    except OperationalError as err:
        print(f"The error '{err}' occurred")

    return deck_list

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    data = {
        'message': 'Working test'
    }
    return jsonify(data)

@app.route('/generate', methods=['POST'])
def getCardsText():
    # Get body of request
    data = request.get_json()
    print(data)

    # Generate prompt based on text from body
    text = data['text']
    deck = build_deck(text)
    data = {
        'deck': deck,
    }

    # Add the deck to the database
    add_to_db(deck) 

    return jsonify(data)

@app.route('/img_generate', methods=['POST'])
def img_generate():
    file = request.files['file']
    path = 'files/' + file.filename
    file.save(path)

    """Detects text in the file."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    
    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )

    # Get the text from the image
    text = texts[0].description

    # Enter the text into the make_deck
    deck = build_deck(text)

    data = {
        'deck': deck,
    }

    # return
    return jsonify(data)

@app.route('/webscrape_generate', methods=['POST'])
def webscrape_generate():
    data = request.get_json() 
    url = data['url']
    html = urlopen(url).read().decode('utf-8')
    text = html2text.html2text(html)
    if len(text) > 4096:
        text = text[0:4096]
    deck = build_deck(text)
    data = {
        'deck': deck,
    }
    return jsonify(data)

@app.route('/decks', methods=['GET', 'POST'])
def decks():
    if request.method == 'GET':
        return jsonify(retrieve_db())
    else:
        data = request.get_json()
        add_to_db(data)
        return jsonify({})

app.run(port=8080)
