import sys
from PyQt6.QtGui import QIcon, QFontDatabase, QFont, QPalette, \
    QColor
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt6.QtWidgets import QPushButton, QGridLayout, QLabel, QLCDNumber, \
    QLineEdit, QInputDialog, QMessageBox, QTableView, QHeaderView
from PyQt6.QtSql import QSqlDatabase, QSqlQueryModel
from random import randrange
from PyQt6 import uic
import sqlite3
import csv

# контекстный менеджер для удобного раскрытия csv файла с медиа
with open('photo.csv', encoding='utf8') as csvfile:
    reader = csv.reader(csvfile, delimiter=';', quotechar='"')
    reader = {i[0]: i[1] for i in reader}


class LoginError(Exception):
    pass


class PasswordError(Exception):
    pass


class Registration(QMainWindow):
    def __init__(self):
        super().__init__()
        # ---------------- загрузка UI и бд
        uic.loadUi(reader['registr_menu'], self)
        self.con = sqlite3.connect('MinesweeperDB.db')
        self.cur = self.con.cursor()

        # ---------------- UI настройка/инициализация
        custom_font = font_set()
        app.setFont(custom_font)
        self.in_login.setEnabled(False)
        self.in_password.setEnabled(False)
        self.in_dal.setEnabled(False)
        self.log_in_checkbox.setEnabled(False)
        self.in_login.setFont(custom_font)
        self.in_password.setFont(custom_font)
        self.registration_login.setFont(custom_font)
        self.registration_password.setFont(custom_font)
        reg_b = self.regist_checkbox
        in_b = self.log_in_checkbox
        self.menu = None

        # ---------------- настройка сигналов кнопок
        self.choi_registration_bt.clicked.connect(self.regist_visible)
        self.choi_in_bt.clicked.connect(self.log_in_visible)
        self.registration_dal.clicked.connect(self.regist_logic)
        self.in_dal.clicked.connect(self.log_in)

        # ---------------- настройка сигналов чекбоксов, открывающих пароль
        # в метод передается состояние чекбокса и сама ссылка на него
        self.regist_checkbox.stateChanged.connect(
            lambda sel, x=reg_b: self.echo_mode(sel, x))
        self.log_in_checkbox.stateChanged.connect(
            lambda sel, x=in_b: self.echo_mode(sel, x))

    def regist_visible(self):
        # ---------------- настройка виджетов при включении режима регистрации
        self.in_login.setEnabled(False)
        self.in_password.setEnabled(False)
        self.in_dal.setEnabled(False)
        self.log_in_checkbox.setEnabled(False)
        self.log_in_checkbox.setChecked(False)
        self.regist_checkbox.setEnabled(True)
        self.registration_login.setEnabled(True)
        self.registration_password.setEnabled(True)
        self.registration_dal.setEnabled(True)
        self.in_error.setText('')
        self.in_password.setText('')
        self.in_login.setText('')

    def log_in_visible(self):
        # ---------------- настройка виджетов при включении режима входа
        self.registration_login.setEnabled(False)
        self.registration_password.setEnabled(False)
        self.registration_dal.setEnabled(False)
        self.regist_checkbox.setEnabled(False)
        self.regist_checkbox.setChecked(False)
        self.log_in_checkbox.setEnabled(True)
        self.in_login.setEnabled(True)
        self.in_password.setEnabled(True)
        self.in_dal.setEnabled(True)
        self.registration_error.setText('')
        self.registration_password.setText('')
        self.registration_login.setText('')

    def regist_logic(self):
        # проверка, написано ли что-то в выводе ошибки, получение логина/пароля
        if self.registration_error.text() != '':
            self.registration_error.setText('')
        login = self.registration_login.text()
        password = self.registration_password.text()

        # проверка на заполненность строчек логина/пароля
        if login == '':
            self.registration_error.setText('Введите логин')
        elif password == '':
            self.registration_error.setText('Введите пароль')
        else:

            # проверка по правилам написания логина пароля
            # логин попадает в функцию вне класса validator_check, возвращает
            # True, если ник написан по всем правилам. Проходит проверка пароля
            # на длину символа.
            try:
                if not validator_check(login):
                    raise LoginError()
                if len(password) < 5:
                    raise PasswordError()
            except LoginError:
                self.registration_error.setText(
                    'Логин не соответствует правилам')
                return
            except PasswordError:
                self.registration_error.setText(
                    'Пароль должен содержать не менее 5 символов')
                return

            # после всех проверок мы вытаскиваем из бд строчку по нику, который
            # ввел пользователь. Сделано это для того, чтобы если что
            # перезаписать
            # удаленный аккаунт. Если None - значит создаем новый аккаунт,
            a = self.cur.execute('''SELECT name, is_deleted FROM users
                WHERE name = ?''', (login,)).fetchone()
            if a is not None:

                # Если аккаунт удален (is_deleted = 1) - перезаписываем
                if a[1]:
                    self.cur.execute('''UPDATE users
                        SET
                        password = ?,
                        is_deleted = ?
                        WHERE name = ?''', (password, False, login))
                else:
                    self.registration_error.setText(
                        'Данный логин уже существует')
                    return
            else:

                # аккаунта с таким ником никогда не было, записываем данные в
                # таблицу с пользователями и с результатами игр
                self.cur.execute(
                    '''\
INSERT INTO users(name, password, is_deleted) VALUES(?, ?, ?)''',
                    (login, password, False))

                # запись в таблицу с результатами (изначально
                # результаты = Null)
                self.cur.execute(
                    '''\
    INSERT INTO game(user_id, easy, medium, hard) VALUES((SELECT id FROM users
                        WHERE name = ?), Null, Null, Null)''',
                    (login,))

            # сохраняем все изменения
            self.con.commit()

            # переходим в окно меню, показав новое окно и скрыв старое
            self.menu = Menu(login)
            self.menu.show()
            self.hide()

    def log_in(self):
        # проверка, написано ли что-то в выводе ошибки, получение логина/пароля
        if self.in_error.text() != '':
            self.in_error.setText('')
        login = self.in_login.text()
        password = self.in_password.text()

        # проверка на заполненность строчек логина/пароля
        if login == '':
            self.in_error.setText('Введите логин')
        elif password == '':
            self.in_error.setText('Введите пароль')
        else:

            # после проверок вызываем из бд данные о пользователе
            info = self.cur.execute('''SELECT name, password, \
is_deleted FROM users
            WHERE name = ?''', (login,)).fetchone()

            # если логина в бд не существует (None) - выдаем ошибку,
            # или если аккаунт удален
            if info is None or info[2]:
                self.in_error.setText('Логин не обнаружен')
            else:

                # проверка на правильный пароль
                if info[1] != password:
                    self.in_error.setText('Неверный пароль')
                else:

                    # переходим в окно меню, показав новое окно и скрыв старое
                    self.menu = Menu(login)
                    self.menu.show()
                    self.hide()

    def echo_mode(self, state, checkbox):

        # метод показа/скрытия пароля. если checkbox равен чекбоксу
        # регистрации - работаем с паролем регистрации, иначе с паролем входа
        if checkbox == self.regist_checkbox:

            # если чекбокс включен (state = True) - показываем пароль,
            # иначе скрываем
            if state:
                self.registration_password.setEchoMode(
                    QLineEdit.EchoMode.Normal)
            else:
                self.registration_password.setEchoMode(
                    QLineEdit.EchoMode.Password)
        else:

            # если чекбокс включен (state = True) - показываем пароль,
            # иначе скрываем
            if state:
                self.in_password.setEchoMode(
                    QLineEdit.EchoMode.Normal)
            else:
                self.in_password.setEchoMode(
                    QLineEdit.EchoMode.Password)


