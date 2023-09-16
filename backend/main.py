from flask import Flask, jsonify, request
from flask_cors import CORS
from psycopg2 import OperationalError
import psycopg2
import cohere
import html2text
from urllib.request import urlopen
import json

# IMPORTS FOR DECK GENERATION
import db 

# Initialize cohere client 
co = cohere.Client('66dAWH9FogjnzRBEt8NT0sWp0m8lOZmbnFN83Rgv')
# Initialize postgresql client

def build_deck(text, title = ""):
    # Generate prompt based on text from body
    prompt = f"""This is a bot that generates questions and answers for a flashcard based on the text input. The questions MUST focus on the context provided.
                Example (FOLLOW THIS FORMAT):
                Question: What is X  
                Answer: X is ...
                
                Text input: 
                """ 
    prompt += text
    prompt += '\nPlease focus on this topic when creating your questions: ' + title + '\n'
    prompt += "List of questions and answers: \n"

    print('!!!!!!' + title)

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
    deck = build_deck(text, data['title'])
    data = {
        'deck': deck,
        'text': text
    }

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
        'text': text
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
    deck = build_deck(text, data["title"])
    data = {
        'deck': deck,
        'text': text
    }
    return jsonify(data)

@app.route('/decks', methods=['GET', 'POST'])
def decks():
    if request.method == 'GET':
        return jsonify(db.retrieve_db())
    else:
        data = request.get_json()
        db.add_to_db(data)
        return jsonify({})

@app.route('/question', methods=['POST'])
def question():
    data = request.get_json()
    text = data['text']
    prompt = 'This is a bot that generates comprehension questions based on the key concepts presented text input(general ideas, not specific examples).\n'
    prompt += 'Example output (FOLLOW THIS FORMAT)\n'
    prompt += 'Question: What is the capital of Great Britain?\n' 
    prompt += 'Text input:\n'
    prompt += text
    prompt += '\nList of questions:\n'
    response = co.generate(
        model="command-nightly", 
        prompt=prompt,
        max_tokens=100
    )

    raw_data = ""

    for generation in response.generations:
        raw_data += generation.text

    lines = raw_data.split('\n')
    questions = []
    for line in lines:
        if 'question:' in line.lower():
            question = line.replace('Question:', '').replace('question:', '')
            questions.append(question) 

    return questions 


app.run(port=8080)