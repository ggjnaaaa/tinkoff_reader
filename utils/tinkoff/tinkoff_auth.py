﻿# tinkoff_auth.py

# Стандартные библиотеки Python
import time, re

# Сторонние библиотеки
from fastapi import HTTPException

# Модули проекта
from utils.tinkoff.browser_utils import (
    write_input, 
    click_button, 
    get_text,
    check_for_error_message, 
    detect_page_type, 
    PageType
)
import tinkoff.config as config

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

async def paged_login(driver, user_input, retries=3):
    detected_page = await detect_page_type(driver)
    print(f"тип нынешней страницы: {detected_page}")

    if detected_page:
        try:
            await route_login_by_page_type(driver, detected_page, user_input)
        except:
            raise
        
        attempt_new_page = 1
        while attempt_new_page <= retries:
            new_detected_page = await detect_page_type(driver)
            print(f"тип следующей страницы: {new_detected_page}")
            if new_detected_page and new_detected_page != detected_page:
                return new_detected_page
            else:
                attempt_new_page += 1
                print(f"Не удалось определить тип следующей страницы. Осталось попыток: {retries - attempt_new_page + 1}")
                time.sleep(1)
    else:
        print(f"Не удалось определить тип страницы.")
    raise HTTPException(status_code=500, detail="Ошибка входа в тинькофф. Пожалуйста, войдите заново.")

async def route_login_by_page_type(driver, detected_page, user_input):
    try:
        if detected_page == PageType.LOGIN_PHONE:
            await phone_page(driver=driver, phone_number=user_input)
        elif detected_page == PageType.LOGIN_INPUT_SMS_CODE:
            await sms_page(driver=driver, sms_code=user_input)
        elif detected_page == PageType.LOGIN_PASSWORD:
            await password_page(driver=driver, password=user_input)
        elif detected_page == PageType.LOGIN_CREATE_OTP:
            await create_otp_page(driver=driver, otp_code=user_input)
        elif detected_page == PageType.LOGIN_OTP:
            await otp_page(driver=driver, otp_code=user_input)
    except:
        raise
    
async def phone_page(driver, phone_number):
    try:
        # Ввод номера телефона
        await write_input(driver, phone_input_selector, phone_number)
        await click_button(driver, submit_button_selector)
        error_message = await check_for_error_message(driver=driver, error_selector=error_selector)

        if error_message:
            raise HTTPException(status_code=400, detail=error_message)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка на странице ввода номера телефона: {str(e)}")

async def sms_page(driver, sms_code):
    try:
        # Ввод кода из СМС
        while True:
            await write_input(driver, sms_code_input_selector, sms_code)
            error_message = await check_for_error_message(driver=driver, error_selector=error_selector)

            if not error_message:
                break
            else:
                raise HTTPException(status_code=400, detail=error_message)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при вводе смс-кода: {str(e)}")
    
async def password_page(driver, password):
    try:
        # Ввод пароля
        await write_input(driver, password_input_selector, password)
        await click_button(driver, submit_button_selector)
        error_message = await check_for_error_message(driver=driver, error_selector=error_selector)

        if error_message:
            raise HTTPException(status_code=400, detail=error_message)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при вводе пароля: {str(e)}")
    
async def create_otp_page(driver, otp_code):
    try:
        # Ввод временного кода
        await write_input(driver, pin_code_input_selector, otp_code)
        await click_button(driver, submit_button_selector)
        error_message = await check_for_error_message(driver=driver, error_selector=error_selector)

        if error_message:
            raise HTTPException(status_code=400, detail=error_message)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при создании нового временного кода: {str(e)}")
    
async def otp_page(driver, otp_code):
    try:
        # Ввод временного кода
        await write_input(driver, pin_code_input_selector, otp_code)
        error_message = await check_for_error_message(driver=driver, error_selector=error_selector)

        if error_message:
            raise HTTPException(status_code=400, detail=error_message)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при вводе временного кода: {str(e)}")

async def close_login_via_sms_page(driver):
    try:
        # Отмена входа по смс
        await click_button(driver, reset_button_selector)
        time.sleep(1)
        return await detect_page_type(driver)
    except Exception as e:
        raise Exception(f"Ошибка при закрытии входа через смс-код: {str(e)}")

async def get_user_name_from_otp_login():
    greeting_text = await get_text(config.page, "[automation-id='form-title']")  # Берем текст из приветствия

    # Регулярное выражение для поиска имени после "Здравствуйте, "
    match = re.search(r"Здравствуйте, (.+)!", greeting_text)
    if match:
        user_name = match.group(1)  # Извлекаем первую группу, которая содержит имя
    else:
        user_name = 'Пользователь'

    return user_name