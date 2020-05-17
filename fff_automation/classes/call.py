class Call():
    def __init__(self, chat_id, user_id, message_id, username, message, title="", date="", time="", duration=3600, description="", agenda_link="", link=""):
        self.chat_id = chat_id
        self.user_id = user_id
        self.message_id = message_id
        self.username = username
        self.message = message
        self.title = title
        self.date = date
        self.time = time
        self.duration = duration
        self.description = description
        self.agenda_link = agenda_link
        self.link = link

