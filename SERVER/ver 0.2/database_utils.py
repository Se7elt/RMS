import psycopg2
from psycopg2 import sql
from config import get_config
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def connect_db(db_name, user, password, host, port):
    try:
        connection = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        logging.info("Подключение к базе данных прошло успешно.")
        return connection
    except Exception as e:
        logging.error(f"Ошибка при подключении к базе данных: {e}")
        return None



def ensure_device_info_table(connection):
    try:
        cursor = connection.cursor()
        # SQL-запрос для проверки наличия столбцов в таблице
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'device_info' 
            AND column_name IN ('ip_address', 'cpu_info', 'ram_info', 'disk_space', 'os_info', 'gpu_info', 'type');
        """)

        # Проверяем, существуют ли все нужные столбцы
        columns = {row[0] for row in cursor.fetchall()}
        required_columns = {"ip_address", "cpu_info", "ram_info", "disk_space", "os_info", "gpu_info", "type"}

        # Если не все столбцы присутствуют, создаем или обновляем таблицу
        if columns != required_columns:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_info (
                    ip_address VARCHAR(45) PRIMARY KEY,
                    cpu_info TEXT,
                    ram_info TEXT,
                    disk_space TEXT,
                    os_info TEXT,
                    gpu_info TEXT,
                    type VARCHAR(10)
                );
            """)
            connection.commit()
            print("Таблица Device_info создана или обновлена успешно.")
        else:
            print("Таблица Device_info уже существует и имеет все нужные столбцы.")

        cursor.close()

    except Exception as e:
        print(f"Ошибка при создании таблицы Device_info: {e}")

def register_device_in_db(connection, device_info):
    try:
        with connection.cursor() as cursor:
            logging.info(f"Вставка данных в таблицу device_info: {device_info}")
            cursor.execute("""
                INSERT INTO device_info (ip_address, cpu_info, ram_info, disk_space, os_info, gpu_info, type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ip_address) DO UPDATE SET
                    cpu_info = EXCLUDED.cpu_info,
                    ram_info = EXCLUDED.ram_info,
                    disk_space = EXCLUDED.disk_space,
                    os_info = EXCLUDED.os_info,
                    gpu_info = EXCLUDED.gpu_info,
                    type = EXCLUDED.type;  -- Обновление типа устройства при конфликте
            """, (device_info["ip_address"], device_info["cpu_info"], device_info["ram_info"],
                  device_info["disk_space"], device_info["os_info"], device_info["gpu_info"], device_info["type"]))
            connection.commit()
            logging.info(f"Устройство с IP {device_info['ip_address']} добавлено.")
    except Exception as e:
        logging.error(f"Ошибка при добавлении устройства: {e}")

def create_metrics_table(connection, ip_address):
    try:
        cursor = connection.cursor()
        table_name = f"metrics_{ip_address.replace('.', '_')}"
        cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {table} (
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cpu_load_proc TEXT,
                    ram_usage_proc TEXT,
                    network_sent_bytes TEXT,
                    network_recv_bytes TEXT,
                    temperatures_C TEXT
                );
            """).format(table=sql.Identifier(table_name)))
        connection.commit()
        print(f"Таблица {table_name} для хранения метрик создана.")
    except Exception as e:
        print(f"Ошибка при создании таблицы для метрик {table_name}: {e}")

def insert_metrics_to_db(connection, ip_address, metrics):
    try:
        cursor = connection.cursor()
        table_name = f"metrics_{ip_address.replace('.', '_')}"

        # Проверим наличие ключей в словаре и инициализируем отсутствующие значения None
        fields = ["timestamp", "cpu_load_proc", "ram_usage_proc", "network_sent_bytes", "network_recv_bytes",
                  "temperatures_C"]
        for field in fields:
            if field not in metrics:
                metrics[field] = None  # Установим значение None, если ключ отсутствует
                print(f"Отсутствует метрика {field}. Установлено значение None.")

        # Вставка метрик в таблицу с указанием времени
        cursor.execute(f"""
            INSERT INTO {table_name} (timestamp, cpu_load_proc, ram_usage_proc, network_sent_bytes, network_recv_bytes, temperatures_C)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (metrics["timestamp"], metrics["cpu_load_proc"], metrics["ram_usage_proc"],
              metrics["network_sent_bytes"], metrics["network_recv_bytes"], metrics["temperatures_C"]))

        connection.commit()
        print(f"Метрики для устройства с IP {ip_address} успешно добавлены.")

    except Exception as e:
        print(f"Ошибка при добавлении метрик в таблицу {table_name}: {e}")
    finally:
        cursor.close()