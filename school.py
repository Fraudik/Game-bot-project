from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove


def start(update, context):
    update.message.reply_text("Привет! Я игровой бот!")
    # under development
    # будет говорить, что это за бот и зачем он.


def instruction(update, context):
    update.message.reply_text("Я могу побеседовать с вами о:..., для этого ..."
                              "\n Твкже я обладаю командами:\n/start - приветствие\n")
    # under development
    # будут перечислены установки бота при общении, темы, на которые можно поговорить,
    # а также команды с их кратким пояснением


def chat(update, context):
    update.message.reply_text("Я услышал" + update.message.text + ".")
    # under development
    # чат. будут добавляться установки на общение и ответные реакции.


def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", instruction))
    dp.add_handler(MessageHandler(Filters.text, chat))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
