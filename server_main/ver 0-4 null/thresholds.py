import configparser

CONFIG_FILE = "thresholds.ini"


def load_thresholds():
    config = configparser.ConfigParser()
    if not config.read(CONFIG_FILE):
        # Если файл отсутствует, создаем его с дефолтными значениями
        with open(CONFIG_FILE, 'w') as configfile:
            config["THRESHOLDS"] = {
                "CPU_LOAD_LIMIT": "85",
                "RAM_USAGE_LIMIT": "90",
                "TEMPERATURE_LIMIT": "80"
            }
            config.write(configfile)
        print("Создан файл thresholds.ini с дефолтными значениями порогов.")

    config.read(CONFIG_FILE)
    thresholds = {
        "CPU_LOAD_LIMIT": int(config["THRESHOLDS"]["CPU_LOAD_LIMIT"]),
        "RAM_USAGE_LIMIT": int(config["THRESHOLDS"]["RAM_USAGE_LIMIT"]),
        "TEMPERATURE_LIMIT": int(config["THRESHOLDS"]["TEMPERATURE_LIMIT"])
    }
    return thresholds
