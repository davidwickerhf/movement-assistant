# FFF Transparency WG
## How to develop for the bot
To develop for the bot, a couple of steps need to be undertaken aside from forking and cloning the repository to your local PC.
The repository contains three branches:
- Master -> This branch is directly connected to the server on which is running the stable version of the code.
- Testing -> This branch is connected to a different server, which runs the code in development. This branch is used for testing before the code get's pushed to the master.
- Development -> This is the development branch of the repository. It is not tied to any server. This branch get's committed to the Testing branch.

To develop for this bot, add pull requests to the Development Branch.

After you fork and clone the development repository, you need to follow the steps below to be able to run the code on your local machine:

### Setup Google API tokens:
- Create a Google Console Project at [Google API Console](https://console.developers.google.com/apis/credentials?project=bot-testing-273208&authuser=1)
- Enable the Calendar, Drive and Sheets APIs from the API Library
- Create a service account
  - go to the Create Credentials section
  - Select the Google Drive API
  - Select "Web Server" to the second question
  - Select "Application Data" to the third question
  - Select "No, I'm not using them
  - tap on "What credentials do I need?"
  - Give a name to the service account
  - Select "Project > Editor" as role
  - Select JSON key type and hit continue
- Download the generated key as "client_secret.json" and place it in the [Secrets](secrets) folder of your local cloned repository. 
> Make sure all the files in the secrets folder are always included in the [.gitignore](.gitignore). They should already be inserted, but always check before committing the code to a git repository.
### Setup Trello Tokens and Keys
- Get the Trello Key from https://trello.com/app-key
- Get the Trello Token from https://trello.com/app-key as local testing
### Setup Telegram Bot
- Create a Telegram bot with @BotFather
- Get the generated Token
### Share a designated calendar
- Share a designated calendar you are owner of to the email address of the Service Account you created when enabling the Google APIs. Make sure to give permission to make changes and manage sharing. The Service Account email address can also be found in your newly generated client_secret.json
### Paste the tokens/keys you obtained in the [set_env.py](secrets/env_variables.json) file
> If no such file is present in the secrets folder, create a new env_variables.json file (make sure the filename is exactly that) and insert the code below, pasting the different tokens/variables instead of insert_here:
```
{
    "SERVER_APP_DOMAIN": "insert_here"
    "TRELLO_KEY": "insert_here",
    "TRELLO_TOKEN": "insert_here",
    "BOT_TOKEN": "insert_here",
    "CALENDAR_ID": "insert_here",
    "GDRIVE_EMAIL": "insert_here",
    "SPREADSHEET": "insert_here_if_available",
    "TRELLO_BOARD_ID": "insert_here_if_available"
  }
```
- SERVER APP DOMAIN (The url that will be used as webhook to receive POST requests from the Telegram API)
> Insert a value in SERVER APP DOMAIN only if you are running the code on a server like Heroku
- TRELLO KEY
- TRELLO TOKEN
- TELEGRAM BOT TOKEN
- GCALENDAR ID (this is either id of the calendar, which is found in the "Integrate Calendar" section of the settings of the calendar you want to access)
- G DRIVE EMAIL (The email you want the database to be shared with)
- SPREADSHEET (the Id of the database spreadsheet. This field should be left empty: "", if you don't have a correctly formatted database sheet yet)
- TRELLO_BOARD_ID (This field should be left empty: "", if you don't have a correctly formatted Trello Board yet))
### Setup virtual enviroment
- Open your comand prompt
- create a python virtual enviroemnt in the folder you have cloned the repository to
- activate the enviroment
- Install the libraries running the code line: 
```
pip install -r requirements.txt
```

There you go! Now run the [bot.py](bot.py) file and check if everything is working fine. If you encounter any errors, feel free to add the procedure you undertook and the error code as an issue in the development branch of the repository, mentioning @davidwickerhf 

