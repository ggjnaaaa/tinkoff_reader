﻿# tinkoff_auth.py

# Стандартные библиотеки Python
import time, re, asyncio

# Сторонние библиотеки
from fastapi import HTTPException

# Модули проекта
from utils.tinkoff.browser_utils import (
    write_input, 
    click_button, 
    get_text,
    detect_page_type, 
    detect_page_type_after_url_change,
    PageType
)
from utils.tinkoff.browser_manager import BrowserManager
from config import (
    submit_button_selector,
    error_selector,
    reset_button_selector,
    phone_input_selector,
    sms_code_input_selector,
    pin_code_input_selector,
    password_input_selector,
)


async def paged_login(browser: BrowserManager, user_input, retries=3):
    detected_page = await detect_page_type(browser)
    print(f"тип нынешней страницы: {detected_page}")

    if detected_page:
        try:
            await route_login_by_page_type(browser, detected_page, user_input)
        except:
            raise
        
        attempt_new_page = 1
        while attempt_new_page <= retries:
            new_detected_page = await detect_page_type(browser)
            print(f"тип следующей страницы: {new_detected_page}")
            if new_detected_page and new_detected_page != detected_page:
                return detected_page, new_detected_page
            else:
                if not browser or not browser.page:
                    raise HTTPException(status_code=500, detail="Ошибка входа в тинькофф. Пожалуйста, войдите заново.")
                attempt_new_page += 1
                print(f"Не удалось определить тип следующей страницы. Осталось попыток: {retries - attempt_new_page + 1}")
    else:
        print(f"Не удалось определить тип страницы.")
    raise HTTPException(status_code=307, detail="Ошибка входа в тинькофф. Пожалуйста, войдите заново.")

async def route_login_by_page_type(browser: BrowserManager, detected_page, user_input):
    try:
        if detected_page == PageType.LOGIN_PHONE:
            await phone_page(browser=browser, phone_number=user_input)
        elif detected_page == PageType.LOGIN_INPUT_SMS_CODE:
            await sms_page(browser=browser, sms_code=user_input)
        elif detected_page == PageType.LOGIN_PASSWORD:
            await password_page(browser=browser, password=user_input)
        elif detected_page == PageType.LOGIN_CREATE_OTP:
            await create_otp_page(browser=browser, otp_code=user_input)
        elif detected_page == PageType.LOGIN_OTP:
            await otp_page(browser=browser, otp_code=user_input)
        
        error_message = await check_for_error_message(browser, 2)
        if error_message:
            raise HTTPException(status_code=400, detail=error_message)
    except:
        raise
    
async def phone_page(browser: BrowserManager, phone_number: str):
    try:
        await input_and_click_submit(browser, phone_input_selector, phone_number)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка на странице ввода номера телефона: {str(e)}")

async def sms_page(browser: BrowserManager, sms_code):
    try:
        # Ввод кода из СМС
        await write_input(browser.page, sms_code_input_selector, sms_code)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при вводе смс-кода: {str(e)}")
    
async def password_page(browser: BrowserManager, password):
    try:
        await input_and_click_submit(browser, password_input_selector, password)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при вводе пароля: {str(e)}")
    
async def create_otp_page(browser: BrowserManager, otp_code):
    try:
        for i in range(4):
            selector = pin_code_input_selector.replace("0", str(i))
            await write_input(browser.page, selector, otp_code[i])
        await click_button(browser.page, submit_button_selector)
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при создании нового временного кода: {str(e)}")
    
async def otp_page(browser: BrowserManager, otp_code: str):
    try:
        for i in range(4):
            selector = pin_code_input_selector.replace("0", str(i))
            await write_input(browser.page, selector, otp_code[i])
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Ошибка при вводе временного кода: {str(e)}")

async def close_login_via_sms_page(browser: BrowserManager):
    try:
        initial_url = browser.page.url
        # Отмена входа по смс
        await click_button(browser.page, reset_button_selector)
        time.sleep(1)
        return await detect_page_type_after_url_change(browser, initial_url)
    except Exception as e:
        raise Exception(f"Ошибка при закрытии входа через смс-код: {str(e)}")

async def get_user_name_from_otp_login(browser: BrowserManager):
    greeting_text = await get_text(browser.page, "[automation-id='form-title']")  # Берем текст из приветствия

    # Регулярное выражение для поиска имени после "Здравствуйте, "
    match = re.search(r"Здравствуйте, (.+)!", greeting_text)
    if match:
        user_name = match.group(1)  # Извлекаем первую группу, которая содержит имя
    else:
        user_name = 'Пользователь'

    return user_name

async def input_and_click_submit(browser: BrowserManager, input_selector: str, user_input: str, timeout: int = 5):
    try:
        page = browser.page

        # Ввод пароля
        await write_input(page, input_selector, user_input, timeout)
        await click_button(page, submit_button_selector, timeout)
    except:
        raise

# Асинхронная функция для проверки наличия сообщения об ошибке
async def check_for_error_message(browser: BrowserManager, timeout=5):
    try:
        browser.reset_interaction_time()
        error = await get_text(browser.page, error_selector, timeout=timeout)
        return error
    except Exception:
        return None