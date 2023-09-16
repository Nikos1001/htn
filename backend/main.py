from flask import Flask, jsonify, request
from flask_cors import CORS

import cohere


co = cohere.Client('66dAWH9FogjnzRBEt8NT0sWp0m8lOZmbnFN83Rgv')

# Helper funcs 
def png_to_text():
    return 0

def pdf_to_text():
    return 0

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
        max_tokens=300
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
        "cards": []
    }

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

    print(json)
    return json 


app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    data = {
        'message': 'Working test'
    }
    return jsonify(data)

@app.route('/getCardsText', methods=['POST'])
def getCardsText():
    # Get body of request
    data = request.get_json()
    print(data)

    # Generate prompt based on text from body
    text = data['text']
    deck = build_deck(text)
    data = {
        'deck': deck,
        'message': 'Working test'
    }

    return jsonify(data)
 

app.run(port=8080)