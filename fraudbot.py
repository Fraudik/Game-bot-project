import discord
import sqlite3
import random
import requests
import pymorphy2
from itertools import product
# база, в которой будут храниться заработанные очки и статус отношений бота с пользователем - играет оно и во что,
# или просто общается


class Bnc:
    def __init__(self):
        random.seed(self.generate_answer())
        self.attempt = self.k = 0
        # создаем список всех возможных чисел.
        self.everything = ["".join(x) for x in product('0123456789', repeat=4)
                           if len(set(x)) == len(x)]
        self.answer = self.generate_answer()
        # таким образом мы еще и перемешиваем все числа. кроме того, из массива их удобнее удалять.
        self.guess_space = set(self.everything)
        # здесь храним историю попыток бота.
        self.historys = []
        # а здесь храним историю попыток игрока.
        self.history = []

    def is_compatible(self, guess):
        # проверка на то, подходит ли нам это число, на основе всех предыдущих попыток.
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
        # возвращает быков и коров в более удобной форме для передачи игроку.
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

    def cheat(self, player_try):
        max_score = 0
        best_answer = self.answer
        for new_answer in self.everything:
            score = 12.0
            error = True
            while error:
                if self.history:
                    for i in self.history:
                        if self.bulls_n_cows(i[0], new_answer) != [i[1], i[2]]:
                            score = 0
                            error = False
                            break
                        error = False
                else:
                    break
            bulls, cows = self.bulls_n_cows(new_answer, player_try)
            score -= bulls * 3 + cows
            if bulls + cows == 0:
                score -= 5.1
            if max_score < score:
                best_answer = new_answer
                max_score = score
        return best_answer


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
                                       'здесь описаны мои игры и команды для их вызова.\nКоманда "/помощь" -- '
                                       'используйте ее, если возникнут вопросы или проблемы.',
                            '/помощь': 'Если у вас возник вопрос, проблема, или у вас есть какая-то идея'
                                       ' -- пишите на адрес fraudbot.help@mail.ru'}
        self.commands = ['/помощь', '/игры', '/привет'] + [g.split(' - ')[0] for g in games.split('\n')]
        # после перезапуска бот должен будет предупредить пользователей, что все их диалоги были прекращены.
        self.reconnect = {}

    async def on_message(self, message):
        # не даем отвечать самому себе
        if message.author == self.user:
            return
        # user_gambler - объект класса Member и служит для проверки в функции check(m).
        user_gambler = message.author
        # user_player - идентификатор пользователя, нужен для обращения к нему и для занесения в базу.
        user_player = str(user_gambler).replace('#', '')
        # user_channel - канал, на котором был запущено общение.
        user_channel = message.channel
        # в базе данных лежит имя сервера и канал. если пользователь общается с ботом в личных сообщениях,
        # то сервера нет и мы записываем только канал.
        try:
            user_chan_guild = str(user_channel.guild.id) + str(user_channel.id)
        except AttributeError:
            user_chan_guild = str(user_channel.id)
        # прекращает все взаимодействия с ботом по команде.
        if message.content == '/стоп':
            await self.db_edit(user_player, 'empty')
            await message.channel.send(user_player + ", вы прервали все взаимодействия с ботом.")
        # если бот был запущен первый раз, или перезапущен
        if user_player in self.reconnect and self.reconnect[user_player]:
            # 1 условие проверяет, что пользователь уже общался с ботом
            await message.channel.send(f"Извините, {user_player}, произошел перезапуск бота. Приносим извинения"
                                       f" за причиненные неудобства. Все диалоги были досрочно прекращены.")
        # если пользователя нет в базе
        if self.user_status(user_player) == 'None':
            # поприветствуем нового пользователя и добавим его в базу. Добавление в базу происходит автоматически,
            await message.channel.send(f'Приветствую, {user_player}! Я Fraudbot и у меня 3 основных команды:\n\t/'
                                       f'привет\t|\t/игры\t|\t/помощь\nВы можете отправить любую из них. Более '
                                       f'подробное приветствие уже отправлено вам в личные сообщения.')
            # также отправляем ему сообщение в личный канал.
            await self.pm_greet(user_gambler)
            # вместе со сменой статуса в конце функции. Но пользователь мог первым сообщением сразу отправить команду
            # и поэтому статус меняется перед проверкой на то, что сообщение является командой.
            await self.db_edit(user_player, 'empty')
        # если пользователь "свободен" от наших игр или диалога
        if self.user_status(user_player) == 'empty':
            for i in self.dialog_base:
                if message.content == i:
                    await message.channel.send(self.dialog_base[i])
        # если игрок не "свободен", и при этом пишет с другого канала - говорим ему об этом
        # и не даем запустить еще один процесс.
        else:
            # также проверяем - не написал ли он в другой чат просто так, не нам.(проверка на наличие нашей команды)
            if self.user_status(user_player, get_channel=True) != "None" and user_chan_guild != \
                    self.user_status(user_player, get_channel=True) and message.content in self.commands:
                await message.channel.send(user_player + ', вы уже ведете диалог с ботом на другом канале.'
                                                         ' Завершите его, или прервите командой "/стоп".')
            # не даем еще раз запустить цикл, даже в случае, если он вызвал команду с того же сервера,
            # где он "занят".
            return

        def check(m):
            # проверяем, что точно сообщение от нашего игрока и что он не случайно нажал enter
            # также не дает случиться путанице с множеством каналов.
            return len(m.content) != 0 and m.author == user_gambler and m.channel == user_channel
        # запуск игры "Быки и Коровы>"
        if message.content == '/быки и коровы':
            await self.db_edit(message.author.name + message.author.discriminator, 'bnc', user_chan_guild)
            # это нужно, чтобы отслеживать сообщения именно от данного пользователя
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
                            history_read += f'\nПопытка {str(len(history_read.split(delimiter)))}.' \
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
                            game.cheat(user_input)
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
                                                   + str(guess) + '\nВведите через пробел количество быков и коров.'
                                                                  ' (например -- 0 2)')
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
                        await message.channel.send(user_player + f"\nМоя {len(game.history) + 1} попытка. Мое число"
                                                                 f" {guess}. У меня {bulls} и {cows}.")
                        if bulls_n_cows[0] == 4:
                            # бот победил
                            await message.channel.send('Бот победил, ' + user_player + '! Вы загадали число '
                                                       + str(guess))
                            playing = 2
                        player_turn = True
                if playing != -1:
                    await message.channel.send('Спасибо за игру! Если вы желаете еще поиграть --'
                                               ' введите команду "/игры".')
            await message.channel.send(f'Игра окончена, {user_player}. Если желаете еще раз сыграть в эту или'
                                       f' иную игру -- введите команду "/игры".')
        # запуск игры "Кости"
        elif message.content == '/кости':
            # изменение статуса.
            await self.db_edit(message.author.name + message.author.discriminator, 'dices', user_chan_guild)
            # объяснение правил игры
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
                                                                  ' коэффициент ставки - 10\nТакже вам всегда будет д'
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
            # проверка на правильный ввод
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
                # начальные и стартовые суммы, словарь названий костей и их коэффициентов.
                dash_set = {'один шестигранник': 3,
                            'два шестигранника': 6,
                            'один восьмигранник': 4,
                            'два восьмигранника': 8,
                            'один двадцатигранник': 10}
                # все возможные результаты бросков для разных наборов костей.
                values = {'один шестигранник': range(1, 7),
                          'два шестигранника': range(2, 13),
                          'один восьмигранник': range(1, 9),
                          'два восьмигранника': range(2, 17),
                          'один двадцатигранник': range(1, 21),
                          'монета': range(1, 3)}
                # использовалась ли монета в прошлый раз.
                d2_used = False
                # пока игрок не проиграет, или не выиграет.
                while start_cash != 0 or start_cash != end_cash:
                    # экспериментальным путем было определено, что именно такая генерация
                    random.seed(random.randint(10 ** 10, 10 ** 20))
                    # те наборы кубиков, которые буду предоставлены игроку в этот раз.
                    cur_set = [random.choice([d for d in dash_set.keys()]) for _ in range(2)]
                    for i in range(len(cur_set)):
                        # устранение и замена дупликатов.
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
                    # проверка на правильный ввод.
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
                        # если было указано наименование, то узнаем его номер.
                        dice = str([d.split(' -- ')[0][2:] == dice for d in cur_set].index(True) + 1)
                    if dice == '3':
                        d2_used = True
                    coefficient = int(cur_set[int(dice) - 1][-1])
                    await message.channel.send(user_player + ', теперь выберите число, на которое будете делать ставку.'
                                                             ' Число не может превышать максимальную сумму цифр костей'
                                                             ', или быть меньше 1 (или 2 если костей две).')
                    digit = await self.wait_for('message', check=check)
                    # получаем все числа, на которые можно делать ставки.
                    sums = [str(b) for b in values[cur_set[int(dice) - 1].split(' -- ')[0][2:]]]
                    # проверяем ввод
                    while digit.content not in sums and digit.content != '/стоп':
                        await message.channel.send(user_player + ', выберите число, на которое будете делать ставку.'
                                                                 ' Введите любое число из следуюших:  ' +
                                                   ',  '.join(sums) + '\nТакже вы можете прервать игру командой '
                                                                      '"/стоп"')
                        digit = await self.wait_for('message', check=check)
                    if digit.content == '/стоп':
                        break
                    await message.channel.send(f'Отлично, {user_player}, а теперь введите ставку. Ставкой может быть '
                                               f'любое число от 5 до 20 включительно.')
                    bet = await self.wait_for('message', check=check)
                    # проверяем корректность ставки. Существует возможность сделать ставку и уйти в минус,
                    # в полном соответствии с правилами игры, которые были предоставлены пользователю.
                    while bet.content not in [str(b) for b in range(5, 21)] and bet.content != '/стоп':
                        await message.channel.send(user_player + ', введите ставку. Ставкой может быть любое число из'
                                                                 ' следующих: ' + ', '.join([str(g) for g in
                                                                                             range(5, 21)]))
                        bet = await self.wait_for('message', check=check)
                    if bet.content == '/стоп':
                        break
                    # бросок костей.
                    cast = random.choice(sums)
                    await message.channel.send(f'{user_player}, вы сделали ставку {bet.content} монет на число '
                                               f'{digit.content}. Бот бросает кости...\nИ выбрасывает число'
                                               f' {cast}.')
                    if digit.content != cast:
                        await message.channel.send(f'Жаль, {user_player}, вы не угадали и лишились {bet.content} монет.')
                        start_cash -= int(bet.content)
                    else:
                        await message.channel.send(f'Вы угадали, {user_player}! Ваш выигрыш составляет '
                                                   f'{coefficient * int(bet.content)} монет(а).')
                        start_cash += coefficient * int(bet.content)
                if start_cash <= 0:
                    await message.channel.send(f'Вы проиграли, {user_player}. Но это не повод для огорчения,'
                                               f' ведь смысл этой игры не в победах или поражениях, а в самой игре.'
                                               f' Каждый проигрыш или победа чему-то учат.')
                if start_cash == end_cash:
                    await message.channel.send(f'Поздравляю, {user_player}, вы победили!')
                await message.channel.send(f'Игра окончена, {user_player}. Если вы желаете сыграть еще '
                                           f'-- введите команду "/игры".')
        await self.db_edit(user_player, 'empty')

    async def db_edit(self, user_id, status, channel='None'):
        # функция заносит игрока в базу данных, или изменяет статус, если он там уже есть.
        cur = self.con.cursor()
        # на сервере идентификатор содержит #, а в личных сообщениях нет. Не даем дублировать записи.
        user = cur.execute("Select * from users WHERE user_id=?", (user_id,)).fetchone()
        if user is None:
            cur.execute('INSERT INTO users(user_id, state, channel) VALUES(?, ?, ?)', (str(user_id), status, channel))
        else:
            cur.execute(f'UPDATE users SET state = "{status}", channel = "{channel}" WHERE user_id = "'
                        + str(user_id) + '"')
        self.con.commit()

    def user_status(self, user_id, get_channel=False):
        # получение статуса пользователя.
        cur = self.con.cursor()
        user = cur.execute("Select * from users WHERE user_id=?", (user_id.replace('#', ''),)).fetchone()
        if user is None:
            return 'None'
        if get_channel:
            return user[2]
        return user[1]

    async def on_ready(self):
        # при перезапуске все статусы сбрасываются, а при первом запуске ничего не просходит,
        # так как в базе нет пользователей.
        cur = self.con.cursor()
        users = cur.execute("Select * from users").fetchall()
        for i in users:
            cur.execute('UPDATE users SET state = "empty", channel = "None" WHERE user_id = "' + str(i[0]) + '"')
            self.reconnect[i[0]] = True
        self.con.commit()

    async def on_member_join(self, member):
        # отправляем новому на сервере пользователю сообщение.
        await self.pm_greet(member)

    async def pm_greet(self, member):
        # приветствие мы отправляем только в том случае, если пользователя нет в базе.
        if self.user_status(str(member)) == 'None':
            await member.create_dm()
            await member.dm_channel.send(self.dialog_base['/привет'])
            await member.dm_channel.send('Вы можете общаться со мной как на общем канале, так и здесь. Eще у меня'
                                         ' есть команда "/помощь". Отправьте ее мне, если понадобится помощь.')


client = Fraudbot()
client.run(open('token.txt', 'r').readline())
