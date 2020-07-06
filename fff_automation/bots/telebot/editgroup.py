from fff_automation.bots.telebot import *


####################### EDIT GROUP FUNCTIONS #################################
@run_async
def edit_group(update, context):
    print('TELEBOT: edit_group()')
    chat_id = update.effective_chat.id
    group = database.get(chat_id)[0]
    botupdate = BotUpdate(obj=group, update=update, user=update.effective_user)
    

    if group == None:
        if update.callback_query != None:
            update.callback_query.edit_message_text(no_permission_edit_group, parse_mode=ParseMode.HTML)
        else:
            update.effective_chat.send_message(no_permission_edit_group, parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    group.children = database.get(group.id, field='parent_group')
    botupdate.card_url = 'https://trello.com/c/{}'.format(group.card_id)

    # Send Argument Menu
    markup = create_menu([
        'Category',
        'Restriction',
        'Region',
        'Color',
        'Purpose',
        'Onboarding',
        'Parent Group',
        'Cancel'
    ], [
        CATEGORY,
        RESTRICTION,
        REGION,
        COLOR,
        PURPOSE,
        ONBOARDING,
        PARENT_GROUP,
        'cancel_edit_group'
    ], 2)

    if update.callback_query:
        update.callback_query.edit_message_text(
            'Select below what you wish to edit:', reply_markup=markup)
        botupdate.message = update.callback_query.message
    else:
        botupdate.message = update.message.reply_text(
            'Select below what you wish to edit:', reply_markup=markup)

    utils.dump_pkl('edit_group', botupdate)
    return ARGUMENT


@run_async
def edit_group_argument(update, context):
    print('TELEBOT: edit_group_argument()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    query = update.callback_query

    # CANCEL is pressed
    if query.data == 'cancel_edit_group':
        cancel_edit_group(update, context)
        return ConversationHandler.END

    # RETRIEVE GROUP INFO
    botupdate = utils.load_pkl('edit_group', chat_id, user_id)
    if botupdate == None:
        return ARGUMENT
    group = botupdate.obj
    botupdate.edit_argument = int(query.data)

    # HANDLE INPUT MARKUP
    markup = None
    if botupdate.edit_argument == CATEGORY:
        print('TELEBOT: edit_group_argument(): Create Category Markup')
        markup = create_menu(
            [interface.trelloc.WORKING_GROUP, interface.trelloc.DISCUSSION_GROUP, interface.trelloc.PROJECT, 'Cancel'], [
                interface.trelloc.WORKING_GROUP, interface.trelloc.DISCUSSION_GROUP, interface.trelloc.PROJECT, 'cancel_edit_group'])
        text = edit_category_text
    elif botupdate.edit_argument == RESTRICTION:
        print('TELEBOT: edit_group_argument(): Create Restriction Markup')
        markup = create_menu(["Open", "Restricted", "Closed", 'Cancel'],
                             [interface.trelloc.restrictions['Open'],
                              interface.trelloc.restrictions['Restricted'],
                              interface.trelloc.restrictions['Closed']])
        text = edit_restriction_text
    elif botupdate.edit_argument == REGION:
        print('TELEBOT: edit_group_argument(): Create Region Markup')
        markup = create_menu(["Africa", "Asia", "North America", "South America", "Oceania", "Europe", "Global", 'Cancel'], [
            interface.trelloc.regions['Africa'],
            interface.trelloc.regions['Asia'],
            interface.trelloc.regions['North America'],
            interface.trelloc.regions['South America'],
            interface.trelloc.regions['Oceania'],
            interface.trelloc.regions['Europe'],
            interface.trelloc.regions['Global'],
            'cancel_edit_group'], 2)
        text = edit_region_text
    elif botupdate.edit_argument == COLOR:
        print('TELEBOT: edit_group_argument(): Create Color Markup')
        markup = create_menu([
            interface.gcalendar.colors.get(1),
            interface.gcalendar.colors.get(2),
            interface.gcalendar.colors.get(3),
            interface.gcalendar.colors.get(4),
            interface.gcalendar.colors.get(5),
            interface.gcalendar.colors.get(6),
            interface.gcalendar.colors.get(7),
            interface.gcalendar.colors.get(8),
            interface.gcalendar.colors.get(9),
            interface.gcalendar.colors.get(10),
            'Cancel'
        ], [
            interface.gcalendar.LAVENDER,
            interface.gcalendar.SAGE,
            interface.gcalendar.GRAPE,
            interface.gcalendar.FLAMINGO,
            interface.gcalendar.BANANA,
            interface.gcalendar.TANGERINE,
            interface.gcalendar.PEACOCK,
            interface.gcalendar.GRAPHITE,
            interface.gcalendar.BLUEBERRY,
            interface.gcalendar.BASIL,
            'cancel_edit_group'

        ], cols=2)
        text = edit_color_text
    elif botupdate.edit_argument == PURPOSE:
        print('TELEBOT: edit_group_argument(): Create Purpose Markup')
        markup = create_menu(['Cancel'], ['cancel_edit_group'])
        text = edit_purpose_text
    elif botupdate.edit_argument == ONBOARDING:
        print('TELEBOT: edit_group_argument(): Create Onboarding Markup')
        text = edit_onboarding_text
        markup = create_menu(['Cancel'], ['cancel_edit_group'])
    elif botupdate.edit_argument == PARENT_GROUP:
        print('TELEBOT: edit_group_argument(): Create Parent Markup')
        markup = create_menu(['Yes', 'No', 'Cancel'], [
                             0, 1, 'cancel_edit_group'], cols=2)
        query.edit_message_text(edit_is_subgroup_text,
                                parse_mode=ParseMode.HTML, reply_markup=markup)
        group.message = query.message
        utils.dump_pkl('edit_group', botupdate)
        return EDIT_IS_SUBGROUP

    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    try:
        query.edit_message_reply_markup(markup)
    except:
        print('TELEBOT: No Markup')
    botupdate.message = query.message
    utils.dump_pkl('edit_group', botupdate)
    return INPUT_ARGUMENT


@run_async
def edit_is_subgroup(update, context):
    print('TELEBOT: edit_is_subgroup()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    botupdate = utils.load_pkl('edit_group', chat_id, user_id)

    if botupdate == None:
        return EDIT_IS_SUBGROUP
    group = botupdate.obj
    query = update.callback_query
    if query.data == 'cancel_edit_group':
        cancel_edit_group(update, context)
        return ConversationHandler.END
    elif int(query.data) == 0:
        groups = database.get()
        print(
            'TELEBOT: edit_is_subgroup(): Group has parent | Database list: ', len(groups))
        if len(groups) <= 1:
            # No Parents available, error message, cancel edit operation
            text = format_group_info(botupdate, 2, no_parents_edit_parent)
            keyboard = [[InlineKeyboardButton("Trello Card", url=str(
            botupdate.card_url)), InlineKeyboardButton("Edit Info", callback_data='edit_group')]]
            markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(text, parse_mode=ParseMode.HTML)
            query.edit_message_reply_markup(markup)
            utils.delete_pkl('edit_group', chat_id, user_id)
            return ConversationHandler.END

        group.is_subgroup = True
        markup = subgroup_menu(botupdate, RIGHT, method='edit_group')
        query.edit_message_text(edit_parent_text)
        query.edit_message_reply_markup(markup)
        botupdate.message = query.message
        utils.dump_pkl('edit_group', botupdate)
        return EDIT_PARENT
    elif int(query.data) == 1:
        print('TELEBOT: edit_is_subgroup(): Group does not have parent')
        group.message.edit_text(editing_group_text)
        group.is_subgroup = False
        group.parentgroup = ''
        # Save group into database and delete persistence file
        group = interface.edit_group(botupdate)
        utils.delete_pkl('edit_group', chat_id, user_id)

        # Send confirmation message
        # Markup
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(
            'Trello Card', url=group.card_url), InlineKeyboardButton('Edit Info', callback_data='edit_group')]])
        botupdate.message.delete()
        text = format_group_info(botupdate, type=1)
        update.effective_chat.send_message(
            text, reply_markup=markup, parse_mode=ParseMode.HTML)
        # End Conversation
        return ConversationHandler.END


