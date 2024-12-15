import undetected_chromedriver as uc
import time
import json
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def is_logged_in(driver):
    """Проверяет, залогинен ли пользователь на основе куки."""
    try:
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie.get("name") == "_session":
                print("Пользователь уже залогинен.")
                return True
        print("Куки сессии не найдены.")
        return False
    except Exception as e:
        print(f"Ошибка проверки логина: {e}")
        return False

def perform_login(driver, email, password):
    """Выполняет вход, если пользователь не залогинен."""
    try:
        login_button_selector = "button[data-testid='login-button']"
        email_input_selector = "input[type='email']"
        password_input_selector = "input[type='password']"
        email_continue_button_selector = "button.continue-btn"
        password_continue_button_selector = "button._button-login-password"
        code_input_selector = "input._codeInput_p12g4_28"
        code_input_selector2 = "button._continueButton_p12g4_42"

        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, login_button_selector))
        )
        login_button.click()
        print("Кнопка 'Log in' нажата.")

        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, email_input_selector))
        )
        email_input.send_keys(email)
        print(f"Email введён: {email}")

        email_continue_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, email_continue_button_selector))
        )
        email_continue_button.click()
        print("Кнопка 'Continue' нажата после ввода email.")

        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, password_input_selector))
        )
        password_input.send_keys(password)
        print(f"Пароль введён: {'*' * len(password)}")

        password_continue_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, password_continue_button_selector))
        )
        password_continue_button.click()
        print("Кнопка 'Continue' нажата после ввода пароля.")

        code_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, code_input_selector))
        )
        code = input("Введите код из почты: ")
        code_input.send_keys(code)
        print("Код введён.")

        code_submit_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, code_input_selector2))
        )
        code_submit_button.click()
        print("Кнопка 'Continue' нажата после ввода кода.")

    except Exception as e:
        print(f"Ошибка при попытке логина: {e}")

def delete_profile_data(profile_path):
    """Удаляет данные профиля для выхода из всех аккаунтов."""
    if os.path.exists(profile_path):
        for root, dirs, files in os.walk(profile_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(profile_path)
        print("Данные профиля удалены.")
    else:
        print("Данные профиля не найдены.")

def chat_with_bot():
    profile_path = "./user_data"
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    #options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36")
    options.add_argument(f"--user-data-dir={profile_path}")

    while True:
        print("\nМеню:")
        print("1. Войти в аккаунт")
        print("2. Удалить данные профиля")
        print("3. Выйти из программы")
        choice = input("Выберите действие: ")

        if choice == "1":
            if not os.path.exists(profile_path):
                os.makedirs(profile_path)

            driver = uc.Chrome(options=options)
            driver.get("https://chat.openai.com")

            try:
                email = input("Email: ")
                password = input("Password: ")

                if not is_logged_in(driver):
                    perform_login(driver, email, password)

                input_selector = "div.ProseMirror[contenteditable='true']"
                send_button_selector = "button[data-testid='send-button']"
                response_selector = "div.markdown.prose"

                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, input_selector))
                )

                print("Привет! Чем могу помочь?")

                while True:
                    user_message = input("Вы: ")
                    if user_message.lower() in ["выход", "exit"]:
                        print("Завершение работы.")
                        break

                    input_field = driver.find_element(By.CSS_SELECTOR, input_selector)
                    input_field.click()

                    input_field.clear()
                    input_field.send_keys(user_message)

                    send_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, send_button_selector))
                    )

                    old_responses = driver.find_elements(By.CSS_SELECTOR, response_selector)
                    old_count = len(old_responses)

                    send_button.click()
                    print("Бот думает...")

                    bot_response = wait_for_stable_response(driver, old_count)
                    print(f"Бот: {bot_response}")

            except Exception as e:
                print(f"Произошла ошибка: {e}")
            finally:
                driver.quit()

        elif choice == "2":
            delete_profile_data(profile_path)

        elif choice == "3":
            print("Выход из программы.")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    chat_with_bot()
