from fff_automation.bots.telebot import *


######################## GROUP CONVERSATION FUNCTIONS #######################
@run_async
def save_group(update, context):
    print("BOT: --- SAVE GROUP INFO ---")
    # GET GROUP INFORMATION
    chat = update.message.chat
    title = chat.title
    chat_id = chat.id
    user_id = update.message.from_user.id
    if chat_id == user_id:
        print("Chat is user")
        update.message.chat.send_message(
            text="This command can be run only in group chats")
        return ConversationHandler.END
    elif (database.get(chat_id)[0] == None):
        # GET ALL USERS
        users = chat.get_administrators()
        # SAVE GROUP INSTANCE IN PICKLE
        group = Group(
            id=chat_id,
            title=title,
            users=users,
            platform="Telegram",
            activator_id=user_id,
            activator_name=update.effective_user.name,
            user_id=user_id,
            message=update.message
        )

        # CREATE MARKUP FOR CATEOGORY CHOICE:
        markup = create_menu(
            [interface.trelloc.WORKING_GROUP, interface.trelloc.DISCUSSION_GROUP, interface.trelloc.PROJECT], [interface.trelloc.WORKING_GROUP, interface.trelloc.DISCUSSION_GROUP, interface.trelloc.PROJECT])

        # SEND MESSAGE WITH INTRO AND REQUEST OF CATEGORY
        group.message = chat.send_message(
            text=save_group_message, parse_mode=ParseMode.HTML, reply_markup=markup)
        utils.dump_pkl('newgroup', group)
        return CATEGORY
    else:
        print("Group is already registered")
        chat.send_message(
            text=save_group_alreadyregistered_message, parse_mode=ParseMode.HTML)
        return ConversationHandler.END


@run_async
def category(update, context):
    print("BOT: --- CATEGORY ---")
    query = update.callback_query
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id
    print("TELEBOT: CATEGORY: Chat Instance: ", chat_id)
    query.answer()

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return CATEGORY

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.activator_id:
        return CATEGORY
    else:
        group.category = query.data

    # SET NEW TEXT AND MARKAP FOR LEVEL REQUEST
    text = "Ok, cool!\nNow please select the <b>region</b> this group concerns: "
    markup = create_menu(["Africa", "Asia", "North America", "South America", "Oceania", "Europe", "Global"], [
        interface.trelloc.regions['Africa'],
        interface.trelloc.regions['Asia'],
        interface.trelloc.regions['North America'],
        interface.trelloc.regions['South America'],
        interface.trelloc.regions['Oceania'],
        interface.trelloc.regions['Europe'],
        interface.trelloc.regions['Global']], 2)
    print("BOT - CATEGORY: Created Region Markup")
    # EDIT MESSAGE TEXT AND MARKUP -  REQUEST REGION
    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    query.edit_message_reply_markup(markup)
    group.message = query.message
    utils.dump_pkl('newgroup', group)
    return REGION


@run_async
def region(update, context):
    print("BOT: --- REGION ---")
    query = update.callback_query
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id
    query.answer()

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return REGION

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.activator_id:
        return REGION
    else:
        group.region = utils.getKeysByValue(
            interface.trelloc.regions, query.data)[0]

    # SET NEW TEXT AND MARKAP FOR RESTRICTION REQUEST
    text = "Cool! Next, please select the <b>access level</b> for this this group: \n\n<b>Open</b> - Any fff activist working on the international level is allowed to enter\n\n<b>Restricted</b> - Some level of restriction (example: n. activists per country/region\n\n<b>Closed</b> - The group is closed"

    markup = create_menu(["Open", "Restricted", "Closed"],
                         [interface.trelloc.restrictions['Open'],
                          interface.trelloc.restrictions['Restricted'],
                          interface.trelloc.restrictions['Closed']])
    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    query.edit_message_reply_markup(markup)
    group.message = query.message
    utils.dump_pkl('newgroup', group)
    return RESTRICTION


@run_async
def restriction(update, context):
    print("BOT: --- RESTRICTION ---")
    query = update.callback_query
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id
    query.answer()

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return RESTRICTION

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.activator_id:
        return RESTRICTION
    else:
        group.restriction = utils.getKeysByValue(
            interface.trelloc.restrictions, query.data)[0]

    # SET NEW TEXT AND MARKAP FOR IS SUBGOUP REQUEST
    text = "Awesome. Is this chat a sub-group of any working/discussion group in fridays for future? Answer by clicking the buttons below:"
    markup = create_menu(["No", "Yes"], [0, 1], cols=2)
    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    query.edit_message_reply_markup(markup)
    group.message = query.message
    utils.dump_pkl('newgroup', group)
    return IS_SUBGROUP


@run_async
def is_subgroup(update, context):
    print("BOT: --- IS SUBGROUP ---")
    query = update.callback_query
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id
    query.answer()

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return IS_SUBGROUP

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.activator_id:
        return IS_SUBGROUP

    print("BOT - IS SUBGROUP: Query:", query.data, " type: ", type(query.data))
    if query.data == str(1):
        print("BOT: Select parents")
        group.is_subgroup = True

        # SET NEW TEXT AND MARKAP FOR PARENT REQUEST
        if database.get()[0] != None:
            print("BOT: Groups found")
            text = "Alright, select below the parent group of this group chat:"
            markup = subgroup_menu(
                group=group, direction=1)
            query.edit_message_text(text)
            query.edit_message_reply_markup(markup)
            group.message = query.message
            utils.dump_pkl('newgroup', group)
            return PARENT_GROUP
        else:
            print("BOT: No groups available for parents")
            text = "Mmh... It seams no other group has been registerred yet... To add a parent to a group, make sure you register that group chat first!"
            group.is_subgroup = False
            markup = create_menu(["Next"], [0])
            query.edit_message_text(text, parse_mode=ParseMode.HTML)
            query.edit_message_reply_markup(markup)
            group.message = query.message
            utils.dump_pkl('newgroup', group)
            return IS_SUBGROUP
    elif query.data == str(0):
        print("BOT: No parents")
        group.is_subgroup = False

        # SET NEW TEXT AND MARKAP FOR PURPOSE REQUEST
        text = "Alright, last two steps! Please reply to this message with a short description of the purpose and mandate of the group.\nYou can skip this step by clicking the button below."
        markup = create_menu(["Skip"], ["skip"])
        query.edit_message_text(text, parse_mode=ParseMode.HTML)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('newgroup', group)
        return PURPOSE