class Menu(QMainWindow):
    def __init__(self, login):
        super().__init__()
        # ---------------- загрузка UI
        uic.loadUi(reader['menu'], self)

        # ---------------- UI настройка/инициализация
        custom_font = font_set()
        app.setFont(custom_font)
        self.login = login
        self.start_but.setFont(custom_font)
        self.leader_but.setFont(custom_font)
        self.rules_but.setFont(custom_font)
        self.profile_but.setFont(custom_font)
        self.exit_but.setFont(custom_font)
        self.start = None
        self.profile = None
        self.exit = None
        self.rules = None
        self.leader = None

        # ---------------- настройка сигналов кнопок + приветствие пользователя
        self.start_but.clicked.connect(self.start_window)
        self.profile_but.clicked.connect(self.profile_window)
        self.exit_but.clicked.connect(self.exit_window)
        self.rules_but.clicked.connect(self.rules_window)
        self.leader_but.clicked.connect(self.leader_window)
        self.welcome_label.setText(f'Добро пожаловать, {self.login}!')

    def start_window(self):
        # переходим в окно старта игры, показав новое окно и скрыв старое
        self.start = Start(self.login)
        self.start.show()
        self.hide()

    def leader_window(self):
        # переходим в окно таблицы лидеров, показав новое окно и скрыв старое
        self.leader = Leaders(self.login)
        self.leader.show()
        self.hide()

    def rules_window(self):
        # переходим в окно правил, показав новое окно и скрыв старое
        self.rules = Rules(self.login)
        self.rules.show()
        self.hide()

    def profile_window(self):
        # переходим в окно профиля, показав новое окно и скрыв старое
        self.profile = Profile(self.login)
        self.profile.show()
        self.hide()

    def exit_window(self):
        # переходим в окно регистрации, показав новое окно и скрыв старое
        self.exit = Registration()
        self.exit.show()
        self.hide()


