from flask import Flask, jsonify, request

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

build_deck("""
Astatine is a chemical element with the symbol At and atomic number 85. It is the rarest naturally occurring element in the Earth's crust, occurring only as the decay product of various heavier elements. All of astatine's isotopes are short-lived; the most stable is astatine-210, with a half-life of 8.1 hours. A sample of the pure element has never been assembled, because any macroscopic specimen would be immediately vaporized by the heat of its radioactivity.

The bulk properties of astatine are not known with certainty. Many of them have been estimated from its position on the periodic table as a heavier analog of iodine, and a member of the halogens (the group of elements including fluorine, chlorine, bromine, and iodine). However, astatine also falls roughly along the dividing line between metals and nonmetals, and some metallic behavior has also been observed and predicted for it. Astatine is likely to have a dark or lustrous appearance and may be a semiconductor or possibly a metal. Chemically, several anionic species of astatine are known and most of its compounds resemble those of iodine, but it also sometimes displays metallic characteristics and shows some similarities to silver.

The first synthesis of astatine was in 1940 by Dale R. Corson, Kenneth Ross MacKenzie, and Emilio G. Segrè at the University of California, Berkeley, who named it from the Ancient Greek ἄστατος (astatos) 'unstable'. Four isotopes of astatine were subsequently found to be naturally occurring, although much less than one gram is present at any given time in the Earth's crust. Neither the most stable isotope, astatine-210, nor the medically useful astatine-211, occur naturally; they are usually produced by bombarding bismuth-209 with alpha particles.

""")

app = Flask(__name__)

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
 

if __name__ == '__main__':
    app.run(port=8080)
