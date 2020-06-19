from fff_automation.bots.telebot import *


####################### EDIT GROUP FUNCTIONS #################################
@run_async
def edit_group(update, context):
    print('TELEBOT: edit_group()')
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    group = database.get(chat_id)[0]

    if group == None:
        update.effective_chat.send_message(
            no_permission_edit_group, parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    group.user_id = user_id
    group.children = database.get(group.id, field='parent_group')

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
        group.message = update.callback_query.message
    else:
        group.message = update.message.reply_text(
            'Select below what you wish to edit:', reply_markup=markup)

    utils.dump_pkl('edit_group', group)
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
    group = utils.load_pkl('edit_group', chat_id, user_id)
    if group == '' or user_id != group.user_id:
        return ARGUMENT
    group.edit_argument = int(query.data)

    # HANDLE INPUT MARKUP
    markup = None
    if group.edit_argument == CATEGORY:
        print('TELEBOT: edit_group_argument(): Create Category Markup')
        markup = create_menu(
            [interface.trelloc.WORKING_GROUP, interface.trelloc.DISCUSSION_GROUP, interface.trelloc.PROJECT, 'Cancel'], [
                interface.trelloc.WORKING_GROUP, interface.trelloc.DISCUSSION_GROUP, interface.trelloc.PROJECT, 'cancel_edit_group'])
        text = edit_category_text
    elif group.edit_argument == RESTRICTION:
        print('TELEBOT: edit_group_argument(): Create Restriction Markup')
        markup = create_menu(["Open", "Restricted", "Closed", 'Cancel'],
                             [interface.trelloc.restrictions['Open'],
                              interface.trelloc.restrictions['Restricted'],
                              interface.trelloc.restrictions['Closed']])
        text = edit_restriction_text
    elif group.edit_argument == REGION:
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
    elif group.edit_argument == COLOR:
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
    elif group.edit_argument == PURPOSE:
        print('TELEBOT: edit_group_argument(): Create Purpose Markup')
        markup = create_menu(['Cancel'], ['cancel_edit_group'])
        text = edit_purpose_text
    elif group.edit_argument == ONBOARDING:
        print('TELEBOT: edit_group_argument(): Create Onboarding Markup')
        text = edit_onboarding_text
        markup = create_menu(['Cancel'], ['cancel_edit_group'])
    elif group.edit_argument == PARENT_GROUP:
        print('TELEBOT: edit_group_argument(): Create Parent Markup')
        markup = create_menu(['Yes', 'No', 'Cancel'], [
                             0, 1, 'cancel_edit_group'], cols=2)
        query.edit_message_text(edit_is_subgroup_text,
                                parse_mode=ParseMode.HTML, reply_markup=markup)
        group.message = query.message
        utils.dump_pkl('edit_group', group)
        return EDIT_IS_SUBGROUP

    query.edit_message_text(text, parse_mode=ParseMode.HTML)
    try:
        query.edit_message_reply_markup(markup)
    except:
        print('TELEBOT: No Markup')
    group.message = query.message
    utils.dump_pkl('edit_group', group)
    return INPUT_ARGUMENT


@run_async
def edit_is_subgroup(update, context):
    print('TELEBOT: edit_is_subgroup()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    group = utils.load_pkl('edit_group', chat_id, user_id)

    if group == '' or group.user_id != user_id:
        return EDIT_IS_SUBGROUP

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
            query.edit_message_text(no_parents_edit_parent)
            utils.delete_pkl('edit_group', chat_id, user_id)
            return ConversationHandler.END

        group.is_subgroup = True
        markup = subgroup_menu(group, 1, method='edit_group')
        query.edit_message_text(edit_parent_text)
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('edit_group', group)
        return EDIT_PARENT
    elif int(query.data) == 1:
        print('TELEBOT: edit_is_subgroup(): Group does not have parent')
        group.message.edit_text(editing_group_text)
        group.is_subgroup = False
        group.parentgroup = ''
        # Save group into database and delete persistence file
        group = interface.edit_group(group)
        utils.delete_pkl('edit_group', chat_id, user_id)

        # Send confirmation message
        # Markup
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(
            'Trello Card', url=group.card_url), InlineKeyboardButton('Edit Info', callback_data='edit_group')]])
        group.message.delete()
        text = format_group_info(group, type=1)
        update.effective_chat.send_message(
            text, reply_markup=markup, parse_mode=ParseMode.HTML)
        # End Conversation
        return ConversationHandler.END


