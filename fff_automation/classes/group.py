class Group():
    """
    A class reppresenting an instance of a groupchat.
    Attributes:
        chat_id: String, Group chat id
        title: String, title of the group
        admins: List of Strings, list of group admins usernames
        category: String, Category of the group
        platform: String, platform of the group chat
        region: String, Focused region of the group
        restrictions: String, Restriction of the group
        is_subgroup: String, Either Yes or No
        parentgroup: String, chat id of the parent group
        purpose: String, description of the purpose of the group
        onboarding: String, description of the onboarding procedure for the group
        user_id: String, ID of the user who registered the group
        message: Message, message used to register the group
    """

    def __init__(self, chat_id, title, admins, category, platform, region, restrictions, is_subgroup, parentgroup, purpose, onboarding, user_id, message):
        self.chat_id = chat_id
        self.title = title
        self.admins = admins
        self.category = category
        self.platform = platform
        self.region = region
        self.restrictions = restrictions
        self.is_subgroup = is_subgroup
        self.parentgroup = parentgroup
        self.purpose = purpose
        self.onboarding = onboarding
        self.user_id
        self.message
