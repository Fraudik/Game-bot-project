from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
import random
# это все игры, которые доступны, в формате: команду на вызов игры - описание игры
games = '/быки и коровы - математическая игра, в двух изданиях: в одиночку и против бота\n' \
        '/крестики-нолики - классические крестики-нолики с 3 уровнями сложности\n' \
        '/сапер - классический сапер, размер поля варьируется от 5 на 5, до 26 на 26 клеток\n' \
        '/камень-ножницы-бумага - классические... камень-ножницы-бумага!\n' \
        '/кости - вы должны будете выбросить кости больше чем у вашего противника - бота\n\n' \
        'Более подробные правила игр описаны внутри каждой из них. Пусть Фортуна будет благосклонна к вам!'
# это база откуда мы будем брать реакции на разные фразы.
dialog_base = {['игр', 'play', 'game']: ('Вот список моих игр: ' + games, ['']),
               ['не поня', 'что делать', 'помо', 'faq', 'FAQ', 'баг']: faq}
'''
dialog_base['диалог'] = ('О чем поговорим?', ['шутки', 'цитаты, связанные с играми'])}
greetings = 'хай хэй здравствуй прив hi hello hey'.split(' ')
for i in greetings:
    dialog_base[i] = (i.capitalize() + ', поболтаем или поиграем?', ['диалог', 'игры'])
# до фразы диалог (или разговор) количество реплик сильно ограничено, но возможно будет расскрывать
# репликами от пользователей. тоже самое касается и шуток, и загадок, и цитат.
# Но! Все пользовательские реплики добавляются в отдельный список,
# и у людей будет предоставлен выбор - включать их или нет.

 jokes = ['Колобок повесился', 'У Штирлица было 2 двойника, 3 тройника и 1 удлинитель',
         'Носорог плохо видит, но это не его проблема', 'Не сходи с ума. Сходи за хлебом',
         'Быть гением вовсе не трудно. Это вам любой психиатр подтвердит',
         'Знаете почему плачат дети, которых не прививают родители? Кризис среднего возраста']
dialog_base['шутки'] = random.choice(jokes)
dialog_base['анекдоты'] = random.choice(jokes) 
'''
# ДАННЫЙ КОД НАХОДИТСЯ В РАЗРАБОТКЕ
# диалоговая система оказалась сложнее, чем я думал и я решил отложить ее до конца проекта.
# посмотреть dialogflow


def start(update, context):
    update.message.reply_text("Привет! Я игровой бот!"
                              " Могу сыграть с вами в различные игры. Наберите '/игры' или даже просто слово 'игра'"
                              "и я покажу, какие игры у меня есть!")
    # under development
    # будет говорить, что это за бот и зачем он.


def instruction(update, context):
    update.message.reply_text("Если у вас возникли какие-то проблемы, или вы нашли ошибку - пишите по адресу"
                              "fraudbot.help@mail.ru\n"
                              "Кроме этого, существуют ответы на популярные вопросы - FAQ. Доступ к ним в пыолучит по команде"
                              "'/faq'")
    # under development
    # будут перечислены установки бота при общении, темы, на которые можно поговорить,
    # а также команды с их кратким пояснением


def chat(update, context):
    for i in dialog_base:
        if any(word in update.message.text for word in i):
            update.message.reply_text(dialog_base[i])
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
