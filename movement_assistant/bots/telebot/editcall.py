from movement_assistant.bots.telebot import *


@run_async
def edit_call(update, context):
    print('TELEBOT: edit_call()')
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    user = database.get(table=database.USERS, item_id=user_id)[0]
    if user == None:
        print('TELEBOT: user not in Web of Trust')
        update.message.reply_text(text=no_access_group_info_text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    elif update.callback_query:
        print('TELEBOT: edit_call(): Entering from callback')
        message_text = update.callback_query.message.text
        key = message_text[-6:]
        print('Key: ', key)
        botupdate = BotUpdate(update=update, user=update.effective_user)
        botupdate.obj = database.get(table=database.CALLS, item_id=key, field='key')[0]
        if botupdate.obj == None:
            print('TELEBOT: call does not exist anymore')
            update.callback_query.message.edit_text(text=call_not_existing, parse_mode=ParseMode.HTML)
            return ConversationHandler.END
        else:
            markup = create_menu(['Call Title', 'Date', 'Time', 'Duration', 'Description', 'Agenda Link', 'Call Link', 'Cancel'], [EDIT_CTITLE, EDIT_CDATE, EDIT_CTIME, EDIT_CDURATION, EDIT_CDESCRIPTION, EDIT_CAGENDA, EDIT_CLINK, 'cancel_edit_call'], 2)
            text = utils.format_call_info(botupdate) + '\n\n' + select_edit_call_argument_text
            botupdate.message = update.callback_query.edit_message_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
            utils.dump_pkl('edit_call', botupdate)
            return SELECT_CEDIT_ARGUMENT
    else:
        botupdate = BotUpdate(update=update, user=update.effective_user)
        calls = database.get(table=database.CALLS, item_id=chat_id, field='chat_id')
        if len(calls) > 0 and calls[0] != None:
            markup = rotate_calls(botupdate, RIGHT)
            botupdate.message = update.message.reply_text(text=select_call_text, parse_mode=ParseMode.HTML, reply_markup=markup)
            utils.dump_pkl('edit_call', botupdate)
            return SELECT_CALL
        else:
            update.message.reply_text(text=no_calls_text, parse_mode=ParseMode.HTML)
            return ConversationHandler.END
        
        
@run_async
def select_edit_call(update, context):
    print('TELEBOT: select_edit_call()')
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    botupdate = utils.load_pkl('edit_call', chat_id, user_id)
    if botupdate == None:
        update.callback_query.answer()
        return SELECT_CALL
    else:
        query = update.callback_query
        try:
            if int(query.data) in (LEFT, RIGHT):
                try:
                    markup = rotate_calls(botupdate, int(query.data))
                    update.callback_query.message.edit_text(text=select_call_text, reply_markup=markup, parse_mode=ParseMode.HTML)
                except:
                    print('TELEBOT: select_edit_call(): Rotated calls are the same')
                    query.answer()
                return SELECT_CALL
        except:
            botupdate.obj = database.get(table=database.CALLS, item_id=update.callback_query.data)[0]
            if botupdate.obj == None:
                print('TELEBOT: call does not exist anymore')
                markup = rotate_calls(botupdate, RIGHT)
                update.callback_query.message.edit_text(text=call_not_exist_text, reply_markup=markup, parse_mode=ParseMode.HTML)
                return SELECT_CALL
            else:
                markup = create_menu(['Call Title', 'Date', 'Time', 'Duration', 'Description', 'Agenda Link', 'Call Link', 'Cancel'], [EDIT_CTITLE, EDIT_CDATE, EDIT_CTIME, EDIT_CDURATION, EDIT_CDESCRIPTION, EDIT_CAGENDA, EDIT_CLINK, 'cancel_edit_call'], 2)
                text = utils.format_call_info(botupdate) + '\n\n' + select_edit_call_argument_text
                botupdate.message.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
                utils.dump_pkl('edit_call', botupdate)
                return SELECT_CEDIT_ARGUMENT


@run_async
def select_edit_call_argument(update, context):
    print('TELEBOT: select_call_argument()')
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    botupdate = utils.load_pkl('edit_call', chat_id, user_id)
    if botupdate == None:
        update.callback_query.answer()
        return SELECT_CEDIT_ARGUMENT
    else:
        if update.callback_query.data == 'cancel_edit_call':
            cancel_edit_call(update, context)
            return ConversationHandler.END
        botupdate.edit_argument = int(update.callback_query.data)
        if botupdate.edit_argument == EDIT_CTITLE:
            text = edit_ctitle_text
        elif botupdate.edit_argument == EDIT_CDATE:
            text = edit_cdate_text
        elif botupdate.edit_argument == EDIT_CTIME:
            text = edit_ctime_text
        elif botupdate.edit_argument == EDIT_CDURATION:
            text = edit_cduration_text
        elif botupdate.edit_argument == EDIT_CDESCRIPTION:
            text = edit_cdescription_text
        elif botupdate.edit_argument == EDIT_CAGENDA:
            text = edit_cagenda_text
        else:
            text = edit_clink_text
        markup = create_menu(['Cancel'], ['cancel_edit_texts'])
        botupdate.message.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        utils.dump_pkl('edit_call', botupdate)
        return INPUT_CEDIT_ARGUMENT


@run_async
@send_typing_action
def input_edit_call_argument(update, context):
    print('TELEBOT: input_call_argument()')
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    botupdate = utils.load_pkl('edit_call', chat_id, user_id)
    if botupdate == None:
        update.callback_query.answer()
        return INPUT_CEDIT_ARGUMENT
    else:
        if update.callback_query and update.callback_query.data == 'cancel_edit_call':
            cancel_edit_call(update, context)
            return ConversationHandler.END
        elif botupdate.edit_argument == EDIT_CTITLE:
            print('TELEBOT: input_edit_call_argument(): edit Title')
            botupdate.obj.title = update.message.text
        
        elif botupdate.edit_argument == EDIT_CDATE:
            print('TELEBOT: input_edit_call_argument(): edit Date')
            date = utils.str2date(update.message.text)
            if date:
                # CHECK PAST DATE
                now = datetime.now(tz=pytz.utc).date()
                if date >= now:
                    # DATE IS IN THE FUTURE
                    botupdate.obj.date = date
                    print("Date is valid: ", botupdate.obj.date)
                else:
                    # DATE IS IN THE PAST
                    print('TELEBOT: input_edit_call_argument(): edit Date: Date in the past')
                    markup = create_menu(['Cancel'], ['cancel_edit_call'])
                    botupdate.message.delete()
                    botupdate.message = update.message.reply_text(
                        text=past_date_text, parse_mode=ParseMode.HTML, reply_markup=markup)
                    utils.dump_pkl('edit_call', botupdate)
                    return INPUT_CEDIT_ARGUMENT
            else:
                print('TELEBOT: input_edit_call_argument(): edit Date: Date not accepted')
                botupdate.message.delete()
                markup = create_menu(['Cancel'], ['cancel_edit_call'])
                botupdate.message = update.message.reply_text(text=wrong_date_text, reply_markup=markup, parse_mode=ParseMode.HTML)
                return INPUT_CEDIT_ARGUMENT

        elif botupdate.edit_argument == EDIT_CTIME:
            print('TELEBOT: input_edit_call_argument(): edit Time')
            time = utils.str2time(update.message.text)
            if time:
                local_tz = get_localzone()
                offset = timedelta(minutes=45)
                now = datetime.now(tz=local_tz).astimezone(pytz.utc) - offset
                if botupdate.obj.date == now.date():
                    if time >= now.time():
                        # TIME IS ACCEPTABLE
                        botupdate.obj.time = time
                    else:
                        # TIME IS IN THE PAST
                        print('TELEBOT: input_edit_call_argument(): edit Date: Time in the past')
                        markup = create_menu(['Cancel'], ['cancel_edit_call'])
                        botupdate.message.delete()
                        botupdate.message = update.message.reply_text(
                            text=wrong_time_text, parse_mode=ParseMode.HTML, reply_markup=markup)
                        utils.dump_pkl('edit_call', botupdate)
                        return INPUT_CEDIT_ARGUMENT
                else: 
                    botupdate.obj.time = time
            else: 
                print('TELEBOT: input_edit_call_argument(): edit Date: Time not valid')
                markup = create_menu(['Cancel'], ['cancel_edit_call'])
                botupdate.message.delete()
                botupdate.message = update.message.reply_text(
                    text=past_date_text, parse_mode=ParseMode.HTML, reply_markup=markup)
                utils.dump_pkl('edit_call', botupdate)
                return INPUT_CEDIT_ARGUMENT

        elif botupdate.edit_argument == EDIT_CDURATION:
            print('TELEBOT: input_edit_call_argument(): edit Duration')
            duration = utils.str2duration(update.message.text)
            if duration:
                botupdate.obj.duration = duration
            else:
                print('TELEBOT: input_edit_call_argument(): edit Date: Duration not valid')
                markup = create_menu(['Cancel'], ['cancel_edit_call'])
                botupdate.message.delete()
                botupdate.message = update.message.reply_text(
                    text=wrong_duration_text, parse_mode=ParseMode.HTML, reply_markup=markup)
                utils.dump_pkl('edit_call', botupdate)
                return INPUT_CEDIT_ARGUMENT

        elif botupdate.edit_argument == EDIT_CDESCRIPTION:
            print('TELEBOT: input_edit_call_argument(): edit Description')
            botupdate.obj.description = update.message.text

        elif botupdate.edit_argument == EDIT_CAGENDA:
            print('TELEBOT: input_edit_call_argument(): edit Agenda')
            if utils.is_link(update.message.text):
                botupdate.obj.agenda_link = update.message.text
            else:
                print('TELEBOT: input_edit_call_argument(): edit Date: Duration not valid')
                markup = create_menu(['Cancel'], ['cancel_edit_call'])
                botupdate.message.delete()
                botupdate.message = update.message.reply_text(
                    text=wrong_link_text, parse_mode=ParseMode.HTML, reply_markup=markup)
                utils.dump_pkl('edit_call', botupdate)
                return INPUT_CEDIT_ARGUMENT

        else:
            print('TELEBOT: input_edit_call_argument(): edit Link')
            if utils.is_link(update.message.text):
                botupdate.obj.agenda_link = update.message.text
            else:
                print('TELEBOT: input_edit_call_argument(): edit Date: Duration not valid')
                markup = create_menu(['Cancel'], ['cancel_edit_call'])
                botupdate.message.delete()
                botupdate.message = update.message.reply_text(
                    text=wrong_link_text, parse_mode=ParseMode.HTML, reply_markup=markup)
                utils.dump_pkl('edit_call', botupdate)
                return INPUT_CEDIT_ARGUMENT

        # Save Edited Call
        interface.edit_call(botupdate)
        # Return feedback
        text = utils.format_call_info(botupdate, context='edit_call')
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(text='Trello Card', url=botupdate.get_card_url()), InlineKeyboardButton(text='Edit Info', callback_data='edit_call')]])
        botupdate.message.delete()
        update.message.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        return ConversationHandler.END


@run_async
def cancel_edit_call(update, context):
    print('TELEBOT: Cancel Edit Call')
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.callback_query.from_user.id
    botupdate = utils.load_pkl('edit_call', chat_id, user_id)
    update.callback_query.answer()
    if botupdate == None:
        return
    else:
        print("CANCEL PRESSED")
        botupdate.message.edit_text(
            text=cancel_edit_call_text, parse_mode=ParseMode.HTML)
        utils.delete_pkl('edit_call', chat_id, user_id)
    return ConversationHandler.END