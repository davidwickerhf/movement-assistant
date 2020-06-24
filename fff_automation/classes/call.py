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
                 activator_id='',
                 status=0,
                 key='',
                 message='',
                 message_id='',
                 user_id='',
                 name='',
                 duration_string='',
                 card_url=''):
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
        self.activator_id = activator_id
        self.status = status

        self.key = key
        self.message = message
        self.message_id = message_id
        self.user_id = user_id
        self.name = name
        self.duration_string = duration_string
        self.card_url = card_url
        self.TITLE, self.DATE, self.TIME, self.DURATION, self.DESCRIPTION, self.AGENDALINK, self.LINK = range(
            7)
        self.order = {self.TITLE: "Title", self.DATE: "Date", self.TIME: "Time",
                      self.DURATION: "Duration", self.DESCRIPTION: "Description", self.AGENDALINK: "Agenda Link", self.LINK: "Link"}
