# в этом файле собраны классы всех окон, кроме основного
import sqlite3
from random import sample
from datetime import timedelta, date

from graphics import LOADING

from PyQt5.QtChart import QChart, QChartView, QPieSeries
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QWidget, QInputDialog
from PyQt5 import QtGui

from ui_py.personaldata_ui import Ui_Dialog as Ui_data
from ui_py.cabinet_ui import Ui_Form as Ui_cabinet
from ui_py.statistic_ui import Ui_Dialog as Ui_statistics
from ui_py.info_ui import Ui_Dialog as Ui_info
from ui_py.helloscreen_ui import Ui_Form as Ui_helloscreen


class PersonalDialog(QDialog, Ui_data):  # окно запроса персональной информации
    def __init__(self, other, SCREEN_SIZE):
        super().__init__()
        self.setupUi(self)
        self.parent = other
        self.setWindowTitle('Смарт')
        self.setGeometry((SCREEN_SIZE[0] - 425) // 2, (SCREEN_SIZE[1] - 266) // 2, 425, 266)
        self.acepted = False

    def keyPressEvent(self, event):
        if event.key() == 16777220 or event.key() == 16777221:  # коды клавиш Enter
            self.accept()

    def accept(self):  # ОК
        # получаем информацию из виджетов
        self.parent.name = self.lineEdit.text()
        self.parent.age = int(self.spinBox_3.value())
        self.parent.sex = self.comboBox.currentText()
        self.parent.weight = float(self.doubleSpinBox.value())
        self.parent.height = int(self.spinBox_2.value())
        self.parent.AMR = [1.375, 1.2, 1.725, 1.9][self.comboBox_2.currentIndex()]
        # если она корректна, то записываем в файл
        if self.parent.name:
            file = open('personal_data.txt', 'w', encoding='utf-8')
            print(self.parent.name, self.parent.age, self.parent.sex,
                  self.parent.weight, self.parent.height, self.parent.AMR, file=file)
            file.close()
            self.hide()
            self.acepted = True

    def reject(self):  # ОТМЕНА
        self.hide()
        self.acepted = False


class Cabinet(QWidget, Ui_cabinet):  # класс окна личного кабинета
    def __init__(self, other, SCREEN_SIZE):
        super().__init__()
        self.SCREEN_SIZE = SCREEN_SIZE
        self.parent = other
        self.setupUi(self)
        self.setWindowTitle('Личный кабинет')
        self.pushButton.clicked.connect(self.change)
        self.pushButton_2.clicked.connect(self.erease)
        self.pushButton_3.clicked.connect(self.statistic)
        self.pushButton_4.clicked.connect(self.workspace)
        self.pushButton_5.clicked.connect(self.delete)
        self.pushButton_6.clicked.connect(self.info)
        self.dateEdit.setDate(date.today() - timedelta(6))
        self.dateEdit_2.setDate(date.today())
        file = open('personal_data.txt', 'r', encoding='utf-8')
        info = [x.strip().split() for x in file.readlines()]
        file.close()
        if info:
            self.name, self.age, self.sex, self.weight, self.height, self.AMR = info[0]
            self.age = int(self.age)
            self.AMR = float(self.AMR)
            self.weight = float(self.weight)
            self.height = int(self.height)

    def info(self):
        self.w = Info()
        self.w.show()

    def workspace(self):  # возвращение на рабочий стол (данные на нем сохраняются)
        self.hide()
        self.parent.show()

    def change(self):  # просмотр и изменение персональных данных
        self.d = PersonalDialog(self, self.SCREEN_SIZE)

        self.d.lineEdit.setText(self.name)
        self.d.spinBox_3.setValue(self.age)
        if self.sex == 'Мужской':
            self.d.comboBox.setCurrentIndex(0)
        else:
            self.d.comboBox.setCurrentIndex(1)
        if self.AMR == 1.375:
            self.d.comboBox_2.setCurrentIndex(0)
        elif self.AMR == 1.2:
            self.d.comboBox_2.setCurrentIndex(1)
        elif self.AMR == 1.725:
            self.d.comboBox_2.setCurrentIndex(2)
        elif self.AMR == 1.9:
            self.d.comboBox_2.setCurrentIndex(3)
        self.d.doubleSpinBox.setValue(self.weight)
        self.d.spinBox_2.setValue(self.height)

        self.d.show()

    def erease(self):  # удаление персональных данных
        answer, ok_pressed = QInputDialog.getItem(
            self, "Подтверждение",
            "Вы точно хотите очистить персональные данные?\nОтменить это действие будет невозможно.",
            ("нет", "да"), 0, False)
        if ok_pressed and answer == 'да':
            file = open('personal_data.txt', 'w', encoding='utf-8')
            print('', file=file, end='')
            self.name, self.age, self.sex, self.weight, self.height, self.AMR = 'Пользователь', 1, "Мужской", 1, 100, 1.5

    def delete(self):
        answer, ok_pressed = QInputDialog.getItem(
            self, "Подтверждение",
            "Вы точно хотите очистить дневник питания?\nОтменить это действие будет невозможно.",
            ("нет", "да"), 0, False)
        if ok_pressed and answer == 'да':
            self.connection = sqlite3.connect('dnevnik.sqlite')
            cur = self.connection.cursor()
            cur.execute('''DELETE from log''')
            self.connection.commit()
            self.connection.close()

    def statistic(self):  # начинает расчет, и если данных достаточно, то выводит их в новое окно
        self.period = self.dateEdit.dateTime().daysTo(self.dateEdit_2.dateTime()) + 1
        self.real = self.calculation_based_on_the_fact()  # возвращают список целых значений    |
        self.norm = self.calculation_of_the_norm()  # |     белков жиров углеводов и килокалорий|
        if self.real:
            self.w = Statistic(self)
            self.w.show()

    def calculation_based_on_the_fact(self):  # реальные результаты пользователя
        protein, fats, carbohydrates, kilocalories = 0, 0, 0, 0

        self.date_mn = self.dateEdit.date()
        self.date_mx = self.dateEdit_2.date()

        self.connection = sqlite3.connect('dnevnik.sqlite')
        self.cur = self.connection.cursor()
        result = self.cur.execute(f"""SELECT food, weight FROM log WHERE
         (date BETWEEN '{self.date_mn.toString('yyyy-MM-dd')}' AND
          '{self.date_mx.toString('yyyy-MM-dd')}')""").fetchall()
        self.connection.close()
        if result == ('',):
            self.label_4.setText('Ничего не было найдено')
            return False
        else:
            self.connection = sqlite3.connect('food.sqlite')
            self.cur = self.connection.cursor()
            for el in result:
                nutrients = self.cur.execute(f"""SELECT protein, fats, carbohydrates, kilocalories FROM
                             foods WHERE product = '{el[0]}'""").fetchone()
                nutrients = [float(x[:-1].replace(",", ".")) for x in nutrients[:3]] + [
                    float(nutrients[3][:-4].replace(",", "."))]
                protein += (nutrients[0] / 100 * el[1])
                fats += (nutrients[1] / 100 * el[1])
                carbohydrates += (nutrients[2] / 100 * el[1])
                kilocalories += (nutrients[3] / 100 * el[1])
            return int(protein), int(fats), int(carbohydrates), int(kilocalories)

    def calculation_of_the_norm(self):  # усредненненные, нормальные значения
        # зависят от показателей базального метаболизма (BMR) и активного метаболизма (AMR), формула Харриса — Бенедикта
        if self.sex == "Женский":
            self.BMR = 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * self.age)
        else:  # Мужской
            self.BMR = 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * self.age)
        kilocalories = self.BMR * self.AMR * self.period
        protein = (22.5 / 100) * kilocalories
        fats = (25 / 100) * kilocalories
        carbohydrates = (52.5 / 100) * kilocalories
        return int(protein), int(fats), int(carbohydrates), int(kilocalories)


