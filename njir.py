import requests
import sys
import threading
import random
import argparse
import os
import signal
from colorama import Fore, init
from concurrent.futures import ThreadPoolExecutor

init(autoreset=True)

print(Fore.GREEN + """

    ___       __          _       _______           __
   /   | ____/ /___ ___  (_)___  / ____(_)___  ____/ /__  _____
  / /| |/ __  / __ `__ \/ / __ \/ /_  / / __ \/ __  / _ \/ ___/
 / ___ / /_/ / / / / / / / / / / __/ / / / / / /_/ /  __/ /
/_/  |_\__,_/_/ /_/ /_/_/_/ /_/_/   /_/_/ /_/\__,_/\___/_/

            """ + Fore.GREEN + "[ " + Fore.WHITE + "www.kirovgroup.org" + Fore.GREEN + " ]")
print()


найдено = threading.Event()
замок = threading.Lock()
прокси_список = []

агенты_пользователя = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Googlebot/2.1 (+http://www.google.com/bot.html)"
]

def загрузить_прокси(файл):
    try:
        with open(файл, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}❌ Файл прокси '{файл}' не найден!")
        sys.exit(1)

def проверить_админ_путь(цель, путь):
    if найдено.is_set():
        return

    url = f"{цель}/{путь}"
    заголовки = {"User-Agent": random.choice(агенты_пользователя)}

    прокси = {}
    if прокси_список:
        адрес_прокси = random.choice(прокси_список)
        прокси = {"http": f"http://{адрес_прокси}", "https": f"http://{адрес_прокси}"}

    try:
        ответ = requests.get(url, headers=заголовки, timeout=5, proxies=прокси)
        статус = ответ.status_code

        with замок:
            if статус == 200 and not найдено.is_set():
                найдено.set()
                print(f"{Fore.GREEN}{url} [200] > ГОТОВО")
                print(f"\n{Fore.CYAN}[•] Найдена админ-панель: {url}\n")
                os.kill(os.getpid(), signal.SIGTERM)

            elif статус == 404:
                print(f"{Fore.RED}{url} [404]")
            else:
                print(f"{Fore.YELLOW}{url} [{статус}]")
    except:
        with замок:
            print(f"{Fore.RED}{url} [ОШИБКА]")

def главная():
    парсер = argparse.ArgumentParser()
    парсер.add_argument('--target', required=True, help='Целевой URL')
    парсер.add_argument('--threads', type=int, default=10, help='Количество потоков')
    парсер.add_argument('--proxy', help='Файл со списком прокси')
    аргументы = парсер.parse_args()

    цель = аргументы.target.rstrip('/')
    потоки = аргументы.threads

    if аргументы.proxy:
        global прокси_список
        прокси_список = загрузить_прокси(аргументы.proxy)

    try:
        with open("admin_list.txt", "r") as f:
            пути = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}❌ Файл 'admin_list.txt' не найден!")
        sys.exit(1)

    print(f"\n{Fore.CYAN}🟡 Сканирование {len(пути)} путей по {цель} с {потоки} потоками...\n")

    with ThreadPoolExecutor(max_workers=потоки) as исполнитель:
        for путь in пути:
            if найдено.is_set():
                break
            исполнитель.submit(проверить_админ_путь, цель, путь)

if __name__ == "__main__":
    главная()
