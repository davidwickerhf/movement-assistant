from movement_assistant.bots.telebot import *


####################### CALL CONVERSATION FUNCTIONS #########################
@run_async
@send_typing_action
def new_call(update, context):
    message = update.message
    groupchat = update.message.chat
    user = message.from_user
    chat_id = groupchat.id

    print("Got chat id")

    if groupchat.id == user.id:
        # CHAT IS USER
        print("Chat is user")
        groupchat.send_message(
            text=new_call_onlygroups_message)
        return ConversationHandler.END
    elif database.get(item_id=update.message.chat.id)[0] == None:
        # CHAT IS NOT REGISTERED
        print("Chat is not registered yet")
        text = chat_not_registerred.format(
            new_group_description)
        groupchat.send_message(
            text=text, parse_mode=ParseMode.HTML)
        return ConversationHandler.END
    else:
        # EVERYTHING OK
        message_text = update.message.text + ' '
        print("Message Text: " + message_text)
        command = message_text[:message_text.find(' ') + 1]
        print(command)
        # ALGORITHM IS NOT WORKING - AND IS SLOW
        propcall = Call(chat_id=chat_id, activator_id=user.id)
        call = utils.format_string(message_text, command, propcall)
        botupdate = BotUpdate(obj=call, update=update, user=update.effective_user)

        # ARGUMENTS FORMAT: TITLE, DATE, TIME, DURATION, DESCRIPTION, AGENDA LINK, LINK
        print("GET ARGUMENTS")
        if call.title == '':
            print("Requesting Title input")
            # SEND MESSAGE
            format_input_argument(update, 0, call.TITLE, botupdate)
            return ADD_TITLE
        elif call.date == '':
            print("Title is not missing - Requesting Date input")
            # SEND MESSAGE
            format_input_argument(update, 0, call.DATE, botupdate)
            return ADD_DATE
        elif call.time == '':
            print("Date is not missing - Requesting Time input")
            # SEND MESSAGE
            format_input_argument(update, 0, call.TIME, botupdate)
            return ADD_TIME

        print("Not returned get arguments -> ALL necessary arguments are alraedy given")
        # SAVE CALL TO DATABASE

        save_call_info(update, context, botupdate)
        return ConversationHandler.END


@run_async
@send_typing_action
def add_title(update, context):
    print("ADD CALL TITLE")
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    botupdate = utils.load_pkl('newcall', chat_id, user_id)
    if botupdate == None:
        return ADD_TITLE
    call = botupdate.obj
    call.title = update.message.text

    # Request Call Date Input
    if call.date == '':
        format_input_argument(update, 1, call.DATE, botupdate)
        return ADD_DATE
    elif call.time == '':
        format_input_argument(update, 1, call.TIME, botupdate)
        return ADD_TIME
    else:
        print("CONVERSATION END - send call details")
        # SAVE INFO IN DATABASE
        save_call_info(update, context, botupdate)
        return ConversationHandler.END


