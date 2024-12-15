import undetected_chromedriver as uc
import time
import json
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

ACCOUNTS_FILE = "accounts.json"

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print("Ошибка: Невозможно загрузить accounts.json. Перезаписываю файл.")
    return {}

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as file:
        json.dump(accounts, file, indent=4)

def create_browser(profile_dir=None):
    options = uc.ChromeOptions()
    if profile_dir:
        options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    try:
        driver = uc.Chrome(options=options)
        print("Браузер создан и запущен.")
        return driver
    except Exception as e:
        print(f"Ошибка при создании браузера: {e}")
        return None

def open_site(driver, url):
    try:
        driver.get(url)
        print(f"Сайт {url} успешно открыт.")
    except Exception as e:
        print(f"Ошибка при открытии сайта {url}: {e}")
        driver.quit()

def perform_login(driver, email, password):
    try:
        print("Начинаю процесс логина...")

        # Нажать кнопку "Log in"
        login_button = None
        for selector in ["button[data-testid='login-button']", "//button[contains(text(), 'Log in')]"]:
            try:
                if "//" in selector:
                    login_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    login_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                if login_button:
                    break
            except Exception:
                continue

        if not login_button:
            raise Exception("Кнопка 'Log in' не найдена.")

        login_button.click()
        print("Кнопка 'Log in' нажата.")

        # Ввести email
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        email_input.send_keys(email)
        print(f"Email введён: {email}")

        # Нажать "Continue"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.continue-btn"))
        ).click()
        print("Кнопка 'Continue' нажата после ввода email.")

        # Ввести пароль
        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
        )
        password_input.send_keys(password)
        print("Пароль введён.")

        # Нажать "Continue"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button._button-login-password"))
        ).click()
        print("Кнопка 'Continue' нажата после ввода пароля.")

        # Проверить, нужно ли вводить код
        try:
            code_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input._codeInput_p12g4_28"))
            )
            code = input("Введите код из почты: ")
            code_input.send_keys(code)
            print("Код введён.")

            WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button._continueButton_p12g4_42"))
            ).click()
            print("Код подтверждён.")
        except Exception:
            print("Поле для кода не найдено. Продолжаем без него.")

        print("Вход выполнен успешно.")
    except Exception as e:
        print(f"Ошибка при логине: {e}")
        driver.save_screenshot("error_screenshot.png")
        print("Скриншот сохранён: error_screenshot.png")

def menu():
    accounts = load_accounts()
    drivers = []  # Список для хранения активных браузеров

    while True:
        print("\nМеню:")
        print("1. Добавить аккаунт")
        print("2. Войти во все аккаунты")
        print("3. Удалить аккаунт")
        print("4. Выход")

        choice = input("Выберите действие: ").strip()

        if choice == "1":
            email = input("Введите email: ")
            password = input("Введите пароль: ")
            accounts[email] = {"email": email, "password": password}
            save_accounts(accounts)
            print(f"Аккаунт {email} добавлен.")

        elif choice == "2":
            for email, creds in accounts.items():
                print(f"Логин для {email}...")
                driver = create_browser()
                if not driver:
                    print("Не удалось создать браузер для аккаунта.")
                    continue
                open_site(driver, "https://chat.openai.com")
                perform_login(driver, creds['email'], creds['password'])
                drivers.append(driver)  # Сохраняем браузер

        elif choice == "3":
            email = input("Введите email для удаления: ").strip()
            if email in accounts:
                del accounts[email]
                save_accounts(accounts)
                print(f"Аккаунт {email} удалён.")
            else:
                print(f"Аккаунт {email} не найден.")

        elif choice == "4":
            print("Выход из программы. Закрытие всех браузеров...")
            for driver in drivers:
                driver.quit()
            break

        else:
            print("Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    menu()
