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

    def __init__(self, chat_id, title, admins, platform, user_id, message, category="", region="", restriction="", is_subgroup="", parentgroup="", purpose="", onboarding="", pgroup_last_index=1):
        self.chat_id = chat_id
        self.title = title
        self.admins = admins
        self.platform = platform
        self.user_id = user_id
        self.message = message
        self.category = category
        self.region = region
        self.restriction = restriction
        self.is_subgroup = is_subgroup
        self.parentgroup = parentgroup
        self.purpose = purpose
        self.onboarding = onboarding
        self.pgroup_last_index = pgroup_last_index

    def print_arguments(self):
        print("GROUP: Chat Id", self.chat_id)
        print("GROUP: Title", self.title)
        print("GROUP: admins", self.admins)
        print("GROUP: platform", self.platform)
        print("GROUP: user Id", self.user_id)
        print("GROUP: message", self.message)
        print("GROUP: category", self.category)
        print("GROUP: regiom", self.region)
        print("GROUP: restriction", self.restriction)
        print("GROUP: is_subgroup", self.is_subgroup)
        print("GROUP: parentgroup", self.parentgroup)
        print("GROUP: purpose", self.purpose)
        print("GROUP: onboarding", self.onboarding)
        print("GROUP: pgroup_last_index", self.pgroup_last_index)
