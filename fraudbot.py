import discord
import sqlite3
import random
import requests
import pymorphy2
from itertools import product

TOKEN = "BOT_TOKEN"


# база, в которой будут храниться заработанные очки и статус отношений бота с пользователем - играет оно и во что,
# или просто общается


class Bnc:
    @staticmethod
    # возвращает быки и коровы, сравнивая 2 числа
    def bulls_n_cows(a, b):
        bulls = sum(1 for x, y in zip(a, b) if x == y)
        cows = len(set(a) & set(b)) - bulls
        return str(bulls), str(cows)

    @staticmethod
    # генерирует число
    def generate_answer():
        n = [i for i in range(10)]
        number = []
        for _ in range(4):
            a = n.pop(random.choice(range(len(n))))
            number.append(str(a))
        return ''.join(number)


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
                            '/помощь': 'помощь. создается.',
                            '/старт': 'Привет! Я игровой бот! Могу сыграть с вами в различные игры. Наберите "/игры" '
                                      'и я покажу, какие игры у  меня есть! Кроме того, у меня есть команда "/помощь".'
                                      ' Попробуйте ее ввести!'}

    async def on_message(self, message):
        # не даем отвечать самому себе
        if message.author == self.user:
            return
        # если пользователь "свободен" от наших игр или диалога
        if message.content == '/стоп':
            await self.db_edit(message.author.name + message.author.discriminator, 'empty')
        if self.user_status(message.author.name + message.author.discriminator) == 'empty':
            for i in self.dialog_base:
                if message.content == i:
                    await message.channel.send(self.dialog_base[i])
        if message.content == '/быки и коровы':
            await self.db_edit(message.author.name + message.author.discriminator, 'bnc')
            # это нужно, чтобы отслеживать сообщения именно от данного пользователя
            user_player = message.author
            await message.channel.send('Хорошо, ' + str(user_player) + '!\nУгадывающий называет число, а '
                                                                       'загадывающий специальным образом отвечает, '
                                                                       'сколько цифр совпало с ответом.\nЕсли в назван'
                                                                       'ном числе цифра какого-то раз'
                                                                       'ряда совпала с цифрой в том же разряде правил'
                                                                       'ьного ответа, '
                                                                       'это называется «быком». Если указанная цифра '
                                                                       'есть в ответе, но на неверной'
                                                                       ' позиции, это «корова». Загадывающий отвечает,'
                                                                       ' сколько «быков» и «коров» '
                                                                       'в числе угадывающего.\n'
                                                                       'Вы собираетесь просто отгадывать, играть'
                                                                       ' против бота(одновременно загадывать свое число '
                                                                       'и отгадывать его),'
                                                                       ' или вы не собираетесь играть?\nЧтобы ответи'
                                                                       'ть, введите'
                                                                       ' один из следующих вариантов: '
                                                                       ' 1  |  2  |  /стоп\n'
                                                                       '\nЕсли вы '
                                                                       'пожелаете прекратить игру, то в любой'
                                                                       ' момент введите команду "/стоп"')

            def check(m):
                # проверяем, что точно сообщение от нашего игрока и что он не случайно нажала enter
                return len(m.content) != 0 and m.author == user_player

            choice = await self.wait_for('message', check=check)
            while choice.content not in ('1', '2', '/стоп'):
                await message.channel.send(str(user_player) + ', чтобы ответить,'
                                                              ' введите один из следующих вариантов: \n1\n2\n/стоп')
                choice = await self.wait_for('message', check=check)
            if choice.content == '/стоп':
                # стоп игры
                await self.db_edit(message.author.name + message.author.discriminator, 'empty')
            elif choice.content == '1':
                # генерируем число, выводим быки и коровы, пока игрок не выиграет
                answer = Bnc.generate_answer()
                await message.channel.send('Вы в одиночной игре, ' + str(user_player) + '! Бот уже загадал число,'
                                                                                        ' попробуйте угадать его. Введите четырехзначное число'
                                                                                        ' с неповторяющимися цифрами.')
                win = False
                number = 1

                async def bnc_user_input():
                    # пользовательский ввод для игры быки и коровы
                    user_try = await self.wait_for('message', check=check)
                    # по другому это не сделать, так как нельзя напрямую обратьтся к coroutine
                    user_try = user_try.content
                    while user_try != '/стоп' and (len(set(list(user_try))) != 4 or
                                                   user_try not in [str(d) for d in range(1000, 9999)]):
                        await message.channel.send(str(user_player) + ', введите четырехзначное число'
                                                                      ' с неповторяющимися цифрами или команду "/стоп",'
                                                                      ' чтобы прекратить игру.')
                        user_try = await self.wait_for('message', check=check)
                        user_try = user_try.content
                    return user_try

                morph = pymorphy2.MorphAnalyzer()
                user_input = await bnc_user_input()
                # количество попыток
                while not win:
                    if user_input == '/стоп':
                        break
                    bulls, cows = Bnc.bulls_n_cows(user_input, answer)
                    cows = cows + ' ' + morph.parse('корова')[0].make_agree_with_number(int(cows)).word
                    bulls = bulls + ' ' + morph.parse('бык')[0].make_agree_with_number(int(bulls)).word
                    await message.channel.send(str(user_player) + f"\n{number} попытка. Твое число {user_input}."
                                                                  f" У тебя {cows} и {bulls}")
                    if '4' in bulls:
                        win = True
                        break
                    else:
                        user_input = await bnc_user_input()
                        number += 1
                if win:
                    await message.channel.send('Невероятная победа, ' + str(user_player) + '! Вы сделали это'
                                                                                           ' всего за ' + str(number)
                                               +
                                               ' ' + morph.parse('попытку')[0].make_agree_with_number(number).word)\
                                               + '.'
                await message.channel.send('Игра окончена.')
                await self.db_edit(user_player.name + user_player.discriminator, 'empty')
            # создается далее. вариант с 2 игроками.
            # запуск игры быки и коровы. сначала объяснение и только потом старт.

    async def db_edit(self, user_id, status):
        # функция заносит игрока в базу данных, или изменяет статус, если он там уже есть.
        cur = self.con.cursor()
        user = cur.execute("Select * from users WHERE user_id=?", (user_id,)).fetchone()
        if user is None:
            cur.execute('INSERT INTO users(user_id, points, state) VALUES(?, ?, ?)', (str(user_id), '0', status))
        else:
            cur.execute('UPDATE users SET state = "' + status + '" WHERE user_id = "' + str(user_id) + '"')
        self.con.commit()

    def user_status(self, user_id):
        # получение статуса пользователя
        cur = self.con.cursor()
        user = cur.execute("Select * from users WHERE user_id=?", (user_id,)).fetchone()
        if user is None:
            return 'empty'
        return user[2]

    async def on_ready(self):
        cur = self.con.cursor()
        users = cur.execute("Select * from users").fetchall()
        for i in users:
            cur.execute('UPDATE users SET state = "empty" WHERE user_id = "' + str(i[0]) + '"')
        self.con.commit()


client = Fraudbot()
client.run(TOKEN)