class Start(QMainWindow):
    def __init__(self, login):
        super().__init__()
        # ---------------- загрузка UI
        uic.loadUi(reader['difficult'], self)

        # ---------------- UI настройка/инициализация
        custom_font = font_set()
        app.setFont(custom_font)
        self.difficult.setFont(custom_font)
        self.playbutt.setFont(custom_font)
        self.exit.setFont(custom_font)
        self.difficult.addItems(['Легко', 'Нормально', 'Сложно'])
        self.login = login
        self.load_menu = None
        self.exit_to_menu = None

        # ---------------- настройка сигналов
        self.difficult.currentIndexChanged.connect(self.bombs_and_fields)
        self.playbutt.clicked.connect(self.load_game)
        self.exit.clicked.connect(self.exit_menu)

    def bombs_and_fields(self):

        # Если текущий индекс выпадающего меню равен сложности игры
        # (0 - легкий, 1 - средний и т.д.) - отображаем хар-ки поля
        if self.difficult.currentIndex() == 0:
            self.label_2.setText('Поле: 9x9')
            self.label.setText('Кол-во бомб: 12')
        elif self.difficult.currentIndex() == 1:
            self.label_2.setText('Поле: 15x15')
            self.label.setText('Кол-во бомб: 45')
        else:
            self.label_2.setText('Поле: 25x25')
            self.label.setText('Кол-во бомб: 125')

    def load_game(self):

        # переходим в окно загрузки игры, показав новое окно и скрыв старое
        self.load_menu = LoadGame(self.difficult.currentIndex(),
                                  self.login)
        self.load_menu.show()
        self.hide()

    def exit_menu(self):

        # переходим в окно меню, показав новое окно и скрыв старое
        self.exit_to_menu = Menu(self.login)
        self.exit_to_menu.show()
        self.hide()


class LoadGame(QMainWindow):
    def __init__(self, difficult, login):
        super().__init__()
        # ---------------- загрузка UI
        uic.loadUi(reader['load'], self)

        # ---------------- UI настройка/инициализация
        self.difficult = difficult
        self.login = login
        self.timer = QTimer()
        self.minesweeper_logic = None

        # ставим максимальное значение полосы
        self.progress_bar.setRange(0, 100)

        # ставим изначальное значение полосы
        self.progress_bar.setValue(0)

        # ---------------- настройка сигналов
        self.timer.timeout.connect(self.update_loading)

        # запуск метода, чтобы активировать таймер
        self.start()

    def start(self):
        # по достижению 75 миллисекунд активируется сигнал timeout, который
        # запустит метод update_loading, который обновит загрузочную полоску
        self.timer.start(75)

    def update_loading(self):
        # максимум полоски - 100, каждые 75 миллисекунд добавляем 10 к общей
        # сумме
        val = self.progress_bar.value() + 10

        # устанавливаем значение на данный момент
        self.progress_bar.setValue(val)

        # если максимум - останавливаем таймер и обращаемся к методу-переходу
        # к игре
        if val == self.progress_bar.maximum():
            self.timer.stop()
            self.start_game()

    def start_game(self):
        # переходим в окно меню, показав новое окно и скрыв старое
        self.minesweeper_logic = MinesweeperLogic(self.difficult,
                                                  self.login)
        self.minesweeper_logic.show()
        self.hide()


