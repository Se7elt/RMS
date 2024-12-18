import configparser
import smtplib
import imaplib
import os

CONFIG_FILE = "config.ini"


def save_config(config):
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        print("Файл конфигурации не найден. Требуется ввод данных.")
        create_config(config)
    else:
        config.read(CONFIG_FILE)
        if not validate_email_settings(config):
            print("Конфигурация неверна или соединение не установлено. Введите данные заново.")
            create_config(config)
    return config


def create_config(config):
    config['SMTP'] = {}
    config['IMAP'] = {}
    config['Servers'] = {}

    config['SMTP']['server'] = input("Введите SMTP сервер (например, smtp.gmail.com): ")
    config['SMTP']['port'] = input("Введите порт SMTP (например, 587): ")
    config['SMTP']['user'] = input("Введите email для SMTP: ")
    config['SMTP']['password'] = input("Введите пароль для SMTP: ")

    config['IMAP']['server'] = input("Введите IMAP сервер (например, imap.gmail.com): ")
    config['IMAP']['user'] = config['SMTP']['user']
    config['IMAP']['password'] = config['SMTP']['password']

    config['Servers']['proxy_server_email'] = input("Введите email прокси-сервера: ")
    config['Servers']['main_server_email'] = input("Введите email главного сервера: ")

    if validate_email_settings(config):
        save_config(config)
        print("Конфигурация сохранена и подтверждена.")
    else:
        print("Ошибка подключения. Проверьте данные и повторите ввод.")
        create_config(config)


def validate_email_settings(config):
    """Проверка соединения с почтовыми серверами."""
    try:
        # Проверка SMTP
        with smtplib.SMTP(config['SMTP']['server'], int(config['SMTP']['port'])) as smtp:
            smtp.starttls()
            smtp.login(config['SMTP']['user'], config['SMTP']['password'])

        # Проверка IMAP
        with imaplib.IMAP4_SSL(config['IMAP']['server']) as imap:
            imap.login(config['IMAP']['user'], config['IMAP']['password'])
        return True
    except Exception as e:
        print(f"Ошибка соединения с сервером: {e}")
        return False


config = load_config()
