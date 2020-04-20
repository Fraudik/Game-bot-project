import discord
import sqlite3
import random
import requests
import pymorphy2
from itertools import product

TOKEN = "Njk0OTMzMDExNjYxMDYyMTg2.Xp24FQ.pAN_5_BJGmDKpNTNsrpLLdR4ktA"


# база, в которой будут храниться заработанные очки и статус отношений бота с пользователем - играет оно и во что,
# или просто общается


class Bnc:
    def __init__(self):
        random.seed(self.generate_answer())
        self.attempt = self.k = 0
        self.everything = ["".join(x) for x in product('0123456789', repeat=4)
                           if len(set(x)) == len(x)]
        self.answer = self.generate_answer()
        self.guess_space = set(self.everything)
        self.historys = []
        self.history = []
        self.digitals = []

    def is_compatible(self, guess):
        return all(self.bulls_n_cows(guess, previous_guess) == (bulls, cows)
                   for previous_guess, bulls, cows in self.historys)

    @staticmethod
    # возвращает быки и коровы, сравнивая 2 числа
    def bulls_n_cows(attempt, answer):
        bulls = sum(1 for x, y in zip(attempt, answer) if x == y)
        cows = len(set(attempt) & set(answer)) - int(bulls)
        return bulls, cows

    @staticmethod
    def bulls_n_cows_morph(bulls, cows):
        morph = pymorphy2.MorphAnalyzer()
        cows = str(cows) + ' ' + morph.parse('корова')[0].make_agree_with_number(int(cows)).word
        bulls = str(bulls) + ' ' + morph.parse('бык')[0].make_agree_with_number(int(bulls)).word
        return bulls, cows

    @staticmethod
    # генерирует число
    def generate_answer():
        n = [i for i in range(10)]
        number = []
        for _ in range(4):
            a = n.pop(random.choice(range(len(n))))
            number.append(str(a))
        return ''.join(number)

    def cheat(self):
        error = True
        new_answer = None
        while error:
            new_answer = self.generate_answer()
            while new_answer == self.answer:
                new_answer = self.generate_answer()
            else:
                if self.history:
                    for i in self.history:
                        if self.bulls_n_cows(i[0], new_answer) != [i[1], i[2]]:
                            error = True
                            break
                        else:
                            error = False
                else:
                    error = False
        if not error:
            self.answer = new_answer


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
                '/кости - вы делаете ставки на сумму выброшенных ботом костей\n\n' \
                'Более подробные правила игр описаны внутри каждой из них. Пусть Фортуна будет благосклонна' \
                ' к вам!'
        # это база откуда мы будем брать реакции на разные фразы.
        self.dialog_base = {'/игры': 'Вот список моих игр: \n' + games,
                            '/привет': 'Здравствуйте! Я Fraudbot. Я представляю математические игры, то есть игры,'
                                       ' где используется математическое мышление. Команда "/игры" -- '
                                       'здесь описаны мои игры и команды для их вызова.\n',
                            '/помощь': 'Если у вас возник вопрос, или у вас есть какая-то идея -- пишите на адрес '
                                       'fraudbot.help@mail.ru'}

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
        else:
            # если пользователь не "свободен" от наших игр или диалога, то мы не даем еще раз запустить цикл
            return

        def check(m):
            # проверяем, что точно сообщение от нашего игрока и что он не случайно нажала enter
            return len(m.content) != 0 and m.author == user_gambler

        if message.content == '/быки и коровы':
            await self.db_edit(message.author.name + message.author.discriminator, 'bnc')
            # это нужно, чтобы отслеживать сообщения именно от данного пользователя
            user_gambler = message.author
            user_player = str(user_gambler)
            await message.channel.send('Хорошо, ' + user_player + '!\nУгадывающий называет число, а '
                                                                  'загадывающий специальным образом отвечает, '
                                                                  'сколько цифр совпало с ответом.\nЕсли в назван'
                                                                  'ном числе цифра какого-то раз'
                                                                  'ряда совпала с цифрой в том же разряде правил'
                                                                  'ьного ответа, '
                                                                  'это называется "быком". Если указанная цифра '
                                                                  'есть в ответе, но на неверной'
                                                                  ' позиции, это "корова". Загадывающий отвечает,'
                                                                  ' сколько "быков" и "коров" '
                                                                  'в числе угадывающего.\nПример -- числа\n8536\n'
                                                                  '6573\nУ них 1 "бык" (это цифра 5) и 2 "коровы"'
                                                                  ' (это цифры 3 и 6).\n\n'
                                                                  'Вы собираетесь просто отгадывать; играть'
                                                                  ' против бота(одновременно загадывать свое число '
                                                                  'и отгадывать его);'
                                                                  ' или вы не собираетесь играть?\nЧтобы ответи'
                                                                  'ть, введите'
                                                                  ' один из следующих вариантов: '
                                                                  ' 1  |  2  |  /стоп\n'
                                                                  '\nЕсли вы '
                                                                  'пожелаете прекратить игру, то в любой'
                                                                  ' момент введите команду "/стоп"')

            async def bnc_user_input(history=None):
                # пользовательский ввод для игры быки и коровы
                user_try = await self.wait_for('message', check=check)
                user_try = user_try.content
                # здесь находятся комбинации цифр, начинающиеся с 0.
                zero_digitalis = ['0' + str(digital) for digital in range(100, 1000)]
                while user_try != '/стоп' and (len(set(list(user_try))) != 4 or user_try not in
                                               (zero_digitalis + [str(d) for d in range(1000, 10000)])):
                    if history is not None and user_try == '/история':
                        history_read = ''
                        for p in history:
                            b, c = Bnc.bulls_n_cows_morph(p[1], p[2])
                            # в f строке нельзя напрямую вызвать метод split() с аргументом '\n',
                            # поэтому аргументом будет служить переменная со значением '\n'
                            delimiter = '\n'
                            history_read += f'\nПопытка {str(len(history_read.split(delimiter)) + 1)}.' \
                                            f' Ваше число {str(p[0])} -- {b} и {c}.'
                        await message.channel.send(user_player + ', это история ваших попыток.' + history_read)
                    await message.channel.send(user_player + ', введите четырехзначное число'
                                                             ' с неповторяющимися цифрами или команду "/стоп",'
                                                             ' чтобы прекратить игру.')
                    user_try = await self.wait_for('message', check=check)
                    user_try = user_try.content
                return user_try

            choice = await self.wait_for('message', check=check)
            while choice.content not in ('1', '2', '/стоп'):
                await message.channel.send(user_player + ', чтобы ответить,'
                                                         ' введите один из следующих вариантов: \n1\n2\n/стоп')
                choice = await self.wait_for('message', check=check)
            if choice.content == '/стоп':
                # игрок отказался играть. В конце блока игры его статус автоматически поменяется.
                pass
            elif choice.content == '1':
                # генерируем число, выводим быки и коровы, пока игрок не выиграет
                answer = Bnc.generate_answer()
                await message.channel.send('Вы в одиночной игре, ' + user_player + '! Бот уже загадал число,'
                                                                                   ' попробуйте угадать его.'
                                                                                   ' Введите четырехзначное число'
                                                                                   ' с неповторяющимися цифрами.')
                win = False
                number = 1
                user_input = await bnc_user_input()
                # количество попыток
                while not win:
                    if user_input == '/стоп':
                        break
                    bulls_count, cows_count = Bnc.bulls_n_cows(user_input, answer)
                    bulls, cows = Bnc.bulls_n_cows_morph(bulls_count, cows_count)
                    await message.channel.send(user_player + f"\n{number} попытка. Ваше число {user_input}."
                                                             f" У вас {bulls} и {cows}.")
                    if bulls_count == 4:
                        win = True
                        break
                    else:
                        await message.channel.send('Введите четырехзначное число с неповторяющимися цифрами.')
                        user_input = await bnc_user_input()
                        number += 1
                if win:
                    morph = pymorphy2.MorphAnalyzer()
                    await message.channel.send('Невероятная победа, ' + user_player + '! Вы сделали это'
                                                                                      ' всего за ' + str(number)
                                               + ' ' +
                                               morph.parse('попытку')[0].make_agree_with_number(number).word + '.')
                await message.channel.send('Игра окончена.')
            else:
                await message.channel.send(user_player + ', вы играете против бота. Для того, чтобы решить,'
                                                         ' кто будет ходить первым, бот использует бинарную'
                                                         ' монетку. Выберите 0 или 1.\nВо время вашего хода также'
                                                         ' будет доступна команда "/история", эта команда покажет'
                                                         ' все ваши попытки и ответы соперника.')
                # определяет, кто ходит первым.
                bin_coin = str(random.choice((0, 1)))
                choice = await self.wait_for('message', check=check)
                while choice.content not in ('1', '0', '/стоп'):
                    await message.channel.send(user_player + ', выберите\n0\tили\t1\n Для прекращения игры '
                                                             'напишите команду "/стоп"')
                    choice = await self.wait_for('message', check=check)
                # объект класса Быки и Коровы, в игре против бота используются все его функции.
                game = Bnc()
                # 0 означает, что игра в процессе. 1 - что игрок победил. 2 - что победил бот.
                # -1 - что игра была прервана потому, что игрок жульничал, или потому, что он ее прервал.
                playing = 0
                # True, если сейчас ход игрока
                player_turn = False
                # ведет подсчет попыток игрока
                if choice.content == '/стоп':
                    playing = -1
                elif choice.content == bin_coin:
                    player_turn = True
                    await message.channel.send('Вы угадали, ' + user_player + '.')
                else:
                    await message.channel.send('Вы не угадали, ' + user_player + '. ')
                # игра длится до остановки командой или победы одной из сторон
                while playing == 0:
                    if player_turn:
                        await message.channel.send(user_player + ', введите четырехзначное число '
                                                                 'с неповторяющимися цифрами. Также вы можете'
                                                                 ' ввести команду "/история".')
                        user_input = await bnc_user_input(history=game.history)
                        if user_input == '/стоп':
                            playing = -1
                            break
                        bulls_count, cows_count = game.bulls_n_cows(user_input, game.answer)
                        # считаем быков и коров, и, если они подходят под условие, генерируем число заново,
                        # в связи с историей попыток.
                        if bulls_count >= 2 or cows_count >= 3 or bulls_count + cows_count in (4, 0):
                            game.cheat()
                        bulls_count, cows_count = game.bulls_n_cows(user_input, game.answer)
                        # добавляем в историю попытку и ее результаты
                        game.history.append([user_input, bulls_count, cows_count])
                        bulls, cows = game.bulls_n_cows_morph(bulls_count, cows_count)
                        await message.channel.send(user_player + f"\nВаша {len(game.history)} попытка. Ваше число"
                                                                 f" {user_input}. У вас {bulls} и {cows}.")
                        if bulls_count == 4:
                            # игрок победил
                            await message.channel.send('Вы победили, ' + user_player + '! Я загадал число '
                                                       + str(game.answer))
                            playing = 1
                        player_turn = False
                    else:
                        guess = None
                        while True:
                            if len(game.guess_space) == 0:
                                await message.channel.send(user_player + ', вы попытались обмануть бота. '
                                                                         'Вы проиграли.')
                                playing = -1
                                break
                            guess = random.choice(list(game.guess_space))
                            game.guess_space.remove(guess)
                            if game.is_compatible(guess):
                                break
                        # если бот обнаружил, что игрок жульничает - прерываем игру
                        if playing != 0:
                            break
                        await message.channel.send(user_player + ', я думаю, что вы загадали число '
                                                   + str(guess) + '\nВведите через пробел количество быков и коров.')
                        bulls_n_cows = await self.wait_for('message', check=check)
                        bulls_n_cows = bulls_n_cows.content.split(' ')
                        while len(bulls_n_cows) != 2 or not all(j in [str(d) for d in range(0, 5)]
                                                                for j in bulls_n_cows) \
                                or sum([int(c) for c in bulls_n_cows]) > 4:
                            if bulls_n_cows == ['/стоп']:
                                playing = -1
                                break
                            await message.channel.send(user_player + ', введите через пробел количество'
                                                                     ' "быков" и "коров".\nЕсли в названном числе '
                                                                     'цифра какого-то разряда совпала с цифрой'
                                                                     ' в том же разряде правильного ответа, эт'
                                                                     'о называется "быком". Если указанная циф'
                                                                     'ра есть в ответе, но на неверной позиции,'
                                                                     ' это "корова". Пример -- у чисел 1234 и 5631 '
                                                                     ' 1 "бык" (это цифра 3) и 1 "корова"'
                                                                     ' (это цифра 1). Сумма "быков" и "коров" не может'
                                                                     ' быть больше 4.')
                            bulls_n_cows = await self.wait_for('message', check=check)
                            bulls_n_cows = bulls_n_cows.content.split(' ')
                        # это условие приходится дублировать из-за того, что во время хода бота 2 варианта
                        # прерывания игры. 1 - игрок жульничал. 2 - игрок прервал игру. В обоих случаях игра
                        # должна прекратиться незамедлительно.
                        if playing != 0:
                            break
                        game.historys.append((guess, int(bulls_n_cows[0]), int(bulls_n_cows[1])))
                        bulls, cows = game.bulls_n_cows_morph(bulls_n_cows[0], bulls_n_cows[1])
                        await message.channel.send(user_player + f"\nМоя {len(game.history)} попытка. Мое число"
                                                                 f" {guess}. У меня {bulls} и {cows}.")
                        if bulls_n_cows[0] == 4:
                            # бот победил
                            await message.channel.send('Бот победил, ' + user_player + '! Вы загадали число '
                                                       + str(guess))
                            playing = 2
                        player_turn = True
                if playing != -1:
                    await message.channel.send('Спасибо за игру! Заходите еще!')
                else:
                    await message.channel.send('Игра окончена.')
            await self.db_edit(user_gambler.name + user_gambler.discriminator, 'empty')
        elif message.content == '/кости':
            await self.db_edit(message.author.name + message.author.discriminator, 'dices')
            # это нужно, чтобы отслеживать сообщения именно от данного пользователя
            user_gambler = message.author
            user_player = str(user_gambler)
            await message.channel.send('Хорошо, ' + user_player + '! Правила таковы -- у вас ровно 100 монет. Вам нужно'
                                                                  ' увеличить их количество. На каждый бросок можно с'
                                                                  'делать ставку, от 5 до 20 монет. Ставка делается '
                                                                  'на сумму цифр, которые будет на верхн(их/ей) гран(я'
                                                                  'х/и) кост(ей/и) после броска. Также вы можете '
                                                                  'выбрать какие кости будете бросать. Кости каждый р'
                                                                  'аз выбираются случайно, из следующих вариантов:'
                                                                  '\n\tодна шестигранная кость, коэффициент ставки - 3.'
                                                                  '\n\tдве шестигранные кости коэффициент ставки - 6'
                                                                  '\n\tодна восьмигранная кость, коэффициент ставки - '
                                                                  '4\n\tдве восьмигранные кости, коэффициент ставки - '
                                                                  '8\n\tодна двадцатигранная кость,'
                                                                  ' кожффициент ставки - 10\nТакже вам всегда будет д'
                                                                  'оступна моентка со стабильным коэффициентом 2.\n'
                                                                  'Коэффициент ставки - это то число, на которое '
                                                                  'будет умножена ваша ставка. При проигрыше у вас '
                                                                  'вычтут вашу ставку. Но есть одно условие - ,'
                                                                  ' все коэффициенты, кроме стабильного, варируются'
                                                                  ' от 2 до самих себя.\nЕсли вы будете'
                                                                  ' играть, то выберите число, которого хотите '
                                                                  'достигнуть, из нижеперечисленных. В противном случ'
                                                                  'ае, напишите команду "/стоп"\n'
                                                                  '200  |  300  |  500  |  1000  |  /стоп')
            choice = await self.wait_for('message', check=check)
            while choice.content not in ('200', '300', '/стоп', '500', '1000'):
                await message.channel.send(user_player + ', чтобы ответить,'
                                                         ' введите один из следующих вариантов: \n200\n300\n500\n100'
                                                         '0\n/стоп')
                choice = await self.wait_for('message', check=check)
            if choice.content == '/стоп':
                # игрок отказался играть. В конце блока игры его статус автоматически поменяется.
                pass
            else:
                start_cash = 100
                end_cash = int(choice.content)
                dash_set = {'один шестигранник': 3,
                            'два шестигранника': 6,
                            'один восьмигранник': 4,
                            'два восьмигранника': 8,
                            'один двадцатигранник': 10}
                values = {'один шестигранник': range(1, 7),
                          'два шестигранника': range(2, 13),
                          'один восьмигранник': range(1, 9),
                          'два восьмигранника': range(2, 17),
                          'один двадцатигранник': range(1, 21),
                          'монета': range(1, 3)}
                d2_used = False
                while start_cash != 0 or start_cash != end_cash:
                    random.seed(random.randint(10 ** 10, 10 ** 20))
                    cur_set = [random.choice([d for d in dash_set.keys()]) for _ in range(2)]
                    for i in range(len(cur_set)):
                        while cur_set.count(cur_set[i]) > 1:
                            del cur_set[i]
                            cur_set.append(random.choice([d for d in dash_set.keys()]))
                        cur_set[i] = f'{i + 1}){cur_set[i]} -- {str(random.randint(2, dash_set[cur_set[i]]))}'
                    if not d2_used:
                        cur_set.append('3)монета -- 2')
                    else:
                        d2_used = False
                    await message.channel.send(user_player + f'. Ваши монеты: {start_cash}, осталось набрать ещё '
                                                             f'{end_cash - start_cash} монет.\n Вы можете кинуть '
                                                             f'следующие кости:\n\t' + '\n\t'.join(cur_set)
                                               + '\nМожно ввести или наименование варианта, или его номер.')
                    user_move = await self.wait_for('message', check=check)
                    while all([user_move.content != c.split(' -- ')[0][2:] for
                               c in cur_set]) and user_move.content not in ['1', '2', '3'] + ['/стоп']:
                        await message.channel.send(user_player + ', чтобы ответить, введите наименование одного из'
                                                                 ' следующих вариантов:\n\t' + '\n\t'.join(cur_set) +
                                                   '\nили номер варианта, от 1 до 3.\nТакже вы можете прервать игру'
                                                   ' командой "/стоп"')
                        user_move = await self.wait_for('message', check=check)
                    dice = user_move.content
                    if dice == '/стоп':
                        break
                    if dice not in ['1', '2', '3']:
                        dice = str([d.split(' -- ')[0][2:] == dice for d in cur_set].index(True) + 1)
                    if dice == '3':
                        d2_used = True
                    coefficient = int(cur_set[int(dice)][-1])
                    await message.channel.send(user_player + ', теперь выберите число, на которое будете делать ставку.'
                                                             ' Число не может превышать максимальную сумму цифр костей'
                                                             ', или быть меньше 1 (или 2 если костей две).')
                    digit = await self.wait_for('message', check=check)
                    sums = [str(b) for b in values[cur_set[int(dice) - 1].split(' -- ')[0][2:]]]
                    while digit not in sums or digit != '/стоп':
                        await message.channel.send(user_player + ', выберите число, на которое будете делать ставку.'
                                                                 ' Введите любое число из следуюших:  ' +
                                                   ',  '.join(sums) + '\nТакже вы можете прервать игру командой '
                                                                      '"/стоп"')
                        digit = await self.wait_for('message', check=check)
                    if digit == '/стоп':
                        break
                    await message.channel.send(f'Отлично, {user_player}, а теперь введите ставку. Ставкой может быть '
                                               f'любое число от 5 до 20 включительно.')
                    bet = await self.wait_for('message', check=check)
                    while bet not in [str(b) for b in range(5, 21)] or bet != '/стоп':
                        await message.channel.send(user_player + ', введите ставку. Ставкой может быть любое число из'
                                                                 ' следующих: ' + ', '.join(range(5, 21)))
                        bet = await self.wait_for('message', check=check)
                    if bet == '/стоп':
                        break
                    await message.channel.send(f'{user_player}, вы сделали ставку {bet} монет на число {digit}.'
                                               f' Бот бросает кости...\n И выбрасывает число {random.randint(sums)}.')
                    if int(digit) != sums:
                        await message.channel.send(f'Жаль, {user_player}, вы не угадали и лишились {bet} монет.')
                        start_cash -= bet
                    else:
                        await message.channel.send(f'Вы угадали, {user_player}! Ваш выигрыш составляет '
                                                   f'{coefficient * bet} монет(а).')
                        start_cash += coefficient * bet
                if start_cash <= 0:
                    await message.channel.send(f'Вы проиграли, {user_player}. Но это не повод для огорчения,'
                                               f' ведь смысл этой игры не в победах или поражениях, а в самой игре.'
                                               f' Каждый проигрыш или победа чему-то учат.')
                if start_cash == end_cash:
                    await message.channel.send(f'Поздравляю, {user_player}, вы победили! Заходите еще!')
            await self.db_edit(user_gambler.name + user_gambler.discriminator, 'empty')

    async def db_edit(self, user_id, status):
        # функция заносит игрока в базу данных, или изменяет статус, если он там уже есть.
        cur = self.con.cursor()
        user = cur.execute("Select * from users WHERE user_id=?", (user_id,)).fetchone()
        if user is None:
            cur.execute('INSERT INTO users(user_id, state) VALUES(?, ?)', (str(user_id), status))
        else:
            cur.execute('UPDATE users SET state = "' + status + '" WHERE user_id = "' + str(user_id) + '"')
        self.con.commit()

    def user_status(self, user_id):
        # получение статуса пользователя
        cur = self.con.cursor()
        user = cur.execute("Select * from users WHERE user_id=?", (user_id,)).fetchone()
        if user is None:
            return 'empty'
        return user[1]

    async def on_ready(self):
        cur = self.con.cursor()
        users = cur.execute("Select * from users").fetchall()
        for i in users:
            cur.execute('UPDATE users SET state = "empty" WHERE user_id = "' + str(i[0]) + '"')
        self.con.commit()


client = Fraudbot()
client.run(TOKEN)
