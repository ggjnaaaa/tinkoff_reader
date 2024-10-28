# tinkoff_auth.py

# Стандартные библиотеки Python
import re

# Сторонние библиотеки
from fastapi import HTTPException

# Модули проекта
from servises.browser_utils import write_input, click_button, check_for_error_message, detect_page_type, PageType

# Селекторы полей
error_selector = 'p[automation-id="server-error"]'  # Объект с выводом ошибки

# Селекторы кнопок
submit_button_selector = 'button[automation-id="button-submit"]'  # Кнопка подтверждения
reset_button_selector = 'button[automation-id="reset-button"]'  # Кнопка отмены

# Селекторы инпутов
phone_input_selector = 'input[name="phone"]'  # Инпут номера телефона
sms_code_input_selector = 'input[automation-id="otp-input"]'  # Инпут смс-кода
pin_code_input_selector = 'input[automation-id="pin-code-input-0"]'  # Инпут временного кода
password_input_selector = 'input[automation-id="password-input"]'  # Инпут пароля
otp_input_selector = 'input[automation-id="otp-input"]'  # Инпут временного пароля

def paged_login(driver, user_input, retries=3):
    attempt_current_page = 0
    while attempt_current_page < retries:
        detected_page = detect_page_type(driver)
        print(f"тип нынешней страницы: {detected_page}")

        if detected_page:
            result = route_login_by_page_type(driver, detected_page, user_input)
            if result:
                return result

            attempt_new_page = 0
            while attempt_new_page < retries:
                new_detected_page = detect_page_type(driver)
                print(f"тип следующей страницы: {new_detected_page}")
                if new_detected_page and new_detected_page != detected_page:
                    return {"status": "success", "next_page_type": new_detected_page.name}
                else:
                    attempt_new_page += 1
                    print(f"Не удалось определить тип следующей страницы. Осталось попыток: {retries - attempt_current_page}")
        else:
            attempt_current_page += 1
            print(f"Не удалось определить тип страницы. Осталось попыток: {retries - attempt_current_page}")
    return {"status": 500, "message": "Проблемы с определением типа страницы"}

def route_login_by_page_type(driver, detected_page, user_input):
    try:
        if detected_page == PageType.LOGIN_PHONE:
            phone_page(driver=driver, phone_number=user_input)
        elif detected_page == PageType.LOGIN_INPUT_SMS_CODE:
            sms_page(driver=driver, sms_code=user_input)
        elif detected_page == PageType.LOGIN_PASSWORD:
            password_page(driver=driver, password=user_input)
        elif detected_page == PageType.LOGIN_CREATE_OTP:
            create_otp_page(driver=driver, otp_code=user_input)
        elif detected_page == PageType.LOGIN_OTP:
            otp_page(driver=driver, otp_code=user_input)
    except HTTPException as e:
        return {"status": e.status_code, "detail": e.detail}
    except Exception:
        raise
    
def phone_page(driver, phone_number):
    try:
        # Ввод номера телефона
        write_input(driver, phone_input_selector, phone_number)
        click_button(driver, submit_button_selector)
        error_message = check_for_error_message(driver=driver, error_selector=error_selector)
        if error_message:
            raise HTTPException(status_code=400, detail=error_message.text)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка на странице ввода номера телефона: {str(e)}")

def sms_page(driver, sms_code):
    try:
        # Ввод кода из СМС
        while True:
            write_input(driver, sms_code_input_selector, sms_code)
            error_message = check_for_error_message(driver=driver, error_selector=error_selector)
            if not error_message:
                break
            else:
                raise HTTPException(status_code=400, detail=error_message.text)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при вводе смс-кода: {str(e)}")
    
def password_page(driver, password):
    try:
        # Ввод пароля
        write_input(driver, password_input_selector, password)
        click_button(driver, submit_button_selector)
        error_message = check_for_error_message(driver=driver, error_selector=error_selector)
        if error_message:
            raise HTTPException(status_code=400, detail=error_message.text)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при вводе пароля: {str(e)}")
    
def create_otp_page(driver, otp_code):
    try:
        # Ввод временного кода
        write_input(driver, pin_code_input_selector, otp_code)
        click_button(driver, submit_button_selector)
        error_message = check_for_error_message(driver=driver, error_selector=error_selector)
        if error_message:
            raise HTTPException(status_code=400, detail=error_message.text)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при создании нового временного кода: {str(e)}")
    
def otp_page(driver, otp_code):
    try:
        # Ввод временного кода
        write_input(driver, pin_code_input_selector, otp_code)
        error_message = check_for_error_message(driver=driver, error_selector=error_selector)
        if error_message:
            raise HTTPException(status_code=400, detail=error_message.text)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при вводе временного кода: {str(e)}")

def close_login_via_sms_page(driver):
    try:
        # Отмена входа по смс
        click_button(driver, reset_button_selector)
    except Exception as e:
        raise Exception(f"Ошибка при закрытии входа через смс-код: {str(e)}")
    
def request_new_sms(driver):
    try:
        click_button()
    except:
        raise