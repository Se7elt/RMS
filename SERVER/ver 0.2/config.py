import configparser

config = configparser.ConfigParser()
config.read("config.ini")

# Функция для получения данных конфигурации
def get_config(section, key):
    try:
        return config[section][key]
    except KeyError:
        print(f"Не удалось найти {key} в секции {section}. Проверьте файл config.ini")
        return None
