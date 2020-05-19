class Call():
    def __init__(self, chat_id, user_id, message_id, username, message, title="", date="", time="", duration=3600, description="", agenda_link="", link="", missing_arguments=[]):
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
        self.TITLE, self.DATE, self.TIME, self.DURATION, self.DESCRIPTION, self.AGENDALINK, self.LINK = range(
            7)
        self.order = {self.TITLE: "Title", self.DATE: "Date", self.TIME: "Time",
                      self.DURATION: "Duration", self.DESCRIPTION: "Description", self.AGENDALINK: "Agenda Link", self.LINK: "Link"}
