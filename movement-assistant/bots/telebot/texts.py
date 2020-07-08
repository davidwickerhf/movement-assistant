# GROUP CONVERSATION MESSAGES TEXT
save_group_message = "<b>TRANSPARENCY BOT</b> \nThank you for adding me to this chat! I am the FFF Transparency Bot and I'm managed by the [WG] Transparency! \nI can help your group by keeping track of planned calls.\nPlease follow this wizard to complete saving this group's informations in the database:\n\n<b>Select a Category for this group:</b>"
save_group_alreadyregistered_message = "<b>TRANSPARENCY BOT</b>\nThis group has already been registered once, no need to do it again\nType /help tp get a list of available commands"

# HELP COMMAND TEXTS
new_group_description = "- /activate -> This command is run automatically once the bot is added to a groupchat. It will get some information about the group (such as group Title and admins) and save it onto the FFF Database.\n<code>/newgroup</code>"
new_call_description = "- /newcall -> Schedule a call in the FFF Database as well as in the Transparency Calendar and Trello Board. \nArguments: <b>Title, Date, Time (GMT), Duration (optional), Description (optional), Agenda Link (optional):</b> \n<code>/newcall Group Call, Wednesday 15th March, 15:00, 00:45, Checkup Call, Link</code>"
help_description = "<b>BOT INFORMATION</b>\nThe FFF Transparency Bot can respond to the following commands:\n - /help -> Get a list of all available commands\n{}\n\n<b>The following commands are automatically run by the bot:</b>\n{}"



# CALL CONVERSATION TEXTS
new_call_onlygroups_message = "This bot command  only works in groupchats! \nIn order for this command to work, please add me to the group you are trying to schedule the call for. \nKindest regards, \nFFF Transparency Bot"
chat_not_registerred = "<b>This group is not yet registerred in the database</b> \nTo proceed in registering a new call for this group, please make sure the group is first registered in the database.\n\n<b>To register a call in the database, use the command:</b>\n\n {}\n\nFor any technical problems, contact @davidwickerhf"
input_argument_text = "<b>SCHEDULE A NEW CALL</b>\nFollow this wizard to schedule a new call!\n\nPlease reply to this message with the <b>{}</b> for the call you are registering\n\n[Step X out of X]"
wrong_time_text = "<b>WARNING</b>\nThe Time you submitted is not recognized. Please submit a time for the call again with the following format:\n<code>hours:minutes | 15:00</code>\nAlso note that the time you input will be treated as GMT"
wrong_date_text = "<b>WARNING</b>\nThe Date you submitted is not recognized. Please submit a date for the call again with the following format:\n<code>day/month/year | 15/03/2019</code>"
past_date_text = "Please insert a date in the future. you cannot schedule calls for a past date."
past_time_text = "Please insert a time in the future. You cannot schedule calls for a past time."
text_input_argument = "<b>SCHEDULE A NEW CALL - ADD A {}</b>\nFollow this wizard to schedule a new call!\n\nPlease reply to this message with the <b>{}</b> for the call you are registering"
cancel_add_call_text = "<b>CALL SCHEDULING CANCELLED</b>\nThe call hasn't been scheduled"

# CALLS CONVERSATION TEXT
select_calls_group_text = 'Select below:'
no_calls_text = 'No calls are available for this selection'
select_call_text = 'Select a call below:'

# EDIT CALL CONVERSATION TEXT
select_edit_call_argument_text = 'Slect below the information you would like to edit:'
call_not_exist_text = 'The selected call does not exist anymore. It may have been deleted. Please select another call:'
call_not_existing = 'The selected call does not exist anymore, it may have been deleted or updated.'
edit_ctitle_text = 'Reply to this message with the <b>new Title</b> of the selected call.'
edit_cdate_text = 'Reply to this message with the <b>new Date</b> for the selected call. Make sure the date is in the future and that it matches the following formats: <code>15/03/2019</code> or <code>Today/Tomorrow</code>'
edit_ctime_text = 'Reply to this message with the <b>new Time</b> of the selected call. The time needs to be in the future (or at maximum 45 minutes previous the current time) Make sure the time is in UTC and in the following format: <code>15:00</code> (hours:minutes)'
edit_cduration_text = 'Reply to this message with the <b>new Duration</b> of the selected call. Make sure the duration is in the following format: <code>00:45</code> (hours:minutes)'
edit_cdescription_text = 'Reply to this message with the <b>new Description</b> of the selected call.'
edit_cagenda_text = 'Reply to this message with the <b>new Agenda Link</b> (GDocs or Pad) for the selected call. Make sure you insert a link.'
edit_clink_text = 'Reply to this message witht the <b>new Call Link</b> (Zoom, Jitsu, etc) for the selected call. Make sure you insert a link.'
wrong_duration_text = '<b>WARNING</b>\nThe Duration you submitted is not recognized. Please submit a duration for the call again with the following format:\n<code>hours:minutes | 00:45 | 01:15</code>'
wrong_link_text = 'The text you inserted is not a valid link. Please try again:'
cancel_edit_call_text = "<b>CALL EDITS CANCELLED</b>\nThe call hasn't been edited"



# FEEDBACK CONVERSATION MESSAGES TEXT
select_feedback_type = "Select below the type of <b>feedback</b> you are giving:"
send_feedback_input = "Reply to this message with the feedback you want to send:"
select_issue_type = "Select below the command you are having an <b>issue</b> with. If you are trying to report another issue, select 'Other'"
send_issue_input = "Reply to this message describing the issye you have encountered in order to send your feedback:"
cancel_feedback_text = "<b>FEEDBACK INPUT CANCELLED</b>\nNo feedback has been sent"

# EDIT GROUP CONVERSATION TEXT
no_permission_edit_group = '<b>This group has not been activated yet</b> \nBefore editing this group\'s info, please activate it using /activate'
edit_category_text = 'Select below the new <b>category</b> for this group:'
edit_restriction_text = 'Select below the new <b>restriction</b> for this group:'
edit_region_text = 'Select below the correct <b>region</b> this group concerns:'
edit_color_text = 'Select below a new <b>color</b> for this group:'
edit_purpose_text = 'Reply to this message with the updated <b>purpose</b> of this group:'
edit_onboarding_text = 'Reply to this message with the updated <b>onboarding</b> procedure for this group:'
edit_is_subgroup_text = 'Select below weather this group is a sub-group of another group or not'
edit_parent_text = 'Select below the new <b>parent group</b> for this group'
no_parents_edit_parent = 'Cannot add a parent group to this group as no other group has been activated yet.'
editing_group_text = 'Editing group\'s information... This might take a while'
edited_group_text = 'This group\'s information has been updated:'
cancel_edit_group_text = '<b>GROUP EDIT CANCELLED</b>\nThe group hasn\'t been edited'

# GROUP INFO COMMAND TEXTS
group_info_text = '<b>{}</b>\'s information:'
chat_not_registerred_info = 'This chat is not registered yet. To activate this group chat, use the command /activate'

# WEB OF TRUST TEXTS
no_access_group_info_text = 'Sorry, you don\' have access to Fridays For Future\'s web of trust yet'