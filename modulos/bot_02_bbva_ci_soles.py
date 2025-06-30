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
from selenium.webdriver.common.action_chains import ActionChains
import logging
import base64
from pathlib import Path
import requests
import os
import platform

logger = logging.getLogger("Bot 02 - BBVA CI Soles")

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

def bbva_ci_soles_descarga_txt(cfg):
    """
    Función principal que ejecuta todo el proceso de descarga de movimientos BBVA SOLES
    """
    driver = None
    try:
        logger.info("Iniciando proceso completo de descarga de movimientos BBVA SOLES")
        driver = create_stealth_webdriver()

        def retry_login(max_attempts=2):
            for attempt in range(max_attempts):
                try:
                    logger.info(f"Intento de login {attempt + 1}/{max_attempts}")
                    login(driver)
                    logger.info("Login exitoso")
                    return True
                except Exception as e:
                    logger.warning(f"Error en intento {attempt + 1}: {e}")
                    if attempt < max_attempts - 1:
                        logger.info("Actualizando página y reintentando login...")
                        driver.refresh()
                        time.sleep(5)
                    else:
                        logger.error("Se agotaron todos los intentos de login")
                        raise e
            return False

        retry_login()
        select_charges(driver)
        select_paid_collection(driver)
        download_txt(driver)
        logger.info("Proceso de descarga de movimientos BBVA SOLES finalizado correctamente")
        
    except Exception as e:
        logger.error(f"Ocurrió un error en bbva_ci_soles_descarga_txt: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Driver cerrado correctamente")
            except Exception:
                logger.warning("Error al cerrar el driver")


def login(driver):
    """
    Realiza el proceso de login en BBVA Netcash. Si falla, lanza una excepción.
    """
    try:
        logger.info("Iniciando login BBVA Netcash")

        # Limpiar cookies y storage
        driver.delete_all_cookies()
        driver.get("https://www.bbvanetcash.pe")
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        time.sleep(5)  # Espera para carga inicial

        # Ingresar código de empresa
        company_code_input = driver.find_element(By.XPATH, "//input[@name='cod_emp']")
        company_code_input.clear()
        company_code_input.send_keys("331771")
        time.sleep(1)

        # Ingresar código de usuario
        user_code_input = driver.find_element(By.XPATH, "//input[@name='cod_usu']")
        user_code_input.clear()
        user_code_input.send_keys("00000093")
        time.sleep(1)

        # Ingresar contraseña
        password_input = driver.find_element(By.XPATH, "//input[@name='eai_password']")
        password_input.clear()
        password_input.send_keys("EEDEtpp2024")
        time.sleep(3)

        # Click en Ingresar
        login_button = driver.find_element(By.XPATH, "//button[text()='Ingresar']")
        login_button.click()
        time.sleep(10)

        # Refrescar después del login
        driver.refresh()
        time.sleep(3)

        logger.info("Login exitoso en BBVA Netcash")

    except Exception as e:
        logger.error(f"Error durante el login BBVA Netcash: {e}")
        raise e

def select_charges(driver):
    time.sleep(5)
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
    time.sleep(5)

    # Step 5: click on the desired account link (LIGO- LA MAGICA SOLES)
    soles_account_link = driver.find_element(By.XPATH, "//a[contains(@href, 'LIGO- LA MAGICA SOLES')]")
    soles_account_link.click()
    time.sleep(5)
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, "//input[@name='fecini']"))
    )

    start_date_input = driver.find_element(By.XPATH, "//input[@name='fecini']")
    ActionChains(driver).move_to_element(start_date_input).click().perform()
    time.sleep(1)
    start_date_input.send_keys(Keys.ENTER)
    time.sleep(1)
    start_date_input.send_keys(Keys.TAB)
    time.sleep(5)

    end_date_input = driver.find_element(By.XPATH, "//input[@name='fecfin']")
    time.sleep(1)
    end_date_input.send_keys(Keys.ENTER)
    time.sleep(1)
    end_date_input.send_keys(Keys.TAB)
    time.sleep(5)

    def click_consultar():
        try:
            logger.info("Esperando el botón 'Consultar'...")

            # Espera hasta que el botón esté presente
            consult_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Consultar']"))
            )

            # Mueve al botón con ActionChains
            ActionChains(driver).move_to_element(consult_button).perform()
            time.sleep(1)  # Pequeña pausa por si hay animación

            # Clic con JavaScript como respaldo (si es necesario)
            driver.execute_script("arguments[0].click();", consult_button)

            logger.info("Se hizo clic en el botón 'Consultar' correctamente.")

        except Exception as e:
            logger.error(f"Error al intentar hacer clic en el botón 'Consultar': {e}")
            raise e

    click_consultar()
    # Step 8: download TXT
    time.sleep(3)
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.XPATH, "//a[@title='Descargar Txt']"))
    )
    download_link = driver.find_element(By.XPATH, "//a[@title='Descargar Txt']")
    download_link.click()
    time.sleep(5)

MAX_ATTEMPTS_FLOW = 3

def bbva_ci_soles_cargar_gescom(cfg):
    """
    Función principal que ejecuta todo el proceso
    """
    try:

        ruta_input = Path(cfg['rutas']['ruta_input'])

        # Buscar archivos que empiecen con "relacion_pago_"
        archivos = list(ruta_input.glob("relacion_pago_*"))

        if not archivos:
            logger.error(f"No se encontró ningún archivo que empiece con: 'relacion_pago_' en {ruta_input}")
            raise FileNotFoundError(f"No se encontró ningún archivo que empiece con: 'relacion_pago_' en {ruta_input}")

        # Tomar el primer archivo encontrado
        ruta_archivo = archivos[0]

        with open(ruta_archivo, "rb") as archivo:
            contenido_b64 = base64.b64encode(archivo.read()).decode()

        payload = {
            "format": "Bbva_HistóricoDeMovimientos",
            "fileName": f"ultimos_movimientos_{datetime.now().strftime('%Y-%m-%dT%H%M%S.%f')[:-3]}.txt",
            "base64File": contenido_b64
        }

        api_url = cfg['api']['api_gescom_transacciones']

        headers = {"Content-Type": "application/json"}
        logger.info("Enviando archivo a GESCOM")
        response = requests.post(api_url, json=payload, headers=headers)

        if response.status_code == 200:
            logger.info("Archivo enviado exitosamente a GESCOM.")
            return True
        else:
            logger.error(f"Error al enviar archivo a GESCOM: {response.status_code} - {response.text}")
            return False, f"Error al enviar archivo a GESCOM: {response.status_code} - {response.text}"
    except Exception as e:
        logger.error(f"Excepción al cargar archivo a GESCOM: {e}")
        return False, f"Excepción al cargar archivo a GESCOM: {e}"
  

def bot_run(cfg, mensaje):
    try:
        resultado = False
        logger.info("Iniciando ejecución principal del bot BBVA SOLES")
        
        bbva_ci_soles_descarga_txt(cfg)
        resultado = True
        mensaje = "Descarga de archivo exitosa"

        if resultado:
            bbva_ci_soles_cargar_gescom(cfg)
            mensaje = "Carga de archivo exitosa"
            resultado = True

    except Exception as e:
        logger.error(f"Error en bot BBVA SOLES: {e}")
        if platform.system() == 'Windows':
            os.system("taskkill /im chrome.exe /f")
        else:
            os.system("pkill -f chrome")
        raise Exception(f"Error en bot BBVA SOLES: {e}") from e

    finally:
        logger.info("Navegador cerrado")
        return resultado, mensaje