@run_async
def parent_group(update, context):
    print("BOT: --- PARENT GROUP ---")
    query = update.callback_query
    user_id = update.callback_query.from_user.id
    chat_id = update.effective_chat.id
    query.answer()

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return PARENT_GROUP

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.activator_id:
        return PARENT_GROUP

    if query.data == 'no_parent':
        group.is_subgroup = False
        # SET NEW TEXT AND MARKAP FOR PURPOSE REQUEST
        text = "Alright, last two steps! Please reply to this message with a short description of the purpose and mandate of the group.\nYou can skip this step by clicking the button below."
        markup = create_menu(["Skip"], ["skip"])
        query.edit_message_text(text, parse_mode=ParseMode.HTML)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('newgroup', group)
        return PURPOSE
    elif int(query.data) in (0, 1):
        markup = subgroup_menu(
            group=group, direction=query.data)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('newgroup', group)
        return PARENT_GROUP
    else:
        print("TELEBOT: parent_group(): Query Data: ", query.data)
        group.parentgroup = query.data

        # SET NEW TEXT AND MARKAP FOR PURPOSE REQUEST
        text = "Great! Last two steps! Please reply to this message with a short description of the purpose and mandate of the group.\nYou can skip this step by clicking the button below."
        markup = create_menu(["Skip"], ["skip"])
        query.edit_message_text(text, parse_mode=ParseMode.HTML)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('newgroup', group)
        return PURPOSE


@run_async
def purpose(update, context):
    print("BOT: --- PURPOSE ---")
    try:
        # UPDATE IS MESSAGE
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
    except:
        # UPDATE IS QUERY
        user_id = update.callback_query.from_user.id
        chat_id = update.effective_chat.id

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return PURPOSE
    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    if user_id != group.activator_id:
        return PURPOSE

    try:
        query = update.callback_query
        query.answer()
        text = "Alright, we'll skip that. Last question:\nPlease reply to this message with a description of who is allowed access to this group and how can activists join this group. You can skip this step as well with the button below."
        markup = create_menu(["Skip"], ["skip"])
        query.edit_message_text(text, parse_mode=ParseMode.HTML)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('newgroup', group)
        return ONBOARDING
    except:
        print("BOT: User sent messages")
        group.purpose = update.message.text
        # SET NEW TEXT AND MARKAP FOR PURPOSE REQUEST
        text = "Great! Last step!\nPlease reply to this message with a description of who is allowed access to this group and how can activists join this group. You can skip this step as well with the button below."
        markup = create_menu(["Skip"], ["skip"])
        group.message.edit_text(
            text=text, parse_mode=ParseMode.HTML, reply_markup=markup)
        utils.dump_pkl('newgroup', group)
        return ONBOARDING


@run_async
@send_typing_action
def onboarding(update, context):
    print("BOT: --- ONBOARDING ---")
    try:
        # UPDATE IS MESSAGE
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
    except:
        # UPDATE IS QUERY
        user_id = update.callback_query.from_user.id
        chat_id = update.effective_chat.id

    if utils.load_pkl('newgroup', chat_id, user_id) == "":
        print("TELEBOT: ERROR - Persistence file not found")
        return REGION

    # LOAD PERSISTENCE FILE
    group = utils.load_pkl('newgroup', chat_id, user_id)
    print('TELEBOT: onboarding(): Is Subgroup: ',
          group.is_subgroup, ' ', type(group.is_subgroup))
    if user_id != group.activator_id:
        return REGION

    try:
        group.onboarding = update.message.text
        group.message.delete()
        group.message = update.message.reply_text(
            'Alright, this group is being registered... this might take a minute...')
        save_group_info(update.message.chat, group)
        group.message.delete()
        return ConversationHandler.END
    except:
        query = update.callback_query
        query.answer()
        query.edit_message_text(
            'Alright, this group is being registered... this might take a minute...')
        save_group_info(group.message.chat, group)
        query.message.delete()
        return ConversationHandler.END


def save_group_info(chat, group):
    # GROUP SAVING: Chat id, Title, Admins, Category, Region, Restrictions, is_subgroup,  parentgroup, purpose, onboarding
    print("SAVE GROUP INFO -----------------------------")
    group.date = datetime.utcnow()
    card_url = interface.save_group(group)
    if card_url == -1:
        chat.send_message(
            text="There was a problem in adding the call to the database.\nPlease contact @davidwickerhf for technical support.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton("Trello Card", url=str(
        card_url)), InlineKeyboardButton("Edit Info", callback_data='edit_group')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print("BOT - Save Group Info: Made Kayboard")

    info_text = format_group_info(group)
    utils.delete_pkl('newgroup', group.id, group.activator_id)
    chat.send_message(
        text=info_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    print("BOT - Save Group Info: Sent Reply")
