class Group():
    """
    A class reppresenting an instance of a groupchat.
    Attributes:
        chat_id: String, Group chat id
        title: String, title of the group
        admins: List of Strings, list of group admins usernames
        user_id: String, ID of the user who registered the group
        message: Message, message used to register the group
        category: String, Category of the group
        platform: String, platform of the group chat
        region: String, Focused region of the group
        restrictions: String, Restriction of the group
        is_subgroup: String, Either Yes or No
        parentgroup: String, chat id of the parent group
        purpose: String, description of the purpose of the group
        onboarding: String, description of the onboarding procedure for the group
    """

    def __init__(self,
                 id='',
                 card_id='',
                 title='',
                 category='',
                 restriction='',
                 region='',
                 platform='',
                 color='',
                 is_subgroup='',
                 parentgroup='',
                 purpose='',
                 onboarding='',
                 date='',
                 status=0,
                 activator_id='',
                 activator_name='',
                 key='',
                 user_id='',
                 users='',
                 admin_string='',
                 name='',
                 message='',
                 children=[],
                 siblings=[],
                 calls='',
                 card_url='',
                 pgroup_last_index='',
                 edit_argument='',
                 old_group=''
                 ):
        # GROUP ESSENTIAL VARIABLES - SAVED IN DATABASE
        self.key = key
        self.id = id
        self.card_id = card_id
        self.title = title
        self.category = category
        self.restriction = restriction
        self.region = region
        self.platform = platform
        self.color = color
        self.is_subgroup = is_subgroup
        self.parentgroup = parentgroup
        self.purpose = purpose
        self.onboarding = onboarding
        self.date = date
        self.status = status
        self.activator_id = activator_id
        self.activator_name = activator_name
        # CONVERSATION UTILS VARIABLES - DISCARDED
        self.admin_string = admin_string
        self.children = children
        self.siblings = siblings
        self.calls = calls
        self.users = users

    def get_color(self):
        colors = {
            1: 'Lavender',
            2: 'Sage',
            3: 'Grape',
            4: 'Flamingo',
            5: 'Banana',
            6: 'Tangerine',
            7: 'Peacock',
            8: 'Graphite',
            9: 'Blueberry',
            10: 'Basil'
        }
        color_str = colors.get(self.color)
        return color_str

    def __repr__(self):
        return '<Group({}, {}, {}, {})>'.format(self.id, self.title, self.activator_id, self.parentgroup)
