# FFF Transparency WG
## How to develop for the bot
To develop for the bot, a couple of steps need to be undertaken aside from forking and cloning the repository to your local PC.
The repository contains three branches:
- Master -> This branch is directly connected to the server on which is running the stable version of the code.
- Testing -> This branch is connected to a different server, which runs the code in development. This branch is used for testing before the code get's pushed to the master.
- Development -> This is the development branch of the repository. It is not tied to any server. This branch get's committed to the Testing branch.

To develop for this bot, add pull requests to the Development Branch.

After you fork and clone the development repository, you need to follow the steps below to be able to run the code on your local machine:

### 1 - Setup Google API tokens:
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
### 2 - Setup Trello Tokens and Keys
- Get the Trello Key from https://trello.com/app-key
- Get the Trello Token from https://trello.com/app-key as local testing
### 3 - Setup Telegram Bot
- Create a Telegram bot with @BotFather
- Get the generated Token
### 4 - Share a designated calendar
- Share a designated calendar you are owner of to the email address of the Service Account you created when enabling the Google APIs. Make sure to give permission to make changes and manage sharing. The Service Account email address can also be found in your newly generated client_secret.json
### 5 - Paste the tokens/keys you obtained in the [env_variables.json](secrets/env_variables.json) file
> If no such file is present in the secrets folder, create a new env_variables.json file (make sure the filename is exactly that) and insert the code below, pasting the different tokens/variables instead of insert_here:
```
{
    "SERVER_APP_DOMAIN": "insert_here"
    "TRELLO_KEY": "insert_here",
    "TRELLO_TOKEN": "insert_here",
    "BOT_TOKEN": "insert_here",
    "BOT_USERNAME": "insert_here",
    "CALENDAR_ID": "insert_here",
    "GDRIVE_EMAIL": "insert_here",
    "SPREADSHEET": "insert_here_if_available",
    "TRELLO_BOARD_ID": "insert_here_if_available"
  }
```
- SERVER APP DOMAIN (The url that will be used as webhook to receive POST requests from the Telegram API)
> Insert a value in SERVER APP DOMAIN only if you are running the code on a server like Heroku
- SERVER APP DOMAIN (this is the link to the server your app is running on. It can also be a ngrok link if you are running the app locally.)
- TRELLO KEY
- TRELLO TOKEN
- TELEGRAM BOT TOKEN
- TELEGRAM BOT USERNAME
- GCALENDAR ID (this is either id of the calendar, which is found in the "Integrate Calendar" section of the settings of the calendar you want to access)
- G DRIVE EMAIL (The email you want the database to be shared with)
- SPREADSHEET (the Id of the database spreadsheet. This field should be left empty: "", if you don't have a correctly formatted database sheet yet)
- TRELLO_BOARD_ID (This field should be left empty: "", if you don't have a correctly formatted Trello Board yet))
### 6 - Setup virtual enviroment
- Open your comand prompt
- create a python virtual enviroemnt in the folder you have cloned the repository to
- activate the enviroment
- Install the libraries running the code line: 
```
pip install -r requirements.txt
```
### 7a - Running the program on your local machine
The program requires a server connected to the internet to run. To achive that you can either run the program on an online server or you can run the program on your local machine and use ngrok to connect to the internet.
- Install NGROK [https://ngrok.com/download](Download here)
- Unzip the downaloaded folder
- Open your command prompt
- Navigate to the folder where the ngrok.exe is located (Use cd on windows)
- Run the ngrok file with the following command:
```
ngrok http 5000
```
- Copy the https link next to "Forwarding" and paste it as SERVER APP DOMAIN in [secrets/env_variables.json](env_variables.json).
> Make sure that the ngrok link includes the '/' at the end of it - otherwise the program won't work.
### 7b - Running the program on an online server
This part is optional. In case you decide to upload the code on an online server, please undergo the further steps below:
- Add all the enviroment variables (set in step 5) as configuration variables for your server
> Don't add the variables 'TRELLO_BOARD_ID' and 'SPREADSHEET' unless you have both the Trello Board and Spreadsheet database set up correctly. If you don't insert these variables, the program will proceed to create a new board and a new spreadsheet for you. If you insert custom values for these variables without having setup the board/spreadsheet correctly, the program might crash.
- Add your client secret as configuration variable for your server and name it 'CLIENT_SECRET'
> DO NOT UPLOAD YOUR client_secret.json TO AN ONLINE SERVER. Make sure that file is always included in the .gitignore file.
> To add your client secret as config variable, see [fff_automation/setup/clean_json.py](fff_automation/setup/clean_json.py). You'll need to copy the values of your client secret and paste it in the file above following the instructions. Then, run the script locally and it will return the client secret formatted correctly into a string, which you can paste as config variable onto your server.


There you go! Now run the [app.py](app.py) file and check if everything is working fine. If you encounter any errors, feel free to add the procedure you undertook and the error code as an issue in the development branch of the repository, mentioning @davidwickerhf 


