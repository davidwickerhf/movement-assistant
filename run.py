from fff_automation.modules import settings
from fff_automation import app, telegram_bot, teleTOKEN, URL


if __name__ == '__main__':
    s = telegram_bot.setWebhook('{URL}{HOOK}'.format(URL=URL, HOOK=teleTOKEN))
    if s:
        print("APP: Webhook setup correctly") 
    else:
        print("APP: Error in setting up webhook")
    app.run(threaded=True) 