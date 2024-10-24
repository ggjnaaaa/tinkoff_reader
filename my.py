import threading
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Тайм-аут для неактивности, после которого браузер будет закрыт (в секундах)
BROWSER_TIMEOUT = 10  # 2 минуты

# Флаг активности
last_interaction_time = time.time()

# Создаём браузер
def create_browser():
    global driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    return driver

# Функция для сброса времени последнего взаимодействия
def reset_interaction_time():
    global last_interaction_time
    last_interaction_time = time.time()

# Функция для закрытия браузера после тайм-аута
def close_browser_after_timeout():
    global last_interaction_time, driver
    while True:
        if time.time() - last_interaction_time > BROWSER_TIMEOUT:
            print("Время ожидания истекло, закрываю браузер...")
            driver.quit()
            break
        time.sleep(5)  # Проверяем каждые 5 секунд

# Основной код работы с браузером
def main():
    # Создаём браузер
    browser = create_browser()

    # Запускаем поток для проверки тайм-аута
    timer_thread = threading.Thread(target=close_browser_after_timeout)
    timer_thread.start()

    try:
        # Пример работы с браузером
        #browser.get("https://www.tbank.ru/")

        # Каждое действие с браузером нужно обновлять время последнего взаимодействия
        reset_interaction_time()
        
        # Например, ждём на странице некоторое время
        time.sleep(2)

        print('проснулся')
        
        # Ещё одно взаимодействие, сбросим таймер
        reset_interaction_time()
        #browser.get("https://www.example.com/")
    
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        browser.quit()
        timer_thread.join()  # Дожидаемся завершения потока

if __name__ == "__main__":
    main()