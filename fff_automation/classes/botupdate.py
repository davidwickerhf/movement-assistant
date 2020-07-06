class BotUpdate():
    def __init__(self, update, user, obj=None, message=None, card_url='', pobj_last_index=1, edit_argument='', old_obj=None, key='', obj_selection='', selected=''):
        self.update = update
        self.user = user
        self.obj = obj
        self.message = message
        self.card_url = card_url
        # Rotate Groups
        self.pobj_last_index = pobj_last_index
        # Edit Obj Arguments
        self.edit_argument = edit_argument
        self.old_obj = old_obj
        # Obj List Arguments
        self.obj_selection = obj_selection
        self.selected = selected

    def get_card_url(self):
        try: self.card_url = 'https://trello.com/c/{}'.format(self.obj.card_id)
        except: return None
        return self.card_url