class MinesweeperLogic(QWidget):
    def __init__(self, difficult, name):
        super().__init__()
        # ---------------- загрузка бд
        self.con = sqlite3.connect('MinesweeperDB.db')
        self.cur = self.con.cursor()

        # ---------------- UI настройка/инициализация
        custom_font = font_set()
        app.setFont(custom_font)
        icon = QIcon(reader['flag'])
        pixmap = icon.pixmap(20, 20)
        self.label_flag_icon = QLabel(self)
        self.label_flag_icon.setPixmap(pixmap)
        self.label_flag_icon.resize(pixmap.size())
        self.buttons_container = QWidget(self)
        self.label_flag_guide = QLabel('Отметить флаг - ПКМ по клетке', self)
        self.label_flag_guide.setStyleSheet('''QLabel {color: white;}''')
        self.label_howmany_bombs = QLabel('Кол-во бомб:', self)
        self.label_howmany_bombs.setStyleSheet('''QLabel {color: white;}''')
        self.timer = QTimer(self)
        self.timer.start(1000)  # таймер срабатывает каждые 1000 мс (1 секунда)
        self.counter = 0
        self.timer_label = QLabel('Время: 0', self)
        self.timer_label.resize(120, 25)
        self.timer_label.setStyleSheet('''QLabel {color: white;}''')
        self.bomb_lcdnumber = QLCDNumber(self)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor('#121212'))
        self.setPalette(palette)
        self.setWindowIcon(QIcon(reader['redbomb']))
        self.exit_button = QPushButton('Выход', self)
        self.exit_button.resize(200, 32)
        self.exit_button.setStyleSheet('''QPushButton {
        background-color: rgb(120, 120, 120); /* Приглушенный красный цвет */
        color: white; /* Белый цвет текста */
        border: none; /* Убирает рамку, при необходимости */
        padding: 8px; /* Отступы внутри кнопки */
        border-radius: 10px; /* Закругление углов кнопки */
        }
        QPushButton:hover {
            background-color: rgb(168, 168, 168); /* Цвет при наведении */
        }
        QPushButton:pressed {
            background-color: rgb(207, 207, 207); /* Цвет при нажатии */
        }''')
        self.yes_no_exit = QMessageBox()
        self.yes_no_exit.setWindowTitle('Подтверждение')
        self.yes_no_exit.setText('Вы уверены? Ваш прогресс не сохранится')
        self.yes_button = QPushButton('Да')
        no_button = QPushButton('Нет')
        self.yes_no_exit.addButton(self.yes_button,
                                   QMessageBox.ButtonRole.YesRole)
        self.yes_no_exit.addButton(no_button, QMessageBox.ButtonRole.NoRole)

        # ---------------- инициализация нужных переменных
        self.counter = 0
        self.difficult = difficult
        self.login = name

        # каждая координата записана в списке типа is_checked, is_flag,
        # is_safe, is_bomb
        self.matrix = []

        # хранение ссылок на кнопки
        self.buttons = {}

        self.exit_to_menu = None
        self.leave_button = None
        self.flag_first = True

        # ---------------- настройка сигналов
        self.exit_button.clicked.connect(self.exit_menu_before)
        self.timer.timeout.connect(self.timer_lab)

        # проверка на сложность, в зависимости от которой будет сгенерировано
        # определенное поле
        if self.difficult == 0:
            self.bombs = 12
            self.bombs_copy = self.bombs
            self.generation(10, 10, 225, 225)
            self.setFixedSize(340, 400)
            self.bomb_lcdnumber.move(135, 35)
            self.label_howmany_bombs.move(10, 35)
            self.timer_label.move(210, 33)
            self.label_flag_icon.move(10, 10)
            self.label_flag_guide.move(37, 10)
            self.exit_button.move(73, 340)
            # Ставим игровое поле на нужные координаты
            self.buttons_container.move(57, 92)
            self.setWindowTitle('Игра - лёгкая сложность')
        elif self.difficult == 1:
            self.bombs = 45
            self.bombs_copy = self.bombs
            self.generation(10, 10, 375, 375)
            self.setFixedSize(485, 550)
            self.bomb_lcdnumber.move(216, 35)  # +18
            self.label_howmany_bombs.move(91, 35)  # +18
            self.timer_label.move(291, 33)  # +18
            self.label_flag_icon.move(81, 10)  # увеличиваем на 71
            self.label_flag_guide.move(108, 10)  # увеличиваем на 71
            self.exit_button.move(146, 490)
            # Ставим игровое поле на нужные координаты
            self.buttons_container.move(57, 92)
            self.setWindowTitle('Игра - средняя сложность')
        else:
            self.bombs = 125
            self.bombs_copy = self.bombs
            self.generation(10, 10, 625, 625)
            self.setFixedSize(743, 750)
            self.bomb_lcdnumber.move(226, 35)  # +130 - 70 - 50
            self.label_howmany_bombs.move(101, 35)  # +130
            self.timer_label.move(301, 33)  # +130
            self.label_flag_icon.move(90, 10)  # увеличиваем на 129
            self.label_flag_guide.move(117, 10)
            self.exit_button.move(460, 20)
            # Ставим игровое поле на нужные координаты
            self.buttons_container.move(57, 92)
            self.setWindowTitle('Игра - тяжелая сложность')

    def generation(self, coord_x, coord_y, size1, size2):

        # устанавливаем поле по заданным координатам и заданным размерам
        self.buttons_container.setGeometry(coord_x, coord_y, size1, size2)

        # отображаем кол-во бомб
        self.bomb_lcdnumber.display(f'{self.bombs}')

        # создаем сетку для кнопок с нулевыми отступами
        grid = QGridLayout()
        grid.setSpacing(0)
        grid.setContentsMargins(0, 0, 0, 0)

        # цикл прорисовки пустых клеток
        for i in range(size1 // 25):

            # список, в который будут записываться клетки ряда,
            # а впоследствии весь ряд в общую матрицу
            sp = []
            for j in range(size2 // 25):
                # создаем кнопку
                button = QPushButton(self)

                # пишем сигнал. сигнал mousePressEvent реагирует конкретно
                # на нажатия кнопки мыши,
                # и передает в event объект, определяющий, какой кнопокй
                # мыши нажали по кнопке
                button.mousePressEvent = lambda event, x=i, y=j: \
                    self.step(event, x, y, size1)  # обработка нажатия

                # устанавливаем фиксированный размер кнопки и ставим картинку
                # не открытой клетки, а далее добавляем в сетку
                button.setFixedSize(25, 25)
                button.setStyleSheet('border-image: url({0}) stretch;'.format(
                    reader['before_block']))
                grid.addWidget(button, i, j)

                # записываем в дополнительный словарь все кнопки с ключем
                # в виде координаты, чтобы работать с ними удобно
                self.buttons[(i, j)] = button

                # добавляем в список-ряд значение кнопки
                sp.append([0, 0, 0, 0])
            self.matrix.append(sp.copy())
            sp.clear()

        # устанавливаем в контейнер сетку
        self.buttons_container.setLayout(grid)

    def step(self, event, x, y, size1):

        # вызываем функцию вне класса, благодаря которой будет возможность
        # отслеживать, какой кнопкой мыши нажали на кнопку.
        flag_status = click(event.button())

        # для удобства записываем в переменную кнопку, которую вызвали,
        # обращаясь к словарю

        button = self.buttons.get((x, y))

        # для удобства делаем список соседей для кнопки, которую проверяем,
        # с уже готовыми координатами
        neighbors = [
            (x - 1, y - 1), (x - 1, y), (x - 1, y + 1),
            (x, y + 1), (x + 1, y + 1), (x + 1, y),
            (x + 1, y - 1), (x, y - 1)
        ]

        # проверка, первый ход или нет
        if (self.flag_first and not flag_status and
                self.matrix[x][y][1] != 1):

            # ставим кнопке иконку проверенной иконки, т.к. по умолчанию
            # первый ход всегда и окружающие 8 кнопок безопасны
            button.setStyleSheet(
                'border-image: url({0}) stretch;'.format(reader['none_block']))

            # ставим True в кнопке на значение is_checked и is_safe. is_safe
            # нужен для правильной генерации бомб
            self.matrix[x][y][0] = 1
            self.matrix[x][y][2] = 1
            self.flag_first = False

            # проверяем, находится ли кнопка на поле и выставляем ей нужные
            # значения на True
            for x_1, y_1 in neighbors:
                if 0 <= x_1 < (size1 // 25) and 0 <= y_1 < (
                        size1 // 25):  # проверка границ поля
                    self.matrix[x_1][y_1][0] = 1
                    self.matrix[x_1][y_1][2] = 1

            # цикл расстановки бомб
            for i in range(self.bombs):

                # в переменной а хранится рандомная строка матрицы
                a = randrange(0, len(self.matrix))
                while True:

                    # в б хранится рандомная кнопка из выбранной строки в
                    # переменной а
                    b = randrange(0, len(self.matrix[a]))

                    # если найдется клетка без имеющейся уже бомбы - ставим
                    # бомбу и выходим из цикла
                    if self.matrix[a][b][3] != 1 and self.matrix[a][b][2] != 1:
                        self.matrix[a][b][3] = 1
                        break

            # вызываем метод алгоритма открытия пустых клеток
            self.none_alg(size1, x, y)

        # если кнопка не проверена
        if not self.matrix[x][y][0]:

            # проверка кнопок с режимом выставления флагов
            # если режим флага включен и кнопка уже с флагом
            if flag_status and self.matrix[x][y][1] == 1:

                # ставим иконку не проверенной кнопки и ставим значение флага
                # на false
                button.setStyleSheet('border-image: url({0}) stretch;'.format(
                    reader['before_block']))
                self.matrix[x][y][1] = 0
                self.bombs_copy += 1
                self.bomb_lcdnumber.display(f'{self.bombs_copy}')

            # если режим флага включен и кнопка без флага
            elif flag_status and self.matrix[x][y][1] == 0:

                # выставляем иконку флага и ставим значение флага на true
                button.setStyleSheet(
                    'border-image: url({0}) stretch;'.format(reader['flag']))
                self.matrix[x][y][1] = 1
                self.bombs_copy -= 1
                self.bomb_lcdnumber.display(f'{self.bombs_copy}')

            # если режим флага выключен и пользователь нажал на кнопку флага
            elif self.matrix[x][y][1] == 1:
                return

            # обычный ход
            else:

                # проверка, попался ли пользователь на мину
                if self.matrix[x][y][3] == 1:

                    # ставим статус проверен, что в последствии правильно
                    # отобразить поле
                    self.matrix[x][y][0] = 1
                    button.setStyleSheet(
                        'border-image: url({0}) stretch;'.format(
                            reader['redbomb']))

                    # вызываем метод отображения бомб
                    self.show_bombs()

                    # останавливаем таймер
                    self.timer.stop()

                    # вызываем метод, который отобразит победу/поражение и
                    # запишет результат в бд
                    self.win_lose(False)

                else:

                    # клетка без бомбы, ставим статус проверен и проверяем
                    # соседние клетки на кол-во бомб рядом
                    self.matrix[x][y][0] = 1
                    countbombs = 0

                    for x_1, y_1 in neighbors:
                        if 0 <= x_1 < (size1 // 25) and 0 <= y_1 < (
                                size1 // 25):  # проверка границ поля
                            if self.matrix[x_1][y_1][3] == 1:
                                countbombs += 1

                    # если есть хотя бы одна бомба, кол-во бомб рядом
                    # отправляем в функцию вне класса для установки
                    # соответствующей картинки
                    if countbombs > 0:
                        self.buttons.get((x, y)).setStyleSheet(
                            f'\
border-image: url({number(countbombs)}) stretch;')
                    else:

                        # иначе ставим картинку пустой клетки и вызываем метод
                        # алгоритма открытия пустых клеток
                        button.setStyleSheet(
                            'border-image: url({0}) stretch;'.format(
                                reader['none_block']))
                        self.none_alg(size1, x, y)

                    # считаем кол-во не открытых клеток (count) и клеток с
                    # бомбой (count1)
                    count = 0
                    count1 = 0
                    for i in range(len(self.matrix)):
                        for j in range(len(self.matrix[0])):
                            if self.matrix[i][j][0] == 0:
                                count += 1
                            if self.matrix[i][j][3] == 1:
                                count1 += 1

                    # если они равны, значит на поле остались только клетки с
                    # бомбами и мы вызываем метод победы и отображения поля
                    if count == count1:
                        # отображение поля
                        self.show_bombs()

                        # кол-во бомб ставим на 0 и отображаем на счетчике
                        self.bombs_copy = 0
                        self.bomb_lcdnumber.display(f'{self.bombs_copy}')

                        # останавливаем таймер
                        self.timer.stop()

                        # вызываем метод win_lose с победой (True)
                        self.win_lose(True)

    def none_alg(self, size1, x, y):

        # sta - очередь с уже заданной начальной координатой
        sta = [(x, y)]

        # is_visited - множество координат, которые мы уже прошли
        is_visited = set()

        # цикл будет работать пока очередь не закончится
        while sta:

            # забираем первый элемент очереди
            x, y = sta.pop(0)

            # проверка, была ли уже такая координата
            if (x, y) in is_visited:
                continue

            # добавляем в посещенные
            is_visited.add((x, y))
            bomb_count = 0
            neighbors = [
                (x - 1, y - 1), (x - 1, y), (x - 1, y + 1),
                (x, y + 1), (x + 1, y + 1), (x + 1, y),
                (x + 1, y - 1), (x, y - 1)
            ]

            for x_1, y_1 in neighbors:
                if 0 <= x_1 < (size1 // 25) and 0 <= y_1 < (
                        size1 // 25):  # проверка границ поля
                    if self.matrix[x_1][y_1][3] == 1:
                        bomb_count += 1

            # если есть хотя бы одна бомба, то мы не добавляем соседей этой
            # клетки и идем дальше по очереди
            # если бомб 0 - проходимся по соседям, проверяем, есть ли они в
            # пределах поле и нет ли их в списке посещенных
            if bomb_count > 0:
                self.buttons.get((x, y)).setStyleSheet(
                    f'border-image: url({number(bomb_count)}) stretch;')
                self.matrix[x][y][0] = 1
            else:
                self.buttons.get((x, y)).setStyleSheet(
                    'border-image: url({0}) stretch;'.format(
                        reader['none_block']))
                self.matrix[x][y][0] = 1
                for x_1, y_1 in neighbors:
                    if (0 <= x_1 < (size1 // 25) and 0 <= y_1 < (
                            size1 // 25) and
                            (x_1, y_1) not in is_visited):
                        sta.append((x_1, y_1))

    def show_bombs(self):

        # метод отображения поля после победы/поражения
        # выключаем каждую кнопку. далее проверка, если клетка не проверена
        # и в ней бомба - ставим иконку бомбы
        for i in range(len(self.matrix)):
            for j in range(len(self.matrix[0])):
                self.buttons.get((i, j)).setEnabled(False)
                if self.matrix[i][j][3] == 1 and self.matrix[i][j][0] != 1:
                    self.buttons.get((i, j)).setStyleSheet(
                        'border-image: url({0}) stretch;'.format(
                            reader['bomb']))

    def timer_lab(self):

        # метод таймера. в __init__ прописано, что каждые 1000 миллисекунд
        # (1 секунда) вызывается этот метод,
        # который суммирует время и отображает его
        self.counter += 1
        self.timer_label.setText(f'Время: {self.counter}')

    def win_lose(self, state):

        # метод победы/поражения. результаты записываются в бд только в случае
        # победы (state = True)
        if state:

            # если победили, берем из базы данных результаты игрока за все
            # сложности
            text = f'Победа!\n{self.counter} секунд(ы)'
            easy, medium, hard = self.cur.execute('''SELECT easy, medium, \
hard FROM game
WHERE user_id = (SELECT id FROM users
                    WHERE name = ?)''', (self.login,)).fetchone()

            # проверка на нынешнюю сложность
            if self.difficult == 0:

                # если результат равен None (то есть это первая победа в
                # данной категории) или результат лучше предыдущего (меньше)
                if (easy is None) or (self.counter < easy):
                    self.cur.execute('''UPDATE game
                        SET
                        easy = ?
                        WHERE user_id = (SELECT id FROM users
                    WHERE name = ?)''', (self.counter, self.login,))
            elif self.difficult == 1:

                # если результат равен None (то есть это первая победа в
                # данной категории) или результат лучше предыдущего (меньше)
                if (medium is None) or (self.counter < medium):
                    self.cur.execute('''UPDATE game
                        SET
                        medium = ?
                        WHERE user_id = (SELECT id FROM users
                    WHERE name = ?)''', (self.counter, self.login,))
            else:

                # если результат равен None (то есть это первая победа в данной
                # категории) или результат лучше предыдущего (меньше)
                if (hard is None) or (self.counter < hard):
                    self.cur.execute('''UPDATE game
                        SET
                        hard = ?
                        WHERE user_id = (SELECT id FROM users
                    WHERE name = ?)''', (self.counter, self.login,))
        else:

            # иначе пишем поражение
            text = f'Поражение!\nЛКМ - выйти'

        # сохраняем изменения
        self.con.commit()

        # создаем кнопку с текстом победы/поражения
        self.leave_button = QPushButton(text, self)

        # сигнал
        self.leave_button.clicked.connect(self.exit_menu_after)
        self.leave_button.setStyleSheet('''
                    QPushButton {
                        background-color: rgba(54, 54, 54, 128);
                        color: white; /* Цвет текста */
                        font-size: 40px; /* Размер текста */
                    }
                ''')

        # проверка на сложность для создания кнопки подходящего размера
        if self.difficult == 0:
            self.leave_button.resize(340, 400)
        elif self.difficult == 1:
            self.leave_button.resize(485, 550)
        else:
            self.leave_button.resize(743, 750)

        # включаем отображение кнопки
        self.leave_button.show()

    def exit_menu_before(self):

        # метод выхода из игры перед концом раунда. активируем диалог.
        # если пользователь нажал да - выкидываем в меню
        self.yes_no_exit.exec()
        if self.yes_no_exit.clickedButton() == self.yes_button:
            self.exit_to_menu = Menu(self.login)
            self.exit_to_menu.show()
            self.hide()

    def exit_menu_after(self):

        # переходим в окно меню, показав новое окно и скрыв старое
        self.exit_to_menu = Menu(self.login)
        self.exit_to_menu.show()
        self.hide()


class Profile(QMainWindow):
    def __init__(self, login):
        super().__init__()
        # ---------------- загрузка UI и бд
        uic.loadUi(reader['profile'], self)
        self.con = sqlite3.connect('MinesweeperDB.db')
        self.cur = self.con.cursor()

        # ---------------- UI настройка/инициализация
        self.login = login
        custom_font = font_set()
        app.setFont(custom_font)
        self.change_login.setFont(custom_font)
        self.change_passw.setFont(custom_font)
        self.delete_acc.setFont(custom_font)
        self.error_label.setFont(custom_font)
        self.login_label.setText(f'Логин: {self.login}')
        self.yes_no_choice = QMessageBox()
        self.yes_no_choice.setWindowTitle('Подтверждение')
        self.yes_no_choice.setText('Вы уверены, что хотите удалить аккаунт?')
        self.yes_button = QPushButton('Да')
        no_button = QPushButton('Нет')
        self.yes_no_choice.addButton(self.yes_button,
                                     QMessageBox.ButtonRole.YesRole)
        self.yes_no_choice.addButton(no_button, QMessageBox.ButtonRole.NoRole)
        self.validator = '\
        абвгдеёжзийклмнопрстуфхцчшщъыьэюяabcdefghijklmnopqrstuvwxyz0123456789_'
        self.exit_to_menu = None
        self.reg = None

        # ---------------- настройка сигналов кнопок
        self.delete_acc.clicked.connect(self.opt_delete_acc)
        self.change_login.clicked.connect(self.opt_change_login)
        self.change_passw.clicked.connect(self.opt_change_password)
        self.exit.clicked.connect(self.exit_menu)

    def opt_delete_acc(self):

        # вызываем диалог для подтверждения пароля перед удалением аккаунта
        password, ok_pressed = QInputDialog.getText(self, 'Удаление аккаунта',
                                                    'Введите пароль от \
аккаунта')

        # если нажал ок - вытаскиваем из бд пароль по логину и сравниваем с
        # введенным. если совпало - вызываем диалог да/нет
        # если да - обновляем данные пользователя is_deleted = 1,
        # сохраняем и отправляем в окно регистрации. в иных случаях
        # будет появляться ошибка
        if ok_pressed:
            password_check = self.cur.execute(f'''SELECT password FROM users
                        WHERE name = ?''', (self.login,)).fetchone()
            if password_check[0] == password:
                self.yes_no_choice.exec()
                if self.yes_no_choice.clickedButton() == self.yes_button:
                    self.cur.execute('''UPDATE users
                            SET 
                            is_deleted = ?
                            WHERE name = ?''', (True, self.login))
                    self.con.commit()
                    self.reg = Registration()
                    self.reg.show()
                    self.hide()
                else:
                    self.error_label.setText('Удаление аккаунта отменено')
            else:
                self.error_label.setText('Неверный пароль')
        else:
            self.error_label.setText('Удаление аккаунта отменено')

    def opt_change_login(self):

        # вызываем диалог для ввода нового логина
        login, ok_pressed = QInputDialog.getText(self, 'Изменение логина',
                                                 'Введите новый \
логин для аккаунта')

        # если нажал ок - обращаемся к функции-валидатору вне класса и
        # проверяем
        # на правильность записи логина. если все верно - обновляем имя,
        # сохраняем и пишем пользователю об успешной операции
        # иначе выводим ошибки
        if ok_pressed:
            try:
                if validator_check(login):
                    self.cur.execute('''UPDATE users
                            SET 
                            name = ?
                            WHERE name = ?''', (login, self.login))
                    self.con.commit()
                    self.login = login
                    self.login_label.setText(f'Логин: {self.login}')
                    self.error_label.setText('Логин успешно изменён')
                else:
                    raise LoginError()
            except LoginError:
                self.error_label.setText('\
Логин должен быть менее 4 и более 15символов, содержать только буквы \
русского/латинского языка и нижнее подчеркивание')
            except sqlite3.IntegrityError:
                self.error_label.setText('Данный логин уже существует')
        else:
            self.error_label.setText('Отмена смены логина')

    def opt_change_password(self):

        # вызываем диалог для ввода нового пароля
        passw, ok_pressed = QInputDialog.getText(self, 'Изменение пароля',
                                                 'Введите новый \
пароль для аккаунта')

        if ok_pressed:
            try:

                # проверяем правильность написания пароля, а далее обновляем
                # его, сохраняем изменения и пишем об успешной операции
                # иначе выводим ошибки
                if len(passw) >= 5:
                    self.cur.execute('''UPDATE users
                                    SET 
                                    password = ?
                                    WHERE name = ?''', (passw, self.login))
                    self.con.commit()
                    self.error_label.setText('Пароль успешно изменён')
                else:
                    raise PasswordError()
            except PasswordError:
                self.error_label.setText('Пароль должен состоять из не менее \
5 символов')
        else:
            self.error_label.setText('Отмена смены пароля')

    def exit_menu(self):

        # переходим в окно меню, показав новое окно и скрыв старое
        self.exit_to_menu = Menu(self.login)
        self.exit_to_menu.show()
        self.hide()


class Rules(QMainWindow):
    def __init__(self, login):
        super().__init__()
        # ---------------- загрузка UI
        uic.loadUi(reader['rules'], self)

        # ---------------- UI настройка/инициализация
        self.login = login
        self.exit_to_menu = None

        # ---------------- настройка сигналов кнопок
        self.exit.clicked.connect(self.exit_menu)

    def exit_menu(self):
        # переходим в окно меню, показав новое окно и скрыв старое
        self.exit_to_menu = Menu(self.login)
        self.exit_to_menu.show()
        self.hide()


class Leaders(QMainWindow):
    def __init__(self, login):
        super().__init__()
        # ---------------- загрузка UI и бд
        uic.loadUi(reader['leaders'], self)
        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.db.setDatabaseName('MinesweeperDB.db')
        if not self.db.open():
            raise Exception('Не удалось подключиться к базе данных.')

        # ---------------- UI настройка/инициализация
        self.login = login
        self.exit_to_menu = None
        self.model = QSqlQueryModel()
        easy = '''
                    SELECT users.name, game.easy
                    FROM game
                    JOIN users ON users.id = game.user_id
                    WHERE users.is_deleted = 0 AND game.easy IS NOT NULL
                    ORDER BY game.easy ASC
                '''
        medium = '''
                    SELECT users.name, game.medium
                    FROM game
                    JOIN users ON users.id = game.user_id
                    WHERE users.is_deleted = 0 AND game.medium IS NOT NULL
                    ORDER BY game.medium ASC
                '''
        hard = '''
                    SELECT users.name, game.hard
                    FROM game
                    JOIN users ON users.id = game.user_id
                    WHERE users.is_deleted = 0 AND game.hard IS NOT NULL
                    ORDER BY game.hard ASC
                '''

        # ---------------- настройка сигналов кнопок
        self.exit.clicked.connect(self.exit_menu)

        # передаем в функцию нужный запрос в соответствии со сложностью
        self.easy_but.clicked.connect(lambda sel, diff=easy: self.table(diff))
        self.medium_but.clicked.connect(lambda sel, diff=medium:
                                        self.table(diff))
        self.hard_but.clicked.connect(lambda sel, diff=hard: self.table(diff))

    def table(self, difficult):
        # Создаём модель с SQL-запросом
        self.model.setQuery(difficult)

        # Устанавливаем заголовки
        self.model.setHeaderData(0, Qt.Orientation.Horizontal,
                                 'Имя пользователя')
        self.model.setHeaderData(1, Qt.Orientation.Horizontal,
                                 'Результат (в секундах)')

        # Настраиваем визуал таблицы
        self.table_v.setModel(self.model)
        self.table_v.setSelectionMode(
            QTableView.SelectionMode.NoSelection)  # Отключаем выделение
        self.table_v.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Убираем фокус
        self.table_v.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)  # заголовки расширяются
        # от содержимого

    def exit_menu(self):
        # переходим в окно меню, показав новое окно и скрыв старое
        self.exit_to_menu = Menu(self.login)
        self.exit_to_menu.show()
        self.hide()


def font_set():
    # добавляем к окну пользовательский шрифт
    font_id = QFontDatabase.addApplicationFont(reader['font_cus'])

    # если шрифт правильно загрузился
    if font_id != -1:
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        custom_font = QFont(font_family)
        return custom_font


def validator_check(login):
    # список разрешенных символов
    validator = '\
абвгдеёжзийклмнопрстуфхцчшщъыьэюяabcdefghijklmnopqrstuvwxyz0123456789_'

    # логин должен быть так же не менее 4 символов и не более 15
    if len(login) < 4 or len(login) > 15:
        return False
    for i in login:
        if i.lower() not in validator:
            return False
    return True


def number(bombs):
    # вставляем кол-во бомб и получаем нужную картинку
    return reader[f'number{bombs}']


def click(buttontype):
    # если нажата левая кнопка = возвращаем False, иначе True
    if buttontype == Qt.MouseButton.LeftButton:
        return False
    elif buttontype == Qt.MouseButton.RightButton:
        return True


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    ex = Registration()
    ex.show()
    sys.exit(app.exec())
