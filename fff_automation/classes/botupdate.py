class BotUpdate():
    def __init__(self, obj, update, user, message=None, card_url='', pobj_last_index=1, edit_argument='', old_obj='', key=''):
        self.obj = obj
        self.update = update
        self.user = user
        self.message = message
        self.card_url = card_url
        self.pobj_last_index = pobj_last_index
        self.edit_argument = edit_argument
        self.old_obj = old_obj
