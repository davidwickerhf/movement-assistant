import json

# INSERT HERE THE CLIENT SECRET
client_secret = {}
# Run the this file only to get the client secret in a JSON string format in your console.
# Once you have the string, paste it as enviroment variable on the server you are running the code on with the key CLIENT_SECRET

string = json.dumps(client_secret)
print(string)
