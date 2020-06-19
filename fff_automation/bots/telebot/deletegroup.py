from fff_automation.bots.telebot import *


####################### DELETE GROUP FUNCTIONS ##############################
@run_async
def delete_group(update, context):
    print("BOT: --- DELETE GROUP ---")
    user = update.message.from_user
    chat_id = update.message.chat.id

    member = update.message.chat.get_member(update.message.from_user.id)
    print("BOT: Member Status: ", member.status)
    if chat_id == user.id:
        print("Chat is user")
        update.message.chat.send_message(
            text="This command can be run only in group chats")
        return ConversationHandler.END
    elif database.get(item_id=chat_id)[0] == None:
        print("BOT - Delete Group: Group is not registerred")
        update.message.reply_text(
            text="This group isn't registerred yet, thus it can't be deleted. Please register this group with the following command:\n/newgroup - This command will take you through a wizard to register this group's information into the FFF Transparency Database.")
        return ConversationHandler.END
    elif member.status == "creator":
        print("BOT - Delete Group: Command was sent by owner/admin")
        markup = create_menu(['NO!', 'Yes, delete the group'], [0, 1])
        group = database.get(chat_id)[0]
        group.message = update.message.reply_text(
            text="<b>WARNING</b>\nBy deleting a group, it's information will be erased from the database and from the Trello Board. All tied calls events will be deleted from both the Trello Board and Google Calendar. Be aware that this action cannot be undone. Use /archivegroup if you are simply archiving the group.\n\nAre you sure you want to delete this group permanently?", reply_markup=markup, parse_mode=ParseMode.HTML)

        # ADD GROUP TO PERSISTANCE
        group.user_id = user.id
        utils.dump_pkl('deletegroup', group)
        return CONFIRM_DELETE_GROUP
    else:
        owner_username = ""
        for admin in update.message.chat.get_administrators():
            if admin.status == "creator":
                owner_username = admin.user.username
        print("BOT - Delete Group: User does not have permission to delete the group")
        update.message.reply_text(
            text="Sorry, you don't have permission to delete this group. Please ask the group owner to do it.\n@{}".format(owner_username))
        utils.delete_pkl('deletegroup', chat_id, user.id)
        return ConversationHandler.END


@run_async
def confirm_delete_group(update, context):
    print("BOT: --- CONFIRM DELETE GROUP ---")
    query = update.callback_query
    chat_id = update.effective_chat.id
    user_id = query.from_user.id
    group = utils.load_pkl('deletegroup', chat_id, user_id)
    if group == "" or group.user_id != user_id:
        # USER DOES NOT HAVE PERMISSION TO DELETE BOT
        print('TELEBOT: delete_group(): User does not have permission. Group: ', group)
        print('Query user: ', user_id)
        query.answer()
        return CONFIRM_DELETE_GROUP
    else:
        query.answer()
        print("BOT: Query Data: ", query.data, " Type: ", type(query.data))

        if query.data == str(0):
            # USER CLICKED DO NOT DELETE BUTTON
            text = "Alright, the group will not be deleted."
            query.edit_message_text(text, parse_mode=ParseMode.HTML)
            utils.delete_pkl('deletegroup', chat_id, user_id)
            return ConversationHandler.END
        elif query.data == str(1):
            # USER CLICKED DELETE BUTTON
            markup = create_menu(['No, don\'t', 'Yes, delete it'], [0, 1])
            text = "Are you really, really sure you want to permanently delete this group's information?"
            query.edit_message_text(text=text, reply_markup=markup)
            group.message = query.message
            utils.dump_pkl('deletegroup', group)
            return DOUBLE_CONFIRM_DELETE_GROUP
        print("BOT: Error in Query data in Confirm Delete Group")


@run_async
@send_typing_action
def double_confirm_delete_group(update, context):
    print("BOT: --- DOUBLE CONFIRM DELETE GROUP ---")
    chat_id = update.effective_chat.id
    user_id = update.callback_query.from_user.id
    group = utils.load_pkl('deletegroup', chat_id, user_id)
    if group == "" or group.user_id != user_id:
        # USER DOES NOT HAVE PERMISSION TO DELETE BOT
        return DOUBLE_CONFIRM_DELETE_GROUP
    else:
        query = update.callback_query
        query.answer()
        if query.data == str(0):
            # USER CLICKED DO NOT DELETE BUTTON
            text = "Alright, the group will not be deleted."
            query.edit_message_text(text=text)
            # DELETE PERSISTENCE FILE
            utils.delete_pkl('deletegroup', chat_id, user_id)
            return ConversationHandler.END
        elif query.data == str(1):
            # USER CLICKED DELETE BUTTON
            text = "Ok, this group is being deleted... This might take a minute..."
            query.edit_message_text(text=text)
            interface.delete_group(group)
            text = "@{} Cool, this group's information has been deleted from the database, as well as the Trello Board. All call events have been erased.".format(
                query.from_user.username)
            query.edit_message_text(text=text)
            # DELETE PERSISTENCE FILE
            utils.delete_pkl('deletegroup', chat_id, user_id)
            return ConversationHandler.END

