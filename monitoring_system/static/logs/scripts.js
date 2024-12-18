    document.addEventListener("DOMContentLoaded", function () {
        const detailsDiv = document.getElementById('device-details');
        const metricsDiv = document.getElementById('metrics-table');
        const logsTable = document.querySelector('table tbody'); // Селектор для таблицы с логами

        let currentDeviceId = null;  // Храним текущий выбранный IP-адрес

        // Функция для обновления таблицы с логами
        function updateLogs() {
            $.ajax({
                url: "/logs/", // URL для получения логов
                method: "GET",
                success: function (data) {
                    let tableHtml = '';
                    data.logs.forEach(log => {
                        // Преобразуем ISO дату в нужный формат
                        const timestamp = new Date(log.timestamp);
                        const formattedTimestamp = timestamp.toISOString().slice(0, 19).replace("T", " ");  // Преобразуем ISO в нужный формат

                        tableHtml += `
                    <table>

                    <tr>
                        <td>${log.ip_address}</td>
                        <td>${log.ram_usage}</td>
                        <td>${formattedTimestamp}</td>  <!-- Здесь используем отформатированное время -->
                        <td>${log.cpu_load}</td>
                        <td>${log.log_message}</td>
                        <td>${log.temperature}</td>
                        </tr>
                    </table>
                `;
                    });
                    logsTable.innerHTML = tableHtml;
                },
                error: function () {
                    console.error('Ошибка при обновлении логов');
                }
            });
        }

        // Функция для обновления метрик для конкретного устройства
        function updateMetrics(deviceId) {
            if (!deviceId) return;  // Если устройство не выбрано, ничего не делаем

    // Загружаем метрики устройства
    fetch(`/metrics/${deviceId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                metricsDiv.innerHTML = `<p>${data.error}</p>`;
                return;
            }

            // Создаем таблицу с метриками
            const columns = [
                        "Время сбора",
                        "Нагрузка процессора (%)",
                        "Нагрузка оперативной памяти (%)",
                        "Отправлено байт по сети",
                        "Получено байт по сети",
                        "Температура (°C)"
            ];
            const rows = data.rows;

            if (!rows || rows.length === 0) {
                showErrorPage();
                return;
            }

            let tableHtml = '<table>';
            tableHtml += '<caption class="cap"><b>Метрики устройства</b></caption>';
            tableHtml += '<thead><tr>';
            columns.forEach(column => {
                tableHtml += `<th>${column}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';

            rows.forEach(row => {
                tableHtml += '<tr>';
                row.forEach((cell, index) => {
                    // Если ячейка содержит временную метку, преобразуем ее в нужный формат
                    if (index === 0 && cell) {  // Предположим, что первая колонка - это timestamp
                        const timestamp = new Date(cell);
                        const formattedTimestamp = timestamp.toISOString().slice(0, 19).replace("T", " ");  // Преобразуем ISO в нужный формат
                        tableHtml += `<td>${formattedTimestamp}</td>`;
                    } else {
                        tableHtml += `<td>${cell}</td>`;
                    }
                });
                tableHtml += '</tr>';
            });

            tableHtml += '</tbody></table>';
            metricsDiv.innerHTML = tableHtml;
        });
}

                    // Используем делегирование событий для обработки кликов по кнопкам IP-адресов
                    document.querySelector('.list-group').addEventListener('click', function (event) {
                        if (event.target && event.target.classList.contains('ip-button')) {
                            const deviceId = event.target.dataset.deviceId;

                            // Обновляем текущий выбранный IP-адрес
                            currentDeviceId = deviceId;

                            // Загружаем характеристики устройства
                            fetch(`/device-details/${deviceId}/`)
                                .then(response => response.json())
                                .then(data => {
                                    if (data.error) {
                                        detailsDiv.innerHTML = `<p>${data.error}</p>`;
                                        return;
                                    }
                                    detailsDiv.innerHTML = `
                            <table>
                                <caption class="cap"><b>Характеристики устройства</b></caption>
                                <tr>
                                    <th>IP адрес</th>
                                    <td>${data.ip_address}</td>
                                </tr>
                                <tr>
                                    <th>Модель процессора</th>
                                    <td>${data.cpu_info}</td>
                                </tr>
                                <tr>
                                    <th>Количество ОЗУ</th>
                                    <td>${data.ram_info}</td>
                                </tr>
                                <tr>
                                    <th>Объём жёсткого диска</th>
                                    <td>${data.disk_space}</td>
                                </tr>
                                <tr>
                                    <th>Модель видеокарты</th>
                                    <td>${data.gpu_info}</td>
                                </tr>
                                <tr>
                                    <th>Операционная система</th>
                                    <td>${data.os_info}</td>
                                </tr>
                                <tr>
                                    <th>Тип устройства</th>
                                    <td>${data.type}</td>
                                </tr>
                            </table>
                        `;
                                });

                            // Обновляем метрики для выбранного устройства
                            updateMetrics(deviceId);
                        }
                    });

                    // Имитация клика по первой кнопке, если устройства уже есть на странице
                    const buttons = document.querySelectorAll('.ip-button');
                    if (buttons.length > 0) {
                        buttons[0].click(); // Имитируем клик по первому устройству
                    }

                    // Обновляем таблицу метрик для выбранного устройства каждые 10 секунд
                    setInterval(function () {
                        // Обновляем метрики только для выбранного устройства
                        if (currentDeviceId) {
                            updateMetrics(currentDeviceId);
                        }
                        updateLogs();
                    }, 10000); // 10 секунд

                });

// Проверка на ошибку подключения БД
 function showErrorPage() {
     document.body.innerHTML = `
    <header>
        <b>Remote Monitoring System</b>
    </header>
     <div class="error-bd">
     <h1>Ошибка подключения к базе данных</h1>
    <p>К сожалению, мы не можем подключиться к базе данных в данный момент</p>
    <p>Перезагрузите страницу или проверьте правильность подключения базы данных</p>
     </div>
     <footer>
        <p><b>ХГУ ИТИ, 2024 год</b></p>
    </footer>
     `;
 }
     //Условие при ошибке подключения к БД
     const dbConnectionSuccessful = true;
     if (dbConnectionSuccessful == false){
         showErrorPage();
     }


