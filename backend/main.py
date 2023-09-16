from flask import Flask, jsonify, request
from flask_cors import CORS
from psycopg2 import OperationalError
import psycopg2
import cohere

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
        "title": "Temp Title"
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

def sql(query):
    db.autocommit = True
    cursor = db.cursor()
    try:
        print(f"Query {query} successful")
        cursor.execute(query)
    except OperationalError as err:
        print(f"Error {err}")

def execute_query(query):
    db.autocommit = True
    cursor = db.cursor()
    try:
        cursor.execute(query)
        print("Query success")
    except OperationalError as err:
        print(f"Error {err}")

execute_query("""
CREATE TABLE IF NOT EXISTS decks (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL, 
  deck JSON,
)
""")

# def sql(query):
#     cursor = db.cursor()
#     cursor.execute(query)
#     db.commit()
#     return cursor.fetchall()

# def add_to_db(deckJson): 
#     listOfCards = deckJson["cards"]
#     title = deckJson["title"]

#     # Add the deck to the database
#     sql("INSERT INTO decks (name, user_id) VALUES ('" + title + "', 1);")

#     # Get the id of the deck that was just added
#     deckId = sql("SELECT id FROM decks WHERE name='" + title + "';")

#     # Iterate through the cards and add them to the database
#     for card in listOfCards:
#         sql("INSERT INTO flashcards (question, answer, deck_id) VALUES ('" + card["question"] + "', '" + card["answer"] + "', " + deckId + ");")
    
#     return 0

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
    # add_to_db(deck) 

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
    


app.run(port=8080)