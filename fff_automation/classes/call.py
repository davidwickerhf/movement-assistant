class Call():
    def __init__(self,
                 id='',
                 chat_id='',
                 card_id='',
                 title='',
                 date='',
                 time='',
                 duration=3600,
                 description='',
                 agenda_link='',
                 calendar_url='',
                 link='',
                 user_id='',
                 status=0,
                 message='',
                 message_id='',
                 username=''):
        self.id = id
        self.chat_id = chat_id
        self.card_id = card_id
        self.title = title
        self.date = date
        self.time = time
        self.duration = duration
        self.description = description
        self.agenda_link = agenda_link
        self.calendar_url = calendar_url
        self.link = link
        self.user_id = user_id
        self.status = status

        self.message = message
        self.message_id = message_id
        self.username = username
        self.TITLE, self.DATE, self.TIME, self.DURATION, self.DESCRIPTION, self.AGENDALINK, self.LINK = range(
            7)
        self.order = {self.TITLE: "Title", self.DATE: "Date", self.TIME: "Time",
                      self.DURATION: "Duration", self.DESCRIPTION: "Description", self.AGENDALINK: "Agenda Link", self.LINK: "Link"}