@run_async
def edit_parent(update, context):
    print('TELEBOT: edit_parent()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    botupdate = utils.load_pkl('edit_group', chat_id, user_id)

    if botupdate == None:
        return EDIT_PARENT
    group = botupdate.obj
    query = update.callback_query
    if query.data == 'cancel':
        # Cancel Edit Group
        cancel_edit_group(update, context)
        return ConversationHandler.END
    elif int(query.data) in (LEFT, RIGHT):
        markup = subgroup_menu(
            botupdate=botupdate, direction=query.data, method='edit_group')
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('edit_group', group)
        return EDIT_PARENT

    botupdate.message.edit_text(editing_group_text)
    group.parentgroup = int(query.data)
    # Save group into database and delete persistence file
    group = interface.edit_group(botupdate)
    utils.delete_pkl('edit_group', chat_id, user_id)

    # Send confirmation message
    # Markup
    markup = InlineKeyboardMarkup([[InlineKeyboardButton(
        'Trello Card', url=group.card_url), InlineKeyboardButton('Edit Info', callback_data='edit_group')]])
    botupdate.message.delete()
    text = format_group_info(botupdate, type=1)
    update.effective_chat.send_message(
        text, reply_markup=markup, parse_mode=ParseMode.HTML)
    # End Conversation
    return ConversationHandler.END


@run_async
@send_typing_action
def input_edit_group_argument(update, context):
    print('TELEBOT: input_edit_group_argument()')
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    botupdate = utils.load_pkl('edit_group', chat_id, user_id)

    if botupdate == None:
        return INPUT_ARGUMENT
    group = botupdate.obj
    query = update.callback_query
    try:
        if query.data == 'cancel_edit_group':
            cancel_edit_group(update, context)
            return ConversationHandler.END
    except:
        print('TELEBOT: Not Cancel')
    botupdate.message.edit_text(editing_group_text)

    if botupdate.edit_argument == CATEGORY:
        print('TELEBOT: input_edit_group_argument(): Category')
        group.category = query.data
    elif botupdate.edit_argument == RESTRICTION:
        print('TELEBOT: input_edit_group_argument(): Restriction')
        group.restriction = utils.getKeysByValue(
            interface.trelloc.restrictions, query.data)[0]
    elif botupdate.edit_argument == REGION:
        print('TELEBOT: input_edit_group_argument(): Region')
        group.region = utils.getKeysByValue(
            interface.trelloc.regions, query.data)[0]
    elif botupdate.edit_argument == COLOR:
        print('TELEBOT: input_edit_group_argument(): Color')
        group.color = query.data
    elif botupdate.edit_argument == PURPOSE:
        print('TELEBOT: input_edit_group_argument(): Purpose')
        group.purpose = update.message.text
    elif botupdate.edit_argument == ONBOARDING:
        print('TELEBOT: input_edit_group_argument(): Onboarding')
        group.onboarding = update.message.text
    elif botupdate.edit_argument == PARENT_GROUP:
        print('TELEBOT: input_edit_group_argument(): Parent group')
        group.parentgroup = query.data

    # Save group into database and delete persistence file
    group = interface.edit_group(botupdate)
    utils.delete_pkl('edit_group', chat_id, user_id)

    # Send confirmation message
    # Markup
    text = format_group_info(botupdate, type=1)
    print('TELEBOT: group card url: ', botupdate.card_url)
    keyboard = [[InlineKeyboardButton("Trello Card", url=str(
        group.card_url)), InlineKeyboardButton("Edit Info", callback_data='edit_group')]]
    markup = InlineKeyboardMarkup(keyboard)
    botupdate.message.delete()
    update.effective_chat.send_message(
        text, reply_markup=markup, parse_mode=ParseMode.HTML)
    # End Conversation
    return ConversationHandler.END

@run_async
@send_typing_action
def cancel_edit_group(update, context):
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.callback_query.from_user.id
    botupdate = utils.load_pkl('edit_group', chat_id, user_id)
    update.callback_query.answer()
    if botupdate == None:
        return
    else:
        print("CANCEL PRESSED")
        text = format_group_info(botupdate, type=2, error_text=cancel_edit_group_text)
        markup = format_group_buttons(botupdate.obj)
        botupdate.message.edit_text(
            text=text, parse_mode=ParseMode.HTML, reply_markup=markup)
        utils.delete_pkl('edit_group', chat_id, user_id)
    return ConversationHandler.END

