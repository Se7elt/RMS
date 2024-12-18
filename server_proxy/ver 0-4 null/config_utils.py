import configparser
import os

CONFIG_FILE = "config.ini"


def initialize_config():
    config = configparser.ConfigParser()

    # Если файл конфигурации не существует, создаем его с пустыми значениями
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as configfile:
            # Задаем базовую структуру
            config["EMAIL"] = {
                "SMTP_SERVER": "",
                "SMTP_PORT": "",
                "SMTP_USER": "",
                "SMTP_PASSWORD": "",
                "IMAP_SERVER": "",
                "IMAP_USER": "",
                "IMAP_PASSWORD": ""
            }
            config["MAIN_SERVER"] = {"MAIN_SERVER_EMAIL": ""}
            config["FLAG"] = {"FLAG": "FALSE"}
            config.write(configfile)
    else:
        config.read(CONFIG_FILE)

    return config


def check_flag_and_data(config):
    return config["FLAG"].get("FLAG", "FALSE") == "TRUE"


def prompt_for_data(config):
    print("Введите данные для подключения к серверам:")

    # Запрос данных SMTP
    config["EMAIL"]["SMTP_SERVER"] = input("SMTP сервер: ")
    config["EMAIL"]["SMTP_PORT"] = input("SMTP порт: ")
    config["EMAIL"]["SMTP_USER"] = input("SMTP пользователь: ")
    config["EMAIL"]["SMTP_PASSWORD"] = input("SMTP пароль: ")

    # Запрос данных IMAP
    config["EMAIL"]["IMAP_SERVER"] = input("IMAP сервер: ")
    config["EMAIL"]["IMAP_USER"] = input("IMAP пользователь: ")
    config["EMAIL"]["IMAP_PASSWORD"] = input("IMAP пароль: ")

    # Email основного сервера
    config["MAIN_SERVER"]["MAIN_SERVER_EMAIL"] = input("Email основного сервера: ")

    # Установка флага и сохранение
    config["FLAG"]["FLAG"] = "TRUE"
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)
    print("Данные успешно сохранены в config.ini.")
