from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from selenium.webdriver.common.keys import Keys
from selenium_stealth import stealth

#Función para imprimir la información de un elemento de html
def print_element_info(elemento):
    children = elemento.find_elements(By.CSS_SELECTOR, "*")
    # Imprimir tag y clase
    for child in children:
        print(child.tag_name, "-", child.get_attribute("class"))

def create_stealth_webdriver():
    """
    Función que crea y configura un driver de Chrome con características anti-detección
    """
    # Inicializar opciones del navegador
    options = webdriver.ChromeOptions()
    options.add_argument("user-data-dir=/app/bcp/perfil/chrome")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')

    # Configuración de preferencias adicionales
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1,
        "profile.default_content_setting_values.cookies": 1,
        "profile.block_third_party_cookies": False
    }
    options.add_experimental_option("prefs", prefs)

    # Creación del driver con las opciones configuradas
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Configuración de stealth
    stealth(driver,
        languages=["es-ES", "es"],
        vendor="Google Inc.", 
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver

def login(driver, max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Login attempt {attempt}/{max_attempts}...")

            # Clean cookies and storage, reload page
            driver.delete_all_cookies()
            driver.get("https://www.bbvanetcash.pe")
            driver.execute_script("window.localStorage.clear();")
            driver.execute_script("window.sessionStorage.clear();")
            time.sleep(5)  # Wait initial load

            # Fill company code
            company_code_input = driver.find_element(By.XPATH, "//input[@name='cod_emp']")
            company_code_input.clear()
            company_code_input.send_keys("331771")
            time.sleep(1)

            # Fill user code
            user_code_input = driver.find_element(By.XPATH, "//input[@name='cod_usu']")
            user_code_input.clear()
            user_code_input.send_keys("00000093")
            time.sleep(1)

            # Fill password
            password_input = driver.find_element(By.XPATH, "//input[@name='eai_password']")
            password_input.clear()
            password_input.send_keys("EEDEtpp2024")
            time.sleep(3)

            # Click 'Ingresar' button
            login_button = driver.find_element(By.XPATH, "//button[text()='Ingresar']")
            login_button.click()
            time.sleep(10)

            # Refresh after login
            driver.refresh()
            time.sleep(3)

            print("Login successful!")
            return  # Exit function if login succeeded

        except Exception as e:
            print(f"Login attempt {attempt} failed: {e}")
            if attempt == max_attempts:
                raise Exception("Login failed after maximum number of attempts.")
            else:
                print("Retrying login...")
                time.sleep(5)  # Wait before retrying

def select_charges(driver):
    app_template_host = driver.find_element(By.CSS_SELECTOR, "bbva-btge-app-template")
    app_template_shadow_root = driver.execute_script("return arguments[0].shadowRoot", app_template_host)

    sidebar_menu_host = driver.find_element(By.CSS_SELECTOR, "bbva-btge-sidebar-menu")
    sidebar_menu_shadow_root = driver.execute_script("return arguments[0].shadowRoot", sidebar_menu_host)

    charges_menu_item = sidebar_menu_shadow_root.find_element(
        By.CSS_SELECTOR,
        "bbva-web-navigation-menu-item[icon='bbva:paysheetdollar']"
    )
    charges_menu_item.click()
    time.sleep(3)

def select_paid_collection(driver):
    # Step 1: locate the main shadow host
    main_shadow_host = driver.find_element(By.CSS_SELECTOR, "bbva-btge-menurization-landing-solution-page")
    main_shadow_root = driver.execute_script("return arguments[0].shadowRoot", main_shadow_host)

    # Step 2: locate iframe inside first shadow DOM
    iframe_host = main_shadow_root.find_element(By.CSS_SELECTOR, "bbva-core-iframe")
    iframe_shadow_root = driver.execute_script("return arguments[0].shadowRoot", iframe_host)
    core_iframe_element = iframe_shadow_root.find_element(By.CSS_SELECTOR, "iframe")
    driver.switch_to.frame(core_iframe_element)

    # Step 3: locate second shadow host inside iframe
    layout_shadow_host = driver.find_element(By.CSS_SELECTOR, "bbva-btge-menurization-landing-solution-home-page")
    layout_shadow_root = driver.execute_script("return arguments[0].shadowRoot", layout_shadow_host)

    # Step 4: find the links inside the second shadow DOM
    link_elements = layout_shadow_root.find_elements(By.CSS_SELECTOR, "bbva-web-link")
    for link_element in link_elements:
        link_text = link_element.text.strip()

        # Step 5: look for 'Recaudos pagados' link and click it
        if link_text == "Recaudos pagados":
            print("✓ Found 'Recaudos pagados', clicking the link.")
            link_element.click()
            break

    # Step 6: wait for next page to load
    time.sleep(5)

def download_txt(driver):
    time.sleep(5)

    # Step 0: return to main DOM
    driver.switch_to.default_content()
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "legacy-page"))
    )

    # Step 1: enter shadowRoot of legacy-page
    legacy_page_host = driver.find_element(By.CSS_SELECTOR, "legacy-page")
    legacy_page_shadow_root = driver.execute_script("return arguments[0].shadowRoot", legacy_page_host)

    # Step 2: enter shadowRoot of bbva-core-iframe
    iframe_host = legacy_page_shadow_root.find_element(By.CSS_SELECTOR, "bbva-core-iframe")
    iframe_shadow_root = driver.execute_script("return arguments[0].shadowRoot", iframe_host)

    # Step 3: switch to internal iframe inside bbva-core-iframe → iframe#bbvaIframe
    core_iframe_element = iframe_shadow_root.find_element(By.CSS_SELECTOR, "iframe")
    driver.switch_to.frame(core_iframe_element)

    # Optional: log when inside iframe
    print("✓ Inside iframe#bbvaIframe")

    # Step 4: wait for iframe#kyop-central-load-area and switch to it
    wait = WebDriverWait(driver, 10)
    kyop_iframe_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#kyop-central-load-area")))
    driver.switch_to.frame(kyop_iframe_element)

    print("✓ Inside iframe#kyop-central-load-area")

    # Step 5: click on the desired account link (LIGO- LA MAGICA SOLES)
    soles_account_link = driver.find_element(By.XPATH, "//a[contains(@href, 'LIGO- LA MAGICA SOLES')]")
    soles_account_link.click()
    time.sleep(5)
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, "//input[@name='fecini']"))
    )

    # Step 6: input date range
    current_date = datetime.now().strftime("%d%m%Y")  # Format: DDMMYYYY

    start_date_input = driver.find_element(By.XPATH, "//input[@name='fecini']")
    start_date_input.click()
    time.sleep(1)
    start_date_input.send_keys(Keys.ENTER)
    time.sleep(5)

    end_date_input = driver.find_element(By.XPATH, "//input[@name='fecfin']")
    end_date_input.click()
    time.sleep(1)
    end_date_input.send_keys(Keys.ENTER)
    time.sleep(1)
    end_date_input.send_keys(Keys.TAB)
    time.sleep(5)

    # Step 7: click on 'Consultar' button
    consult_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@value='Consultar']"))
    )
    consult_button.click()

    # Step 8: download TXT
    time.sleep(2)
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, "//a[@title='Descargar Txt']"))
    )
    download_link = driver.find_element(By.XPATH, "//a[@title='Descargar Txt']")
    download_link.click()
    time.sleep(5)

MAX_ATTEMPTS_FLOW = 3

def bot_run(cfg, mensaje):
    try:
    # Always create driver first
        driver = create_stealth_webdriver()

        # First: try login → only ONCE (it has its own 3 internal attempts)
        login(driver, 3)  # if this fails, exception will be raised → whole flow aborts

        print("✓ Login successful. Continuing with the flow...")

        # Now retry the rest of the flow if needed
        for attempt in range(1, MAX_ATTEMPTS_FLOW + 1):
            try:
                print(f"Flow attempt {attempt}/{MAX_ATTEMPTS_FLOW} running...")

                select_charges(driver)
                select_paid_collection(driver)
                download_txt(driver)

                print("✓ Process completed successfully.")
                break  # Exit loop if success

            except Exception as e:
                print(f"Error in flow on attempt {attempt}: {e}")
                if attempt == MAX_ATTEMPTS_FLOW:
                    print("Flow failed after maximum attempts.")
                    raise
                else:
                    print("Retrying flow steps...")
                    time.sleep(5)  # Optional: wait a bit before retrying

    except Exception as e:
        print(f"Fatal error: {e}")

    finally:
        # Always close driver at the end
        driver.quit()

