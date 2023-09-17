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
    prompt = f"""This is a bot that generates questions and answers for a flashcard based on the text input. The questions MUST focus on the context provided.
                Example (FOLLOW THIS FORMAT):
                Question: What is X  
                Answer: X is ...
                
                Text input: 
                """ 
    prompt += text
    prompt += '\nPlease use ' + title + ' in your questions.\n'
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
            try:
                print("Question: " + line)
                # Iterate to the next line to find the answer
                print("Answer: " + lines[lines.index(line) + 1])
                # Add the answer card to the deck
                json["cards"].append({
                    "question": line.replace("Question", "").replace(": ", "").replace("question", ""),
                    "answer": lines[lines.index(line) + 1].replace("Answer", "").replace(":", "").replace("answer", "")
                })
            except:
                pass
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
    title = data['title']

    prompt = f"""
    Create a bullet list of three to five questions using the keywords {title} given a text passage. 
    Length: each question must be fifteen to twenty words.    

    Text: In common usage, a force is a push or a pull, as the examples in Figure 4.1 illustrate. In football, an offensive lineman pushes against his opponent. The tow bar attached to a speeding boat pulls a water skier. Forces such as those that push against the football player or pull the skier are called contact forces, because they arise from the physical contact between two objects. There are circumstances, however, in which two objects exert forces on one another even though they are not touching. Such forces are referred to as noncontact forces or action-at-a-distance forces. One example of such a noncontact force occurs when a diver is pulled toward the earth because of the force of gravity. 
    Questions:
    - What is a force?
    - What are contact forces?
    - What are action-at-a-distance forces?

    Text: Physical and chemical changes are a manifestation of physical and chemical properties. A physical property is one that a substance displays without changing its composition, whereas a chemical property is one that a substance displays only by changing its composition via a chemical change. The smell of gasoline is a physical property- gasoline does not change its composition when it exhibits its odour. The combustibility of gasoline, in contrast, is a chemical property- gasoline does change its composition when it burns, turning into completely new substances (primarily carbon dioxide and water). Physical properties include odour, taste, colour, appearance, melting point, boiling point, and density. Chemical properties include corrosiveness, flammability, acidity, toxicity, and other such characteristics
    Questions:
    - What are chemical properties?
    - What are physical properties? 
    - List one example of a chemical property
    - List one example of a physical property 

    Text: {text}
    Questions:
    - 
    """
    response = co.generate(
        model="command-nightly", 
        prompt=prompt,
        max_tokens=250,
        temperature=0
    )

    print(prompt)

    raw_data = ""

    for generation in response.generations:
        raw_data += generation.text

    print(raw_data)

    lines = raw_data.split('\n')
    questions = []
    for line in lines:
        if '- ' in line or 'question: ' in line.lower() or re.search('[0-9]*\.', line):
            questions.append(line.replace('- ', '').replace('Question: ', '').replace('question: ', '')) 

    return questions 

