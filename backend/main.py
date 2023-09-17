from flask import Flask, jsonify, request
from flask_cors import CORS
from psycopg2 import OperationalError
import psycopg2
import cohere
import html2text
from urllib.request import urlopen
import json
from bs4 import BeautifulSoup
import re

# IMPORTS FOR DECK GENERATION
import db 

# Initialize cohere client 
co = cohere.Client('66dAWH9FogjnzRBEt8NT0sWp0m8lOZmbnFN83Rgv')
# Initialize postgresql client

def build_deck(text, title = ""):
    # Generate prompt based on text from body
    prompt = f"""
    Create a bullet list of three to five questions for flashcards using the keywords {title} given a text passage. 
    Length: each question and answer must be fifteen to twenty words. 
    
    Use the following format for questions and answers:
    Text: In common usage, a force is a push or a pull, as the examples in Figure 4.1 illustrate. In football, an offensive lineman pushes against his opponent. The tow bar attached to a speeding boat pulls a water skier. Forces such as those that push against the football player or pull the skier are called contact forces, because they arise from the physical contact between two objects. There are circumstances, however, in which two objects exert forces on one another even though they are not touching. Such forces are referred to as noncontact forces or action-at-a-distance forces. One example of such a noncontact force occurs when a diver is pulled toward the earth because of the force of gravity. 
    Question:
    - What is a force?
    Answer:
    - A force is a push or a pull.
    Question:
    - What are contact forces?
    Answer:
    - Contact forces are forces that arise from the physical contact between two objects.
    Question:
    - What are action-at-a-distance forces?
    Answer:
    - Forces resulting between two object even though they are not touching

    Text: Physical and chemical changes are a manifestation of physical and chemical properties. A physical property is one that a substance displays without changing its composition, whereas a chemical property is one that a substance displays only by changing its composition via a chemical change. The smell of gasoline is a physical property-gasoline does not change its composition when it exhibits its odour. The combustibility of gasoline, in contrast, is a chemical property- gasoline does change its composition when it burns, turning into completely new substances (primarily carbon dioxide and water). Physical properties include odour, taste, colour, appearance, melting point, boiling point, and density. Chemical properties include corrosiveness, flammability, acidity, toxicity, and other such characteristics
    Question:
    - What are chemical properties?
    Answer:
    - A property that a substance displays only by changing its composition
    Question:
    - List chemical properties
    Answer:
    - Chemical properties include corrosiveness, flammability, acidity, and toxicity
    Question:
    - Is burning gasoline a physical or chemical change?
    Answer:
    - Burning gasoline is a chemical change.

    Generate the following questions and answers for the given text:
    Text: {text}

    Question:
    """

    #currently fixing the input to improve

    response = co.generate(
        model="command", 
        prompt=prompt,
        max_tokens=250,
        temperature = 0
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

    content_lines = []
    for line in lines:
        if '- ' in line or 'Answer: ' in line:
            content_lines.append(line.replace('- ', '').replace('Answer: ', ''))

    for i in range(0, (len(content_lines) // 2) * 2, 2):
        json['cards'].append({
            'question': content_lines[i].replace('- ', ''),
            'answer': content_lines[i + 1].replace('Answer: ', '')
        })

    print(lines)

    # Iterate through the lines
    # for line in lines:
    #     If the line contains question, then it is a question card
    #     if "question" in line.lower():
    #         Add the question card to the deck
    #         try:
    #             print("Question: " + line)
    #             Iterate to the next line to find the answer
    #             print("Answer: " + lines[lines.index(line) + 1])
    #             Add the answer card to the deck
    #             json["cards"].append({
    #                 "question": line.replace("Question", "").replace(": ", "").replace("question", ""),
    #                 "answer": lines[lines.index(line) + 1].replace("Answer", "").replace(":", "").replace("answer", "")
    #             })
    #         except:
    #             pass
    # return json 

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
    # text = html2text.html2text(html)
    text = ''
    for elem in BeautifulSoup(html).findAll('p'):
        text += elem.getText()
    print(html, text)

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

    return build_deck(text)['cards']

@app.route('/answer', methods=['POST'])
def answer():
    data = request.get_json()
    text = data['text']
    question = data['question']
    computer_answer = data['computer_answer']
    answer = data['answer']

    print('!!!!!!!!!!' + computer_answer)

    if len(answer) == 0:
        return 'Incorrect'

    prompt = f"""
    {text}
    Compare the computer answer {computer_answer} to the user answer {answer} and give feedback. 
    Length: the feedback must be between fifteen and twenty words.

    Use the following format for feedback:
    If the given answer and user answer are similar, state correct.
    If the given answer and user answer are very different or the user answer is incomplete, state incorrect, and describe the differences.
 
    Text: In common usage, a force is a push or a pull, as the examples in Figure 4.1 illustrate. In football, an offensive lineman pushes against his opponent. The tow bar attached to a speeding boat pulls a water skier. Forces such as those that push against the football player or pull the skier are called contact forces, because they arise from the physical contact between two objects. There are circumstances, however, in which two objects exert forces on one another even though they are not touching. Such forces are referred to as noncontact forces or action-at-a-distance forces. One example of such a noncontact force occurs when a diver is pulled toward the earth because of the force of gravity. 
    Question: What is a force?
    Answer: A force is a push or pull.
    User answer: Forces are pushes or pulls.
    Feedback: Correct.

    Text: In common usage, a force is a push or a pull, as the examples in Figure 4.1 illustrate. In football, an offensive lineman pushes against his opponent. The tow bar attached to a speeding boat pulls a water skier. Forces such as those that push against the football player or pull the skier are called contact forces, because they arise from the physical contact between two objects. There are circumstances, however, in which two objects exert forces on one another even though they are not touching. Such forces are referred to as noncontact forces or action-at-a-distance forces. One example of such a noncontact force occurs when a diver is pulled toward the earth because of the force of gravity. 
    Question: What is a force?
    Answer: A force is a push or pull.
    User answer: A force is a pull.
    Feedback: Incorrect. A force can be either a push or a pull.

    Text: In common usage, a force is a push or a pull, as the examples in Figure 4.1 illustrate. In football, an offensive lineman pushes against his opponent. The tow bar attached to a speeding boat pulls a water skier. Forces such as those that push against the football player or pull the skier are called contact forces, because they arise from the physical contact between two objects. There are circumstances, however, in which two objects exert forces on one another even though they are not touching. Such forces are referred to as noncontact forces or action-at-a-distance forces. One example of such a noncontact force occurs when a diver is pulled toward the earth because of the force of gravity. 
    Question: What are contact forces?
    Answer: Contact forces are forces that arise from the physical contact between two objects.
    User answer: Contact forces are forces resulting from physical contact.
    Feedback: Correct.

    Text: In common usage, a force is a push or a pull, as the examples in Figure 4.1 illustrate. In football, an offensive lineman pushes against his opponent. The tow bar attached to a speeding boat pulls a water skier. Forces such as those that push against the football player or pull the skier are called contact forces, because they arise from the physical contact between two objects. There are circumstances, however, in which two objects exert forces on one another even though they are not touching. Such forces are referred to as noncontact forces or action-at-a-distance forces. One example of such a noncontact force occurs when a diver is pulled toward the earth because of the force of gravity. 
    Question: What are contact forces?
    Answer: Contact forces are forces that arise from the physical contact between two objects.
    User answer: Contact forces are forces not resulting from physical contact.
    Feedback: Incorrect. Contact forces result from physical contact between two objects.

    Text: Any piece of informaion
    Question: Any question
    Answer: I am not sure / I don't know
    Feedback: Incorrect. 

    Text: {text}
    Question: {question}
    Answer: {computer_answer}
    User answer: {answer}
    Feedback:
    """

    answers = co.generate(
        model="command",
        prompt = prompt,
        max_tokens=50,
        temperature=0
    )

    raw_data = ""

    for generation in answers.generations:
        raw_data += generation.text

    lines = raw_data.split('\n')
    
    feedbacks = []
    for line in lines:
        feedback = line.replace('Feedback:', '').replace('feedback:', '')
        feedbacks.append(feedback) 

    return {'feedback': raw_data} 


app.run(port=8080, host="10.33.132.221")