# test_functions.py

import undetected_chromedriver as uc
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from accounts_manager import load_accounts, save_accounts

logger = logging.getLogger(__name__)

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
    # options.add_argument("--headless=new")  # Раскомментируйте, если хотите запустить браузер в headless-режиме

    try:
        driver = uc.Chrome(options=options)
        logger.info("Browser created and launched.")
        return driver
    except Exception as e:
        logger.error(f"Error creating browser: {e}")
        return None

def open_site(driver, url="https://chat.openai.com"):
    try:
        driver.get(url)
        logger.info(f"Site {url} opened successfully.")
    except Exception as e:
        logger.error(f"Error opening site {url}: {e}")
        driver.quit()

def perform_login(driver, email, password):
    try:
        logger.info("Starting login process.")

        # Click the "Log in" button
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
            raise Exception("Login button not found.")

        login_button.click()
        logger.info("Clicked 'Log in' button.")

        # Enter email
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        email_input.send_keys(email)
        logger.info(f"Entered email: {email}")

        # Click "Continue"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.continue-btn"))
        ).click()
        logger.info("Clicked 'Continue' after entering email.")

        # Enter password
        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
        )
        password_input.send_keys(password)
        logger.info("Entered password.")

        # Click "Continue"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button._button-login-password"))
        ).click()
        logger.info("Clicked 'Continue' after entering password.")

        # Check if code input is required (2FA)
        try:
            code_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input._codeInput_p12g4_28"))
            )
            logger.info("Two-factor authentication required, but automated input is not handled.")
            # Cannot handle 2FA automatically
        except Exception:
            logger.info("No two-factor authentication required.")

        logger.info("Login successful.")
        return True

    except Exception as e:
        logger.error(f"Error during login: {e}")
        driver.save_screenshot("error_screenshot.png")
        logger.info("Screenshot saved: error_screenshot.png")
        return False

def wait_for_stable_response(driver, old_count, timeout=30):
    response_selector = "div.markdown.prose"
    start_time = time.time()
    stable_text = ""
    last_text = ""
    stable_count = 0

    while time.time() - start_time < timeout:
        responses = driver.find_elements(By.CSS_SELECTOR, response_selector)
        if len(responses) > old_count:
            current_text = responses[-1].text.strip()
            if current_text == last_text and current_text.strip() != "":
                stable_count += 1
                if stable_count >= 2:
                    stable_text = current_text
                    break
            else:
                stable_count = 0
            last_text = current_text
        time.sleep(1)

    return stable_text if stable_text else "No response received or timeout."

def send_query(driver, query):
    input_selector = "div.ProseMirror[contenteditable='true']"
    response_selector = "div.markdown.prose"
    try:
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, input_selector))
        )
        input_field.click()
        input_field.clear()
        input_field.send_keys(query)
        logger.info(f"Entered query: {query}")

        send_button_selector = "button[data-testid='send-button']"
        send_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, send_button_selector))
        )

        old_responses = driver.find_elements(By.CSS_SELECTOR, response_selector)
        old_count = len(old_responses)

        send_button.click()
        logger.info("Clicked send button, waiting for response...")

        bot_response = wait_for_stable_response(driver, old_count)
        logger.info(f"Bot response: {bot_response}")
        return bot_response

    except Exception as e:
        logger.error(f"Error sending query: {e}")
        return "An error occurred while sending the request."

def login_and_send_query(email, password, query):
    driver = create_browser()
    if not driver:
        return "Failed to create browser."

    open_site(driver)
    login_success = perform_login(driver, email, password)
    if not login_success:
        driver.quit()
        return "Failed to log into the account."

    response = send_query(driver, query)
    # Close the browser after getting the response
    driver.quit()
    return response