@app.route('/answer', methods=['POST'])
def answer():
    data = request.get_json()
    text = data['text']
    question = data['question']
    answer = data['answer']

    if len(answer) == 0:
        return 'Incorrect'

    prompt = f"""
    Given a text passage {text}, question{question} 

    """

    # prompt += 'Task: state if input and aoutiput match. If do not match, explain why in at most twenty words. If very similar, state that input and output match.    
    # prompt += """
    # Text: The animal populace of the poorly run Manor Farm near Willingdon, England, is ripened for rebellion by neglect at the hands of the irresponsible and alcoholic farmer, Mr. Jones. One night, the exalted boar, Old Major, holds a conference, at which he calls for the overthrow of humans and teaches the animals a revolutionary song called "Beasts of England". When Old Major dies, two young pigs, Snowball and Napoleon, assume command and stage a revolt, driving Mr. Jones off the farm and renaming the property "Animal Farm". They adopt the Seven Commandments of Animalism, the most important of which is, "All animals are equal". The decree is painted in large letters on one side of the barn. Snowball teaches the animals to read and write, while Napoleon educates young puppies on the principles of Animalism. To commemorate the start of Animal Farm, Snowball raises a green flag with a white hoof and horn. Food is plentiful, and the farm runs smoothly. The pigs elevate themselves to positions of leadership and set aside special food items, ostensibly for their health. Following an unsuccessful attempt by Mr. Jones and his associates to retake the farm (later dubbed the "Battle of the Cowshed"), Snowball announces his plans to modernise the farm by building a windmill. Napoleon disputes this idea, and matters come to a head, which culminates in Napoleon's dogs chasing Snowball away and Napoleon effectively declaring himself supreme commander.
    # The following is a list of questions with good and bad feedback.
    # Question: Why does Old Major hold a conference?
    # Answer: To call for the overthrow of people at the farm.
    # Good feedback: Correct.

    # Question: What is the role of Old Major in the story?
    # Answer: He is a pig.
    # The following feedback is good because it adds necessary detail that was missing from the answer.
    # Good Feedback: Incorrect. Old Major plays a signficant role in starting the animal rebellion.
    # The following feedback is bad, because it fails to mention Old Major's significance to the plot
    # Bad Feedback: Correct.

    # Question: What is Animalism?
    # Answer: The ideology of the animal-run farm.
    # The following feedback is good because the answer gave all the detail it needed to.
    # Good Feedback: Correct.
    # The following feedback is bad because it gives too much detail. 
    # Bad Feedback: Incorrect. Animalism was adopted after the farm was renamed to "animal farm". Animalism has 7 commandments, the most important of which being "All animals are equal". Animalism was taught to puppies by Napoleon who assumed power after the revolution.

    # Text: moraine, accumulation of rock debris (till) carried or deposited by a glacier. The material, which ranges in size from blocks or boulders (usually faceted or striated) to sand and clay, is unstratified when dropped by the glacier and shows no sorting or bedding. Several kinds of moraines are recognized:
    # A ground moraine consists of an irregular blanket of till deposited under a glacier. Composed mainly of clay and sand, it is the most widespread deposit of continental glaciers. Although seldom more than 5 metres (15 feet) thick, it may attain a thickness of 20 m.
    # A terminal, or end, moraine consists of a ridgelike accumulation of glacial debris pushed forward by the leading glacial snout and dumped at the outermost edge of any given ice advance. It curves convexly down the valley and may extend up the sides as lateral moraines. It may appear as a belt of hilly ground with knobs and kettles.
    # A lateral moraine consists of debris derived by erosion and avalanche from the valley wall onto the edge of a glacier and ultimately deposited as an elongate ridge when the glacier recedes.
    # A medial moraine consists of a long, narrow line or zone of debris formed when lateral moraines join at the intersection of two ice streams; the resultant moraine is in the middle of the combined glacier. It is deposited as a ridge, roughly parallel to the direction of ice movement.
    # A recessional moraine consists of a secondary terminal moraine deposited during a temporary glacial standstill. Such deposits reveal the history of glacial retreats along the valley; in some instances 10 or more recessional moraines are present in a given valley, and the ages of growing trees or other sources of dates provide a chronology of glacial movements.

    # The following is a list of questions with good and bad feedback.
    # Question: What is a moraine?
    # Answer: A moraine is rock debris carried by a glacier
    # Good Feedback: Correct
    # The following feedback is bad because it does not accurately represent the given material
    # Bad Feedback: Incorrect. A moraine is a glacier full of rock debris.

    # Question: How is a lateral moraine formed?
    # Answer: A lateral moraine forms due to errosion.
    # The following feedback is bad because it fails to mention an important detail of lateral moraines.
    # Bad Feedback: Correct.
    # Good Feedback: Incorrect. A lateral moraine forms due to erosion from avalanches.

    # MOST IMPORTANTLY, the bot must ONLY give good feedback.

    # """
    # # prompt += 'Question: What is the capital of England?\n'
    # # prompt += 'Answer: London is the capital of England.\n'
    # # prompt += 'Feedback: Correct.\n'
    # # prompt += 'Question: What is the capital of France?\n'
    # # prompt += 'Answer: Rome is the capital of France.\n'
    # # prompt += 'Feedback: Incorrect. Rome is the capital of Italy, not France. The capital of France is Paris.\n\n'
    # prompt += 'Text input:\n'
    # prompt += text
    # prompt += '\nQuestion: ' + question + '\n'
    # prompt += 'Answer: ' + answer + '\n'
    # prompt += 'Feedback:\n'

    answers = co.generate(
        model="command-nightly",
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


app.run(port=8080)