class Statistic(QDialog, Ui_statistics):
    def __init__(self, other):
        super().__init__()
        self.setupUi(self)
        self.parent = other
        self.real = self.parent.real
        self.setWindowTitle(f'Статистика питания с '
                            f'{self.parent.dateEdit.date().toString(Qt.DefaultLocaleLongDate)} по'
                            f' {self.parent.dateEdit_2.date().toString(Qt.DefaultLocaleLongDate)}')
        self.norm = self.parent.norm
        for i, el in enumerate([(self.lcdNumber, self.lcdNumber_2, self.label_6),
                                (self.lcdNumber_3, self.lcdNumber_4, self.label_5),
                                (self.lcdNumber_5, self.lcdNumber_6, self.label_9)]):
            el[0].display(str(self.real[i]))
            el[1].display(str(self.norm[i]))
            palette1 = el[1].palette()
            palette1.setColor(palette1.Dark, QtGui.QColor(0, 0, 0))
            el[1].setPalette(palette1)

            if (self.real[i] / self.norm[i]) * 100 >= 110 or (self.real[i] / self.norm[i]) * 100 <= 90:
                palette = el[0].palette()
                palette.setColor(palette.Dark, QtGui.QColor(255, 0, 0))
                el[0].setPalette(palette)
                file = open(f"{str(i + 1)}.txt", "r", encoding='utf-8')
                if (self.real[i] / self.norm[i]) * 100 > 110:
                    el[2].setText(f"Попробуйте воздержаться от таких продуктов, как "
                                  f"{', '.join(sample([x.strip() for x in file.readlines()], k=3))}")
                else:
                    el[2].setText(f"Попробуйте такие продукты, как "
                                  f"{', '.join(sample([x.strip() for x in file.readlines()], k=3))}")
                file.close()
            else:
                el[2].setText('Все в норме')
        # Заполнение диаграммы
        series = QPieSeries()
        series.append("Белки ", self.real[0])
        series.append("Жиры", self.real[1])
        series.append("Углеводы", self.real[2])
        # выбираем отслоившиеся части
        my_slice1 = series.slices()[0]
        my_slice1.setExploded(True)
        my_slice1.setLabelVisible(True)
        my_slice2 = series.slices()[1]
        my_slice2.setExploded(True)
        my_slice2.setLabelVisible(True)
        my_slice3 = series.slices()[2]
        my_slice3.setExploded(True)
        my_slice3.setLabelVisible(True)
        chart = QChart()
        chart.addSeries(series)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("Ваш результат")
        chart.setTheme(QChart.ChartThemeBlueCerulean)
        # создаем объект просмотра таблицы и загружаем его в layout
        chartview = QChartView(chart)
        self.horizontalLayout_2.addWidget(chartview)
        # АНАЛОГИЧНО
        series_1 = QPieSeries()
        series_1.append("Белки ", self.norm[0])
        series_1.append("Жиры", self.norm[1])
        series_1.append("Углеводы", self.norm[2])

        # slice
        my_slice_1 = series_1.slices()[0]
        my_slice_1.setExploded(True)
        my_slice_1.setLabelVisible(True)
        my_slice_2 = series_1.slices()[1]
        my_slice_2.setExploded(True)
        my_slice_2.setLabelVisible(True)
        my_slice_3 = series_1.slices()[2]
        my_slice_3.setExploded(True)
        my_slice_3.setLabelVisible(True)

        chart_1 = QChart()
        chart_1.addSeries(series_1)
        chart_1.setAnimationOptions(QChart.SeriesAnimations)
        chart_1.setTitle("Норма")
        chart_1.setTheme(QChart.ChartThemeBlueCerulean)
        # create QChartView object and add chart in thier
        chartview_1 = QChartView(chart_1)
        self.horizontalLayout_2.addWidget(chartview_1)


class HelloScreen(QWidget, Ui_helloscreen):
    def __init__(self, other, SCREEN_SIZE):
        super().__init__()
        self.parent = other
        self.SCREEN_SIZE = SCREEN_SIZE
        self.setupUi(self)
        LOADING(self)
        self.setGeometry((SCREEN_SIZE[0] - 700) // 2, (SCREEN_SIZE[1] - 500) // 2, 700, 500)
        self.label_4.resize(41, 41)
        self.pushButton.clicked.connect(self.dialog)

    def dialog(self):  # Запрос личной информации, если пользователь подтвердил действие, то открытие рабочего стола
        self.d = PersonalDialog(self, self.SCREEN_SIZE)
        self.d.exec_()
        if self.d.isHidden() and self.d.acepted:
            file = open('personal_data.txt', 'r', encoding='utf-8')
            info = [x.strip().split() for x in file.readlines()]
            file.close()
            self.hide()
            self.parent.workspace(info[0][0])


class Info(QDialog, Ui_info):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('Информация')
        self.setFixedSize(441, 321)
