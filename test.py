import undetected_chromedriver as uc
import pickle
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

COOKIE_FILE = "cookies.pkl"  # Файл для сохранения куки

def save_cookies(driver):
    """Сохраняет куки в файл."""
    with open(COOKIE_FILE, "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print("Куки сохранены.")

def load_cookies(driver):
    """Загружает куки из файла."""
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print("Куки загружены.")
    else:
        print("Файл с куки не найден.")

def is_logged_in(driver):
    """Проверяет, авторизован ли пользователь."""
    driver.get("https://chat.openai.com")
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ProseMirror[contenteditable='true']"))
        )
        return True
    except:
        return False

def perform_login(driver, email, password):
    """Выполняет вход на сайт, если пользователь не авторизован."""
    try:
        login_button_selector = "button[data-testid='login-button']"
        email_input_selector = "input[type='email']"
        password_input_selector = "input[type='password']"
        email_continue_button_selector = "button.continue-btn"
        password_continue_button_selector = "button._button-login-password"
        code_input_selector = "input._codeInput_p12g4_28"
        code_continue_selector = "button._continueButton_p12g4_42"

        # Нажимаем "Log in"
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, login_button_selector))
        )
        login_button.click()

        # Вводим email
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, email_input_selector))
        )
        email_input.send_keys(email)

        email_continue_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, email_continue_button_selector))
        )
        email_continue_button.click()

        # Вводим пароль
        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, password_input_selector))
        )
        password_input.send_keys(password)

        password_continue_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, password_continue_button_selector))
        )
        password_continue_button.click()

        # Вводим код из почты
        code_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, code_input_selector))
        )
        code = input("Введите код из почты: ")
        code_input.send_keys(code)

        code_continue_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, code_continue_selector))
        )
        code_continue_button.click()

        print("Авторизация завершена.")
        save_cookies(driver)

    except Exception as e:
        print(f"Ошибка при попытке авторизации: {e}")

def chat_with_bot():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-data-dir=./user_data")  # Сохраняем пользовательские данные

    driver = uc.Chrome(options=options)

    try:
        # Загружаем куки, если они существуют
        driver.get("https://chat.openai.com")
        load_cookies(driver)
        driver.refresh()  # Обновляем страницу после загрузки куки

        # Проверяем авторизацию
        if not is_logged_in(driver):
            print("Пользователь не авторизован. Выполняем вход...")
            email = input("email: ")
            password = input("password: ")
            perform_login(driver, email, password)
        else:
            print("Пользователь уже авторизован.")

        # Основной код для общения с ботом
        print("Привет! Чем могу помочь?")
        while True:
            user_message = input("Вы: ")
            if user_message.lower() in ["выход", "exit"]:
                print("Завершение работы.")
                break

            input_selector = "div.ProseMirror[contenteditable='true']"
            send_button_selector = "button[data-testid='send-button']"
            response_selector = "div.markdown.prose"

            input_field = driver.find_element(By.CSS_SELECTOR, input_selector)
            input_field.send_keys(user_message)

            send_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, send_button_selector))
            )
            send_button.click()

            old_responses = driver.find_elements(By.CSS_SELECTOR, response_selector)
            old_count = len(old_responses)
            bot_response = wait_for_stable_response(driver, old_count)
            print(f"Бот: {bot_response}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    chat_with_bot()
