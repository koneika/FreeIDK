
import undetected_chromedriver as uc
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_last_bot_response(driver):
    """Получает последний ответ бота из HTML."""
    try:
        response_selector = "div.markdown.prose"
        responses = driver.find_elements(By.CSS_SELECTOR, response_selector)
        if responses:
            return responses[-1].get_attribute("innerText").strip()
        return "Ответ не найден."
    except Exception as e:
        return f"Ошибка получения ответа: {e}"

def wait_for_stable_response(driver, old_count, timeout=15):
    """Ждёт, пока у бота появится новое сообщение, и оно стабилизируется (не меняется)."""
    response_selector = "div.markdown.prose"
    start_time = time.time()
    
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, response_selector)) > old_count
    )

    stable_text = ""
    last_text = ""
    stable_count = 0

    while time.time() - start_time < timeout:
        current_text = get_last_bot_response(driver)
        if current_text == last_text and current_text.strip() != "":
            stable_count += 1
            if stable_count >= 2:
                stable_text = current_text
                break
        else:
            stable_count = 0

        last_text = current_text
        time.sleep(1)

    return stable_text if stable_text else last_text

def perform_login(driver, email, password):
    """Выполняет вход на сайт: вводит email, нажимает 'Continue', вводит пароль, код и завершает авторизацию."""
    try:
        # Локаторы для элементов
        login_button_selector = "button[data-testid='login-button']"
        email_input_selector = "input[type='email']"
        password_input_selector = "input[type='password']"
        email_continue_button_selector = "button.continue-btn"  # Селектор для 'Continue' после email
        password_continue_button_selector = "button._button-login-password"  # Селектор для 'Continue' после пароля
        code_input_selector = "input._codeInput_p12g4_28"  # Селектор для ввода кода
        #code_submit_button_selector = password_continue_button_selector  # Кнопка может совпадать с предыдущими
        code_input_selector2 = "button._continueButton_p12g4_42"

        # Шаг 1: Нажать на кнопку "Log in"
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, login_button_selector))
        )
        login_button.click()
        print("Кнопка 'Log in' нажата.")

        # Шаг 2: Ввести email
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, email_input_selector))
        )
        email_input.send_keys(email)
        print(f"Email введён: {email}")

        # Шаг 3: Нажать кнопку "Continue" после ввода email
        email_continue_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, email_continue_button_selector))
        )
        email_continue_button.click()
        print("Кнопка 'Continue' нажата после ввода email.")

        # Шаг 4: Ввести пароль
        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, password_input_selector))
        )
        password_input.send_keys(password)
        print(f"Пароль введён: {'*' * len(password)}")

        # Шаг 5: Нажать кнопку "Continue" после ввода пароля
        password_continue_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, password_continue_button_selector))
        )
        password_continue_button.click()
        print("Кнопка 'Continue' нажата после ввода пароля.")

        # Шаг 6: Ввести код из почты
        code_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, code_input_selector))
        )
        code = input("Введите код из почты: ")
        code_input.send_keys(code)
        print("Код введён.")

        # Шаг 7: Нажать кнопку "Continue" после ввода кода
        code_submit_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, code_input_selector2))
        )
        code_submit_button.click()
        print("Кнопка 'Continue' нажата после ввода кода.")


    except Exception as e:
        print(f"Ошибка при попытке логина: {e}")



def chat_with_bot():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--incognito")
    options.add_argument("--headless=new")  # Включаем headless режим
    
    # Указываем виртуальный дисплей
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36")

    driver = uc.Chrome(options=options)
    driver.get("https://chat.openai.com")

    try:
        # Ваши данные для логина
        email = input("email: ")
        password = input("password: ")

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

            for _ in range(50):
                input_field.send_keys("")
            
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

if __name__ == "__main__":
    chat_with_bot()