@run_async
def edit_parent(update, context):
    print('TELEBOT: edit_parent()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    group = utils.load_pkl('edit_group', chat_id, user_id)

    if group == '' or group.user_id != user_id:
        return EDIT_PARENT

    query = update.callback_query
    if query.data == 'cancel':
        # Cancel Edit Group
        cancel_edit_group(update, context)
        return ConversationHandler.END
    elif query.data in (0, 1):
        markup = subgroup_menu(
            group=group, direction=query.data, method='edit_group')
        query.edit_message_reply_markup(markup)
        group.message = query.message
        utils.dump_pkl('edit_group', group)
        return EDIT_PARENT

    group.message.edit_text(editing_group_text)
    group.parentgroup = query.data
    # Save group into database and delete persistence file
    group = interface.edit_group(group)
    utils.delete_pkl('edit_group', chat_id, user_id)

    # Send confirmation message
    # Markup
    markup = InlineKeyboardMarkup([[InlineKeyboardButton(
        'Trello Card', url=group.card_url), InlineKeyboardButton('Edit Info', callback_data='edit_group')]])
    group.message.delete()
    text = format_group_info(group, type=1)
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
    group = utils.load_pkl('edit_group', chat_id, user_id)

    if group == '' or group.user_id != user_id:
        return INPUT_ARGUMENT

    query = update.callback_query
    try:
        if query.data == 'cancel_edit_group':
            cancel_edit_group(update, context)
    except:
        print('TELEBOT: Not Cancel')
    group.message.edit_text(editing_group_text)

    if group.edit_argument == CATEGORY:
        print('TELEBOT: input_edit_group_argument(): Category')
        group.category = query.data
    elif group.edit_argument == RESTRICTION:
        print('TELEBOT: input_edit_group_argument(): Restriction')
        group.restriction = utils.getKeysByValue(
            interface.trelloc.restrictions, query.data)[0]
    elif group.edit_argument == REGION:
        print('TELEBOT: input_edit_group_argument(): Region')
        group.region = utils.getKeysByValue(
            interface.trelloc.regions, query.data)[0]
    elif group.edit_argument == COLOR:
        print('TELEBOT: input_edit_group_argument(): Color')
        group.color = query.data
    elif group.edit_argument == PURPOSE:
        print('TELEBOT: input_edit_group_argument(): Purpose')
        group.purpose = update.message.text
    elif group.edit_argument == ONBOARDING:
        print('TELEBOT: input_edit_group_argument(): Onboarding')
        group.onboarding = update.message.text
    elif group.edit_argument == PARENT_GROUP:
        print('TELEBOT: input_edit_group_argument(): Parent group')
        group.parentgroup = query.data

    # Save group into database and delete persistence file
    group = interface.edit_group(group)
    utils.delete_pkl('edit_group', chat_id, user_id)

    # Send confirmation message
    # Markup
    text = format_group_info(group, type=1)
    print('TELEBOT: group card url: ', group.card_url)
    keyboard = [[InlineKeyboardButton("Trello Card", url=str(
        group.card_url)), InlineKeyboardButton("Edit Info", callback_data='edit_group')]]
    markup = InlineKeyboardMarkup(keyboard)
    group.message.delete()
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
    group = utils.load_pkl('edit_group', chat_id, user_id)
    update.callback_query.answer()
    if group == "" or user_id != group.user_id:
        return
    else:
        print("CANCEL PRESSED")
        group.message.edit_text(
            text=cancel_edit_group_text, parse_mode=ParseMode.HTML)
        utils.delete_pkl('edit_group', chat_id, user_id)
    return ConversationHandler.END

