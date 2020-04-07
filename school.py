from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
# это все игры, которые доступны, в формате: команду на вызов игры - описание игры
games = '/быки и коровы - математическая игра, в двух изданиях: в одиночку и против бота\n' \
        '/крестики-нолики - классические крестики-нолики с 3 уровнями сложности\n' \
        '/сапер - классический сапер, размер поля варьируется от 5 на 5, до 26 на 26 клеток\n' \
        '/камень-ножницы-бумага - классические... камень-ножницы-бумага!\n' \
        '/кости - вы должны будете выбросить кости больше чем у вашего противника - бота\n\n' \
        'Более подробные правила игр описаны внутри каждой из них. Пусть Фортуна будет благосклонна к вам!'
# это база откуда мы будем брать реакции на разные фразы.
dialog_base = {['игр', 'play', 'game']: 'Вот список моих игр: ' + games}
greetings = 'хай хэй здравствуй прив hi hello hey'.split(' ')
for i in greetings:
    dialog_base[i] = i.capitalize() + ', как дела?'
good_emotions = 'нормально хорошо круто весело потрясно неплохо отлично'.split()
for i in good_emotions:
    dialog_base[i] = 'Рад за тебя! А знаешь, что может сделать этот день еще лучше? Мои игры!'
bad_emotions = 'грустно скучно плохо ужасно скучно'.split()
for i in bad_emotions:
    dialog_base[i] = 'Ох, мне жаль. Но я могу попробовать немного развеселить тебя играми.'


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
