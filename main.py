from flask import Flask, request
from user_agents import parse
import re
import requests

app = Flask(__name__)

@app.route("/")
def collect_info():
    ip_address = request.remote_addr
    user_agent = request.headers.get("User-Agent")
    user_agent_parsed = parse(user_agent)
    browser_name = user_agent_parsed.browser.family
    browser_version = user_agent_parsed.browser.version_string
    build_number = None
    build_match = re.search(r"Build/([\w\d]+)", user_agent)
    if build_match:
        build_number = build_match.group(1)
    language = request.headers.get("Accept-Language", "Не указан")
    referer = request.headers.get("Referer", "Нет данных")
    geolocation = "Не определено"
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}/json")
        if response.status_code == 200:
            location_data = response.json()
            geolocation = f"{location_data.get('city', 'Неизвестный город')}, {location_data.get('region', 'Неизвестный регион')}, {location_data.get('country', 'Неизвестная страна')}"
    except:
        geolocation = "Ошибка при получении данных"
    device_info = {
        "IP-адрес": ip_address,
        "Тип устройства": "Мобильное" if user_agent_parsed.is_mobile else "Компьютер",
        "ОС": str(user_agent_parsed.os),
        "Браузер": f"{browser_name} (версия {browser_version})",
        "Номер сборки": build_number if build_number else "Не указан",
        "Язык устройства": language,
        "Геолокация": geolocation,
        "Referer": referer
    }
    print("Получена информация о пользователе:")
    for key, value in device_info.items():
        print(f"{key}: {value}")
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Информация</title>
        <script>
            function collectClientInfo() {
                const screenResolution = `${window.screen.width}x${window.screen.height}`;
                const windowSize = `${window.innerWidth}x${window.innerHeight}`;
                const platform = navigator.platform;
                const darkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
                const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
                const connectionType = connection ? connection.effectiveType : "Неизвестно";
                const maxDownlink = connection ? connection.downlink : "Неизвестно";
                fetch("/client_info", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        screenResolution,
                        windowSize,
                        platform,
                        darkMode,
                        connectionType,
                        maxDownlink
                    })
                });
            }
            function testInternetSpeed() {
                const imageUrl = "https://via.placeholder.com/1024";
                const startTime = Date.now();
                const image = new Image();
                image.onload = function () {
                    const endTime = Date.now();
                    const duration = (endTime - startTime) / 1000;
                    const bitsLoaded = 1024 * 8;
                    const speedMbps = (bitsLoaded / duration) / (1024 * 1024);
                    console.log(`Скорость: ${speedMbps.toFixed(2)} Мбит/сек`);
                    fetch("/internet_speed", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ speed: speedMbps.toFixed(2) })
                    });
                };
                image.onerror = function () {
                    console.log("Не удалось измерить скорость интернета");
                };
                image.src = imageUrl + "?t=" + Date.now();
            }
            window.onload = function() {
                collectClientInfo();
                testInternetSpeed();
            };
        </script>
    </head>
    <style>
        body {
            margin: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            font-family: Arial, sans-serif;
        }
        #message {
            display: none;
            font-size: 4rem;
            font-weight: bold;
            text-align: center;
        }
    </style>
</head>
<body>
    <div id="infoText">Спасибо за вашу информацию, мы готовы к отправке вашей информации</div>
    <button id="cancelButton">Отмена</button>
    <div id="message" style="display: none;">Поздно</div>
    <script>
        const cancelButton = document.getElementById('cancelButton');
        const message = document.getElementById('message');
        const infoText = document.getElementById('infoText');
        cancelButton.addEventListener('click', () => {
            cancelButton.style.display = 'none';
            infoText.style.display = 'none';
            message.style.display = 'block';
        });
    </script>
</body>
    """

@app.route("/client_info", methods=["POST"])
def save_client_info():
    data = request.get_json()
    screen_resolution = data.get("screenResolution", "Неизвестно")
    window_size = data.get("windowSize", "Неизвестно")
    platform = data.get("platform", "Неизвестно")
    dark_mode = data.get("darkMode", "Неизвестно")
    connection_type = data.get("connectionType", "Неизвестно")
    max_downlink = data.get("maxDownlink", "Неизвестно")
    print("Информация с клиента:")
    print(f"Разрешение экрана: {screen_resolution}")
    print(f"Размер окна: {window_size}")
    print(f"Платформа: {platform}")
    print(f"Тёмный режим: {'Да' if dark_mode else 'Нет'}")
    print(f"Тип подключения: {connection_type}")
    print(f"Макс. скорость соединения: {max_downlink} Мбит/с")
    return "Информация клиента успешно получена", 200

@app.route("/internet_speed", methods=["POST"])
def save_speed():
    data = request.get_json()
    internet_speed = data.get("speed", "Не определено")
    print(f"Скорость интернета пользователя: {internet_speed} Мбит/сек")
    return "Скорость интернета успешно получена", 200

@app.route("/android_info")
def android_info():
    kotlin_code = '''
import android.os.Build
import android.util.Log

fun getDeviceInfo() {
    val manufacturer = Build.MANUFACTURER
    val model = Build.MODEL
    val osVersion = Build.VERSION.RELEASE
    val architecture = System.getProperty("os.arch")
    val process = Runtime.getRuntime().exec("uname -r")
    val kernelVersion = process.inputStream.bufferedReader().readText().trim()
    Log.d("DeviceInfo", "Производитель: $manufacturer")
    Log.d("DeviceInfo", "Модель: $model")
    Log.d("DeviceInfo", "ОС: Android $osVersion")
    Log.d("DeviceInfo", "Архитектура: $architecture")
    Log.d("DeviceInfo", "Ядро: $kernelVersion")
}
    '''
    return f"<pre>{kotlin_code}</pre>"

if __name__ == "__main__":
    app.run(debug=True)
