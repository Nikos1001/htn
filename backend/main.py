from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import cohere


co = cohere.Client('66dAWH9FogjnzRBEt8NT0sWp0m8lOZmbnFN83Rgv')
db = psycopg2.connect('postgresql://hiatus:6H3NXwrWDDktAPda9k3pbg@lake-centaur-5448.g8z.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full')

# def sql(sql):
#     with db.cursor() as cur:
#         cur.execute(sql)
#         db.commit()

# sql('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name VARCHAR(255));')

# # Create a table to represent the global decks
# sql('CREATE TABLE IF NOT EXISTS decks (id SERIAL PRIMARY KEY, name TEXT, user_id INT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id));')

# # Create a table to represent flashcards
# sql('CREATE TABLE IF NOT EXISTS flashcards (id SERIAL PRIMARY KEY, question TEXT, answer TEXT, deck_id INT NOT NULL, FOREIGN KEY (deck_id) REFERENCES decks (id));')

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

def add_to_db(deckJson): 
    listOfCards = deckJson["cards"]
    title = deckJson["title"]

    # Add the deck to the database
    sql("INSERT INTO decks (name, user_id) VALUES ('" + title + "', 1);")

    # Get the id of the deck that was just added
    deckId = sql("SELECT id FROM decks WHERE name='" + title + "';")

    # Iterate through the cards and add them to the database
    for card in listOfCards:
        sql("INSERT INTO flashcards (question, answer, deck_id) VALUES ('" + card["question"] + "', '" + card["answer"] + "', " + deckId + ");")
    
    return 0

build_deck("The sun is a star. The moon is a satellite.")


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
    }

    # Add the deck to the database
    # add_to_db(deck) 

    return jsonify(data)

@app.route('/img_generate', methods=['POST'])
def img_generate():
    file = request.files['file']
    file.save('files/' + file.filename)

    return '123'

app.run(port=8080)