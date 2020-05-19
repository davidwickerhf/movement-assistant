from ..fff_automation.modules import settings
import sys
import os
import requests
from trello import TrelloClient
import json


def delete_boards():
    TRELLO_KEY = settings.get_var('TRELLO_KEY')
    print("TRELLOC: Trello Key: ", TRELLO_KEY)
    TRELLO_TOKEN = settings.get_var('TRELLO_TOKEN')
    print("TRELLOC: Trello Token: ", TRELLO_TOKEN)

    client = TrelloClient(
        api_key=TRELLO_KEY,
        token=TRELLO_TOKEN,
    )

    boards = client.list_boards()
    for board in boards:
        url = "https://api.trello.com/1/boards/{}?key={}&token={}".format(
            board.id, TRELLO_KEY, TRELLO_TOKEN)

        response = requests.request(
            "DELETE",
            url
        )
        print(response)


delete_boards()
