# Фикс для imghdr в Python 3.13+
import sys

class ImghdrModule:
    @staticmethod
    def what(file, h=None):
        # Простая реализация для обхода ошибки
        return None

# Подменяем модуль
sys.modules['imghdr'] = ImghdrModule()
