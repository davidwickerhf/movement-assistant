class Feedback():
    def __init__(self,
                 user_id,
                 chat_id,
                 date,
                 title='',
                 body='',
                 type=None,
                 issue_type=None,
                 labels=[],
                 state=None,
                 url='',
                 json='',
                 id='',
                 message=None
                 ):
        self.user_id = user_id
        self.chat_id = chat_id
        self.date = date
        self.title = title
        self.body = body
        self.type = type
        self.issue_type = issue_type
        self.labels = labels
        self.state = state
        self.url = url
        self.id = id

    def get_type(self):
        return self.type

    def get_issue_type(self):
        return self.issue_type
