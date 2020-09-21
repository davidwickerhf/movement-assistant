class Organisation(object):
    def __init__(self, activator_id):
        self.key = self.generate_key()
        self.activator_id = activator_id
        self.name = None 
        self.description = None

    def get_key(self):
        return self.key

    def get_activator_id(self):
        return self.activator_id

    def get_name(self):
        return self.name

    def get_description(self):
        return self.description

    def set_name(self, name):
        """
        Sets a new name for this Organisation object
        :param name: New name for the organisation
        :ptype: str
        """
        self.name = name

    def set_description(self, description):
        """
        Sets a new description for this Organisation object
        :param description: New description for the organisation
        :ptype: str
        """
        self.description = description
