# файл с функциями анимаций и параметрами графики
from PyQt5.QtCore import QPropertyAnimation


def LOADING(self):
    self.animation = QPropertyAnimation(self, b'windowOpacity')
    self.animation.setDuration(1000)  # Продолжительность: 1 секунда
    # Выполните постепенное увеличение
    try:
        self.animation.finished.disconnect(self.close)
    except Exception as e:
        pass
    self.animation.stop()
    # Диапазон прозрачности постепенно увеличивается от 0 до 1.
    self.animation.setStartValue(0)
    self.animation.setEndValue(1)
    self.animation.start()

