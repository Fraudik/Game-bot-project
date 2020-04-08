import discord
import sqlite3
import random
import requests
TOKEN = "BOT_TOKEN"
# база, в которой будут храниться заработанные очки и статус отношений бота с пользователем - играет оно и во что,
# или просто общается


class Fraudbot(discord.Client):
    def __init__(self, **options):
        super().__init__(**options)
        # в базе хранятся данные о пользователях, user_id, points, state.
        # Первое это идентификатор, второе это очки, а третье - то, чем сейчас занимается бот с игроками.
        self.con = sqlite3.connect("users.db")
        # это все игры, которые доступны, в формате: команду на вызов игры - описание игры
        games = '/быки и коровы - математическая игра, в двух изданиях: в одиночку и против бота\n' \
                '/крестики-нолики - классические крестики-нолики с 3 уровнями сложности\n' \
                '/сапер - классический сапер, размер поля варьируется от 5 на 5, до 26 на 26 клеток\n' \
                '/камень-ножницы-бумага - классические... камень-ножницы-бумага!\n' \
                '/кости - вы должны будете выбросить кости больше чем у вашего противника - бота\n\n' \
                'Более подробные правила игр описаны внутри каждой из них. Пусть Фортуна будет благосклонна' \
                ' к вам!'
        # это база откуда мы будем брать реакции на разные фразы.
        self.dialog_base = {'/игры': 'Вот список моих игр: \n' + games,
                            '/faq': 'faq',
                            '/старт': 'Привет! Я игровой бот! Могу сыграть с вами в различные игры. Наберите "/игры" '
                                      'и я покажу, какие игры у  меня есть! Кроме того, у меня есть команда "/помощь".'
                                      ' Попробуйте ее ввести!'}

    async def on_message(self, message):
        # не даем отвечать самому себе
        if message.author == self.user:
            return
        # если пользователь "свободен" от наших игр или диалога
        if self.user_status(message.author.name + message.author.discriminator) == 'empty':
            for i in self.dialog_base:
                if message.content == i:
                    await message.channel.send(self.dialog_base[i])
        if message.content == '/быки и коровы':
            await self.db_edit(message.author.name + message.author.discriminator, 'bnc')
            # запуск игры быки и коровы. сначала объяснение и только потом старт.

    async def db_edit(self, user_id, status):
        # функция заносит игрока в базу данных, или изменяет статус, если он там уже есть.
        cur = self.con.cursor()
        user = cur.execute("Select * from users WHERE user_id=?", ('sf',)).fetchall()
        if len(user) == 0:
            cur.execute('INSERT INTO users(user_id, points, state) VALUES(?, ?, ?)', (str(user_id), '0', status))
        else:
            cur.execute('UPDATE users SET state = ' + status + ' WHERE user_id = ' + str(user_id))
        self.con.commit()

    def user_status(self, user_id):
        # получение статуса пользователя
        cur = self.con.cursor()
        user = cur.execute("Select * from users WHERE user_id=?", (user_id,)).fetchall()
        if len(user) == 0:
            return 'empty'


client = Fraudbot()
client.run(TOKEN)
