# exceptions.py

class LoginRedirectError(Exception):
    def __init__(self, message="Смена типа входа"):
        super().__init__(message)