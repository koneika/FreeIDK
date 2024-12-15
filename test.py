import undetected_chromedriver as uc
import time
import json
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ACCOUNTS_FILE = "accounts.json"

def load_accounts():
    """Загружает список аккаунтов из файла."""
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as file:
            try:
                data = json.load(file)
                if isinstance(data, dict):  # Убедимся, что это словарь
                    return data
                else:
                    print("Ошибка: данные в файле accounts.json повреждены. Сбрасываю.")
                    return {}
            except json.JSONDecodeError:
                print("Ошибка: файл accounts.json повреждён. Сбрасываю.")
                return {}
    return {}


def save_accounts(accounts):
    """Сохраняет список аккаунтов в файл."""
    with open(ACCOUNTS_FILE, "w") as file:
        json.dump(accounts, file, indent=4)
    print("Данные аккаунтов сохранены.")

def create_profile_dir(email):
    """Создаёт уникальную директорию для профиля браузера."""
    profile_dir = f"./profiles/{email.replace('@', '_').replace('.', '_')}"
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    return profile_dir

def perform_login(driver, email, password):
    """Выполняет вход в аккаунт."""
    try:
        driver.get("https://chat.openai.com")
        login_button_selector = "button[data-testid='login-button']"
        email_input_selector = "input[type='email']"
        password_input_selector = "input[type='password']"
        email_continue_button_selector = "button.continue-btn"
        password_continue_button_selector = "button._button-login-password"

        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, login_button_selector))
        )
        login_button.click()

        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, email_input_selector))
        )
        email_input.send_keys(email)

        email_continue_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, email_continue_button_selector))
        )
        email_continue_button.click()

        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, password_input_selector))
        )
        password_input.send_keys(password)

        password_continue_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, password_continue_button_selector))
        )
        password_continue_button.click()

        print(f"Вход выполнен для {email}")
    except Exception as e:
        print(f"Ошибка при попытке логина {email}: {e}")

def chat_with_bot_session(driver):
    """Начинает сессию общения с ботом."""
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



def start_browser(account, accounts):
    """Запускает браузер с заданным аккаунтом и обновляет данные аккаунтов."""
    email = account["email"]
    profile_dir = create_profile_dir(email)

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = uc.Chrome(options=options)
    driver.get("https://chat.openai.com")

    if "cookies" in account:
        for cookie in account["cookies"]:
            driver.add_cookie(cookie)
        driver.refresh()

    if not is_logged_in(driver):
        perform_login(driver, account["email"], account["password"])
        account["cookies"] = driver.get_cookies()
        save_accounts(accounts)  # Сохраняем обновлённые куки

    # После входа переходим к взаимодействию с ботом
    print(f"Начинаем общение с ботом для аккаунта {email}...")
    chat_with_bot_session(driver)

    return driver


def is_logged_in(driver):
    """Проверяет, залогинен ли пользователь на основе куки."""
    try:
        cookies = driver.get_cookies()
        for cookie in cookies:
            if cookie.get("name") == "__Secure-next-auth.session-token":
                return True
        return False
    except Exception:
        return False

def menu():
    accounts = load_accounts()

    while True:
        print("\nМеню:")
        print("1. Добавить новый аккаунт")
        print("2. Войти во все аккаунты")
        print("3. Удалить аккаунт")
        print("4. Выйти")
        choice = input("Выберите действие: ")

        if choice == "1":
            email = input("Введите email: ")
            password = input("Введите пароль: ")
            accounts[email] = {"email": email, "password": password}
            save_accounts(accounts)
            print(f"Аккаунт {email} добавлен.")

        elif choice == "2":
            drivers = []
            for email, account in accounts.items():
                print(f"Запуск браузера для {email}...")
                driver = start_browser(account, accounts)  # Передаём accounts
                drivers.append(driver)
            print("Все аккаунты активны.")

        elif choice == "3":
            email = input("Введите email для удаления: ")
            if email in accounts:
                del accounts[email]
                save_accounts(accounts)
                print(f"Аккаунт {email} удалён.")
            else:
                print(f"Аккаунт {email} не найден.")

        elif choice == "4":
            print("Выход из программы.")
            break

        else:
            print("Неверный выбор. Попробуйте снова.")



if __name__ == "__main__":
    menu()
