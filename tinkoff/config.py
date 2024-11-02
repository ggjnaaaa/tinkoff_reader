import utils.tinkoff.browser_manager as BrowserManager

# Тайм-аут для неактивности, после которого браузер будет закрыт (в секундах)
BROWSER_TIMEOUT: int = 180  # 3 минута
EXPENSES_URL: str = f"https://www.tbank.ru/auth/login/?redirectTo=%2Fevents%2Ffeed%2F&redirectType="
DOWNLOAD_DIRECTORY: str = None
PATH_TO_CHROME_PROFILE: str = None

# Работа с драйвером
browser_instance: BrowserManager = None

# Селекторы
# Селекторы полей
error_selector = 'p[automation-id="server-error"]'  # Объект с выводом ошибки
timer_selector = 'span[automation-id="left-time"]'  # Таймер на вводе смс

# Селекторы кнопок
submit_button_selector = 'button[automation-id="button-submit"]'  # Кнопка подтверждения
reset_button_selector = 'button[automation-id="reset-button"]'  # Кнопка отмены
cancel_button_selector = 'button[automation-id="cancel-button"]'  # Кнопка отмены (на странице где ПРЕДЛАГАЮТ отправить смс)
resend_sms_button_selector = 'button[automation-id="resend-button"]'  # Кнопка повторной отправки смс

# Селекторы инпутов
phone_input_selector = 'input[name="phone"]'  # Инпут номера телефона
sms_code_input_selector = 'input[automation-id="otp-input"]'  # Инпут смс-кода
pin_code_input_selector = 'input[automation-id="pin-code-input-0"]'  # Инпут временного кода
password_input_selector = 'input[automation-id="password-input"]'  # Инпут пароля
otp_input_selector = 'input[automation-id="otp-input"]'  # Инпут временного пароля

