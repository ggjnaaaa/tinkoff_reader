# tinkoff_auth.py

# Стандартные библиотеки Python
import re

# Модули проекта
from utils import write_input, click_button, check_for_error_message
from exceptions import LoginRedirectError

# Функция для извлечения только цифр из номера телефона
def extract_digits(phone_number):
    return re.sub(r'\D', '', phone_number)  # Удаляем все символы, кроме цифр

# Функция для получения номера телефона со страницы,,
def get_phone_digits_from_page(driver):
    # Исходный код страницы
    page_source = driver.page_source

    # Поиск номера телефона с помощью регулярного выражения
    match = re.search(r'\+7\s?\d{3}\s?\*{3}[\s\-]\*{2}[\s\-]\d{2}', page_source)

    # Возвращаем найденный номер телефона как строку
    if match:
        return extract_digits(match.group())
    else:
        return None

def login_via_sms(driver, phone_number):
    # Логика для входа через СМС
    error_selector = 'p[automation-id="server-error"]'
    submit_button_selector = 'button[automation-id="button-submit"]'

    try:
        # Извлекаем цифры из обоих номеров
        extracted_digits = extract_digits(get_phone_digits_from_page(driver))
        input_digits = extract_digits(phone_number)

        # Сравниваем цифры
        if extracted_digits[:3] == input_digits[:3] and extracted_digits[-2:] == input_digits[-2:]:
            # Подтверждение входа через смс
            click_button(driver, submit_button_selector)

            # Ввод кода из СМС
            while True:
                sms_code = input("Введите код из смс: ")
                write_input(driver, 'input[automation-id="otp-input"]', sms_code)
                if not check_for_error_message(driver=driver, error_selector=error_selector):
                    break
                else:
                    print("Неверный код, повторите попытку.")
        else:
            # Отмена входа по смс
            click_button(driver, 'button[automation-id="reset-button"]')
            raise LoginRedirectError('Ошибка входа по смс: Номера не совпадают. Требуется новый вход через пароль.')
    except Exception as e:
        raise Exception(f"Ошибка при входе через смс-код: {str(e)}") from e

def login_via_otp(driver, otp_code):
    # Логика для входа через OTP
    error_selector = 'p[automation-id="server-error"]'

    try:
        # Ввод OTP
        write_input(driver, 'input[automation-id="pin-code-input-0"]', otp_code)
        if check_for_error_message(driver=driver, error_selector=error_selector):
            raise LoginRedirectError('Ошибка входа по OTP: Временный пароль неверный. Требуется новый вход через пароль.')
    except Exception as e:
        # Отмена входа по OTP
        raise Exception(f"Ошибка при входе через OTP: {str(e)}") from e

def login_via_password(driver, phone_number, password, otp_code):
    # Логика входа через пароль
    error_selector = 'p[automation-id="server-error"]'
    submit_button_selector = 'button[automation-id="button-submit"]'

    try:
        # Ввод номера телефона
        write_input(driver, 'input[name="phone"]', phone_number)
        click_button(driver, submit_button_selector)
        if check_for_error_message(driver=driver, error_selector=error_selector):
            raise ValueError("Указан неверный номер телефона")
        
        # Ввод кода из СМС
        while True:
            sms_code = input("Введите код из смс: ")
            write_input(driver, 'input[automation-id="otp-input"]', sms_code)
            if not check_for_error_message(driver=driver, error_selector=error_selector):
                break
            else:
                print("Неверный код, повторите попытку.")

        # Ввод пароля
        if 'Введите пароль' in driver.page_source:
            write_input(driver, 'input[automation-id="password-input"]', password)
            click_button(driver, submit_button_selector)
        if check_for_error_message(driver=driver, error_selector=error_selector):
            raise ValueError("Указан неверный пароль")

        # Ввод временного кода
        if 'Придумайте код' in driver.page_source:
            write_input(driver, 'input[automation-id="pin-code-input-0"]', otp_code)
            click_button(driver, submit_button_selector)
        elif 'Расходы' in driver.page_source:
            return
        else:
            raise Exception('Неизвестная страница после ввода пароля.')
    except Exception as e:
        raise Exception(f"Ошибка при входе через пароль: {str(e)}") from e