@run_async
@send_typing_action
def add_date(update, context):
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    botupdate = utils.load_pkl('newcall', chat_id, user_id)
    if botupdate == None:
        # USER DID NOT START CONVERSATION
        return ADD_DATE
    call = botupdate.obj
    print("ADD CALL DATE")
    print("Requesting user input")
    date_text = update.message.text
    print("Date Text: " + date_text)
    if utils.str2date(date_text) != None:
        # INPUT IS CORRECT
        date = utils.str2date(date_text)

        # CHECK PAST DATE
        now = datetime.now(tz=pytz.utc).date()
        if date >= now:
            # DATE IS IN THE FUTURE
            call.date = date
            print("Date is valid: ", call.date)
        else:
            # DATE IS IN THE PAST
            keyboard = [[InlineKeyboardButton(
                "Cancel", callback_data="cancel")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            botupdate.message.delete()
            botupdate.message = update.message.reply_text(
                text=past_date_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            utils.dump_pkl('newcall', botupdate)
            return ADD_DATE
    else:
        # INPUT IS INCORRECT
        keyboard = [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        botupdate.message.delete()
        botupdate.message = update.message.reply_text(
            text=wrong_date_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        utils.dump_pkl('newcall', botupdate)
        return ADD_DATE

    if call.time == '':
        format_input_argument(update, 1, call.TIME, botupdate)
        print("Going to next step")
        return ADD_TIME
    else:
        print("CONVERSATION END - send call details")
        # SAVE INFO IN DATABASE
        save_call_info(update, context, botupdate)
        return ConversationHandler.END


@run_async
@send_typing_action
def add_time(update, context):
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.message.from_user.id
    botupdate = utils.load_pkl('newcall', chat_id, user_id)
    if botupdate == None:
        return ADD_TIME
    call = botupdate.obj
    print("ADD TIME")
    print("Requesting user input")
    message_text = update.message.text
    if utils.str2time(message_text) != None:
        # INPUT IS CORRECT
        local_tz = get_localzone()
        time = utils.str2time(message_text)
        offset = timedelta(minutes=45)
        now = datetime.now(tz=local_tz).astimezone(pytz.utc) - offset

        if call.date == now.date():
            if time >= now.time():
                # TIME IS ACCEPTABLE
                call.time = time
            else:
                # TIME IS IN THE PAST
                keyboard = [[InlineKeyboardButton(
                    "Cancel", callback_data="cancel")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                botupdate.message.delete()
                botupdate.message = update.message.reply_text(
                    text=past_time_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
                utils.dump_pkl('newcall', botupdate)
                return ADD_TIME
        else:
            call.time = time
        print("Inputted time: ", str(call.time))
        print("CONVERSATION END - send call details")
        # SAVE INFO IN DATABASE
        save_call_info(update, context, botupdate)
        return ConversationHandler.END
    else:
        # INPUT IS INCORRECT
        keyboard = [[InlineKeyboardButton("Cancel", callback_data="cancel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        botupdate.message.delete()
        botupdate.message = update.message.reply_text(
            text=wrong_time_text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        utils.dump_pkl('newcall', botupdate)
        return ADD_TIME


@run_async
@send_typing_action
def cancel_call(update, context):
    # GET CALL SAVED IN PERSISTANCE FILE
    chat_id = update.effective_chat.id
    user_id = update.callback_query.from_user.id
    botupdate = utils.load_pkl('newcall', chat_id, user_id)
    update.callback_query.answer()
    if botupdate == None:
        return
    else:
        print("CANCEL PRESSED")
        botupdate.message.edit_text(
            text=cancel_add_call_text, parse_mode=ParseMode.HTML)
        utils.delete_pkl('newcall', chat_id, user_id)
    return ConversationHandler.END


def format_input_argument(update, state, key, botupdate):
    keyboard = [[InlineKeyboardButton(
        "Cancel", callback_data="cancel")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    call = botupdate.obj
    argument_title = call.order.get(key)

    if state == 0:
        print("SEND FIRST GET ARGUMENTS MESSAGE")
        # Code runs for the first time -> Send message
        botupdate.message = update.message.reply_text(text=text_input_argument.format(
            argument_title.upper(), argument_title), parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        # Code already run -> edit message
        botupdate.message.delete()
        botupdate.message = update.message.reply_text(text=text_input_argument.format(
            argument_title.upper(), argument_title), parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        print("EDIT GET ARGUMENTS MESSAGE")
    utils.dump_pkl('newcall', botupdate)


@send_typing_action
def save_call_info(update, context, botupdate):
    botupdate.message.delete()
    botupdate.message = update.message.chat.send_message(
        text="Saving call information... This might take a minute...")
    interface.save_call(botupdate)
    call = botupdate.obj
    if botupdate == None:
        botupdate.message.edit_text(
            text="There was a problem in adding the call to the database.\nPlease contact @davidwickerhf for technical support.")
        return ConversationHandler.END

    keyboard = [[InlineKeyboardButton("Calendar", url=str(
        botupdate.obj.calendar_url)), InlineKeyboardButton("Trello Card", url=str(botupdate.card_url))], [InlineKeyboardButton('Edit Info', callback_data='edit_call')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print("Made Kayboard")

    text = utils.format_call_info(botupdate, context="save_call")
    print("Formatted text")
    utils.delete_pkl('newcall', call.chat_id, botupdate.user.id)

    botupdate.message.delete()
    update.message.reply_text(
        text=text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    print("Sent Reply")
