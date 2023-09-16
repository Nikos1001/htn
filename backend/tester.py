import requests

# Make a POST request to the server on port 8080 with a body containing JSON data
response = requests.post('http://localhost:8080/getCardsText', json={"text": "the sun is a star, the moon is a satellite"})

# Print the JSON response from the server
print(response)
print(response.json())