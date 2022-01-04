# Главный файл запуска программы

import sqlite3
import sys
import traceback
import file_rc


from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QTextCharFormat, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QHeaderView
from datetime import time, datetime

from ui_py.workspace_ui import Ui_MainWindow
from graphics import LOADING
from windows import Cabinet, HelloScreen
from PyQt5 import QtCore, QtWidgets

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


# Класс главного рабочего окна

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):  # выбор загрузочного экрана в завсимости от наличии информации о пользователе
        super().__init__()
        self.setWindowTitle('SF Calendar')
        self.setGeometry(0, 0, *SCREEN_SIZE)
        file = open('personal_data.txt', encoding='utf-8')
        data = [x.strip().split() for x in file.readlines()]
        file.close()
        if data:
            self.workspace(data[0][0])
        else:
            self.hello = HelloScreen(self, SCREEN_SIZE)
            self.hide()
            self.hello.show()

    def workspace(self, name):  # Инициализатор рабочего стола
        LOADING(self)
        self.show()
        self.setupUi(self)
        self.setWindowTitle('SF Calendar')
        # self.label_4.resize(*SCREEN_SIZE)
        if time(5, 0, 0) < datetime.now().time() < time(12, 0, 0):
            self.label_3.setText(f"Доброе утро, {name}!")
        elif time(12, 0, 0) < datetime.now().time() < time(17, 0, 0):
            self.label_3.setText(f"Добрый день, {name}!")
        elif time(17, 0, 0) < datetime.now().time() < time(23, 0, 0):
            self.label_3.setText(f"Добрый вечер, {name}!")
        else:
            self.label_3.setText(f"Доброй ночи, {name}!")
        self.setGeometry(0, 30, *SCREEN_SIZE)
        self.pushButton.clicked.connect(self.personal_account)
        self.pushButton_3.clicked.connect(self.add)
        self.pushButton_2.clicked.connect(self.delete)
        self.result = []
        self.calendarWidget.clicked.connect(self.load)
        self.pushButton_4.clicked.connect(self.log)
        self.label.setText(
            "Вы заполняете  " + self.calendarWidget.selectedDate().toString(Qt.DefaultLocaleLongDate))

        self.date = self.calendarWidget.selectedDate().toString("yyyy-MM-dd")
        self.tableWidget.itemChanged.connect(self.item_changed)
        self.modified = {}
        # оформляем таблицы
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(3)

        self.tableWidget_2.setRowCount(0)
        self.tableWidget_2.setColumnCount(6)

        self.lineEdit.textChanged[str].connect(self.find)
        self.tableWidget.setHorizontalHeaderLabels(['Название', 'Раздел', 'Масса (г)'])
        self.tableWidget_2.setHorizontalHeaderLabels(["Название", "Раздел", 'Белки', 'Жиры', 'Углеводы', 'ККал'])

        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.load()
        self.calendar_prepare()
        self.comboBox.currentIndexChanged.connect(self.find)

    def personal_account(self):  # Открытие личного кабинета
        self.w = Cabinet(self, SCREEN_SIZE)
        self.hide()
        self.w.show()

    def calendar_prepare(self):  # Выделение заполненных дат крупным шрифтом
        self.connection = sqlite3.connect("dnevnik.sqlite")
        cur = self.connection.cursor()
        dates = cur.execute("""SELECT date FROM log""").fetchall()
        for el in dates:
            format = QTextCharFormat()
            format.setFont(QFont('Times', 15))
            date = QDate(*[int(x) for x in el[0].split('-')])
            self.calendarWidget.setDateTextFormat(date, format)

    def find(self):  # Реагирует на изменение строки поиска и загружает результат в таблицу
        self.connection = sqlite3.connect("food.sqlite")
        cur = self.connection.cursor()
        while self.tableWidget_2.rowCount() > 0:  # Перед запонением необходимо очистить все строки
            self.tableWidget_2.removeRow(0)

        self.tableWidget_2.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        #    задаем параметры ширины столбцов таблицы
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tableWidget_2.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        if self.lineEdit.text():  # Запрос не должен выполняться, если пользователь стер последний символ
            if self.comboBox.currentText() == "По названию":
                result = cur.execute(f"""SELECT product, (SELECT type from types where id = foods.type) , protein,
                                            fats, carbohydrates, kilocalories FROM foods
                                            WHERE product LIKE '{'%' + self.lineEdit.text().lower() + '%'}' OR
                                             product LIKE '{self.lineEdit.text().capitalize() + '%'}'""").fetchall()
            elif self.comboBox.currentText() == "По разделу":
                result = cur.execute(f"""SELECT product, (SELECT type from types where id = foods.type), protein, fats,
                                            carbohydrates, kilocalories FROM foods WHERE type LIKE 
                                            (SELECT id from types Where type LIKE '{self.lineEdit.text().lower()}%' OR
                                             type LIKE '{self.lineEdit.text().capitalize()}%')""").fetchall()
            else:
                result = []
            # Заполняем таблицу элементами
            for i, row in enumerate(result):
                self.tableWidget_2.setRowCount(
                    self.tableWidget_2.rowCount() + 1)
                for j, elem in enumerate(row):
                    self.tableWidget_2.setItem(
                        i, j, QTableWidgetItem(str(elem)))
            self.connection.close()

    def delete(self):
        self.connection = sqlite3.connect("dnevnik.sqlite")
        cur = self.connection.cursor()
        indexes = self.tableWidget.selectedIndexes()
        # удаление элементов из базы данных
        for el in indexes:
            cur.execute(f"""DELETE FROM log WHERE (food = 
                '{self.tableWidget.item(el.row(), el.column()).text()}' AND date = '{self.date.toString('yyyy-MM-dd')}')""")
            self.connection.commit()
        #    удаление строк из таблицы
        if indexes:
            for i, el in enumerate(indexes):
                del self.result[el.row() - i]
                self.tableWidget.removeRow(el.row() - i)

    def add(self):  # Перенос результатов запроса в дневник
        self.connection = sqlite3.connect("food.sqlite")
        cur = self.connection.cursor()
        for el in self.tableWidget_2.selectedIndexes():
            item = cur.execute(f"""SELECT product, (SELECT type from types where id = foods.type), weight FROM foods 
            WHERE product = '{self.tableWidget_2.item(el.row(), el.column()).text()}'""").fetchall()
            self.result += item  # добаявляем очередной выбранный элемент
        #    отключаем реакцию на изменение ячейки пользователем на время заполнения таблицы
        self.tableWidget.itemChanged.disconnect(self.item_changed)

        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        for i, row in enumerate(self.result):
            self.tableWidget.setRowCount(
                len(self.result))
            for j, elem in enumerate(row):
                self.tableWidget.setItem(
                    i, j, QTableWidgetItem(str(elem)))
        # включаем реакцию на изменение ячейки пользователем
        self.tableWidget.itemChanged.connect(self.item_changed)

    def item_changed(self, item):
        #    если масса продукта была изменена в словарь записывается индекс строки и измененная масса
        if item.column() == 2:
            self.modified[item.row()] = item.text()

    def log(self):  # добавление в БД dnevnik.sqlite очистка всех таблиц
        self.connection = sqlite3.connect("dnevnik.sqlite")
        cur = self.connection.cursor()
        self.result = [list(x) for x in self.result]
        # применяем изменения массы
        for key in self.modified:
            self.result[key][2] = self.modified[key]
        self.modified.clear()
        if self.result:
            for el in self.result:
                if any([el[0] in x for x in
                        cur.execute(
                            f"SELECT food FROM log WHERE date = '{self.date.toString('yyyy-MM-dd')}'").fetchall()]):
                    # обновляем массу для продуктов выбранной даты
                    cur.execute(f"""UPDATE log SET weight = {el[2]} WHERE
                     food = '{el[0]}' AND date = '{self.date.toString('yyyy-MM-dd')}' """)
                else:
                    # если во время изменения массы были добалены новые позиции, то их тоже запишем
                    cur.execute(f"""INSERT INTO log(date, food, type, weight) VALUES
                        ('{self.date.toString('yyyy-MM-dd')}', '{(el[0])}', '{(el[1])}', '{(el[2])}')""")
                self.connection.commit()
            self.connection.close()

            #    очищаем все результаты поиска
            while self.tableWidget_2.rowCount() > 0:
                self.tableWidget_2.removeRow(0)
            self.lineEdit.setText('')
            # специальный шрифт для заполненной даты
            format = QTextCharFormat()
            format.setFont(QFont('Times', 15))
            date = QDate(*[int(x) for x in self.date.toString("yyyy-MM-dd").split('-')])
            self.calendarWidget.setDateTextFormat(date, format)

    def load(self):  # при нажатии на дату в календаре заполняется таблица
        # отключаем отслеживание изменений пользователем ячеек на время за полнения
        self.tableWidget.itemChanged.disconnect(self.item_changed)
        self.date = self.calendarWidget.selectedDate()
        # очищаем первую таблицу
        while self.tableWidget.rowCount() > 0:
            self.tableWidget.removeRow(0)

        self.label.setText("Вы заполняете  " + self.date.toString(Qt.DefaultLocaleLongDate))
        self.connection = sqlite3.connect("dnevnik.sqlite")
        cur = self.connection.cursor()
        self.tableWidget.setHorizontalHeaderLabels(['Название', 'Раздел', 'Масса'])
        # запрос данных из БД
        self.result = cur.execute(
            f"""SELECT food, type, weight FROM log WHERE date = '{self.date.toString('yyyy-MM-dd')}'""").fetchall()
        # если данные отсутсвуют, то их будет предложено заполнить, иначе - обновить
        if self.result:
            self.pushButton_4.setText('Обновить')
            for i, row in enumerate(self.result):
                self.tableWidget.setRowCount(len(self.result))
                for j, elem in enumerate(row):
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(elem)))
        else:
            self.pushButton_4.setText('Заполнить')
        self.tableWidget.itemChanged.connect(self.item_changed)

    def excepthook(exc_type, exc_value, exc_tb):  # отлов ошибок на время проектирования приложения
        tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(f"Обнаружена ошибка; {tb}")

    sys.excepthook = excepthook


if __name__ == '__main__':
    app = QApplication(sys.argv)
    SCREEN_SIZE = [app.desktop().width(), app.desktop().height()]
    w = MainWindow()
    sys.exit(app.exec_())
