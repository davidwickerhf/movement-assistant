from movement_assistant import telegram, telegram_bot, update_queue, app, teleTOKEN
from flask import request


@app.route('/{}'.format(teleTOKEN), methods=['POST'])
def receive_update():
    print("APP: Received Update")
    update = telegram.Update.de_json(
        request.get_json(force=True), telegram_bot)
    update_queue.put(update)
    return 'ok'


# RECEIVE OTHER WEBHOOKS
""" @app.route('/other_webhook_route', methods=['POST'])
def receive_child_update(token):
    json_update = request.get_json(force=True)
    do_something(json_update)
    return 'ok' """


@app.route('/')
def index():
    return '.'
