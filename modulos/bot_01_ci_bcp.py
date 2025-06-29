# Importación de librerías necesarias
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import base64
from pathlib import Path
import requests
import json
import os
import platform
import time
from datetime import datetime
from anticaptchaofficial.imagecaptcha import imagecaptcha
import re
from selenium_stealth import stealth
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("Bot 01 - BCP Cash In")

def create_stealth_driver(cfg):
    """
    Función que crea y configura un driver de Chrome con características anti-detección
    """
    logger.info("Creando driver de Chrome con stealth")
    ruta_descarga = cfg['rutas']['ruta_input']
    options = webdriver.ChromeOptions()
    
    profile_dir = os.path.expanduser("~/chrome_profile_bcp")
    os.makedirs(profile_dir, exist_ok=True)
    options.add_argument(f"--user-data-dir={profile_dir}")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')

    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1,
        "profile.default_content_setting_values.cookies": 1,
        "profile.block_third_party_cookies": False,
        "download.default_directory": os.path.abspath(ruta_descarga)
    }
    options.add_experimental_option("prefs", prefs)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    except Exception as e:
        logger.warning("Problema con el chromedriver. Intentando con chromedriver del sistema...")
        try:
            driver = webdriver.Chrome(service=Service('chromedriver'), options=options)
        except:
            logger.error(f"No se pudo crear el driver: {e}")
            raise Exception(f"No se pudo crear el driver: {e}")

    stealth(driver,
        languages=["es-ES", "es"],
        vendor="Google Inc.", 
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )    
    logger.info("Driver de Chrome creado exitosamente")
    return driver


def retry_action(action, error_msg):
    max_retries = 4
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            return action()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"{error_msg}: {str(e)}")
                raise
            logger.warning(f"{error_msg} (reintento {attempt+1}/{max_retries}): {str(e)}")
            time.sleep(retry_delay)

def login(driver):
    """
    Función que realiza el proceso de login en la página del BCP
    """    
    logger.info("Iniciando proceso de login en BCP")
    driver.get("https://www.tlcbcp.com/")
    time.sleep(10)
    def close_modal():
        try:
            modal_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='bcp-modal-0']/div/bcp-modal-footer/div/bcp-button/button/bcp-character/span"))
            )
            driver.execute_script("arguments[0].click();", modal_button)
            time.sleep(1)
            logger.info("Modal cerrado exitosamente")
        except:
            pass
    
    retry_action(close_modal, "Error al cerrar modal")
    time.sleep(10)
    def enter_card():
        campo_tarjeta = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[contains(@name, 'ciam-input-card')]"))
        )
        campo_tarjeta.clear()
        campo_tarjeta.send_keys("0006000003532706")
        logger.info("Número de tarjeta ingresado")
        return campo_tarjeta
    
    retry_action(enter_card, "Error al ingresar número de tarjeta")
    
    def click_continue():
        boton_continuar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'keyboard-input')]"))
        )
        boton_continuar.click()
        return boton_continuar

    retry_action(click_continue, "Error al hacer clic en continuar")
    
    digitos = ["2", "1", "0", "5", "9", "3"]
    
    def enter_digits():
        for digito in digitos:
            elemento = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//bcp-keyboard//*[text()='{digito}']"))
            )
            elemento.click()
            time.sleep(0.5)
        logger.info("Clave ingresada mediante teclado virtual")
    
    retry_action(enter_digits, "Error al ingresar dígitos")
    
    def get_captcha_image():
        img_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'captcha-container')]//bcp-img/img"))
        )
        return img_element
    
    img_element = retry_action(get_captcha_image, "Error al obtener imagen captcha")
    
    img_src = img_element.get_attribute('src')
    
    if 'image/svg' in img_src:
        extension = '.svg'
    else:
        extension = '.jpg'
    
    if 'base64,' in img_src:
        base64_data = img_src.split('base64,')[1]
        img_data = base64.b64decode(base64_data)
    else:
        img_data = img_src.encode('utf-8')
    
    with open('./cliente/input/captcha.jpg', 'wb') as f:
        f.write(img_data)
    logger.info("Imagen de captcha guardada")

    ruta_imagen = "./cliente/input/captcha.jpg"
    api_key = "d1a79dd90565f566d2f6b48b4fad5260"
    
    def solve_captcha():
        solver = imagecaptcha()
        solver.set_verbose(1)
        solver.set_key(api_key)
        captcha_text = solver.solve_and_return_solution(ruta_imagen)
        if captcha_text == 0:
            raise Exception(f"Error: {solver.error_code}")
        return captcha_text
    
    captcha_text = retry_action(solve_captcha, "Error al resolver captcha")
    logger.info(f"Captcha resuelto: {captcha_text}")

    def click_out():
        out = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,"//ciam-form-session-card//form//bcp-title/h2"))
        )
        out.click()
        return out

    retry_action(click_out, "Error al hacer clic en título")

    def enter_captcha():
        input_captcha = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'bcp-ffw-form-group')]//*[@placeholder='Código']"))
        )
        input_captcha.click()
        input_captcha.send_keys(captcha_text)
        return input_captcha

    retry_action(enter_captcha, "Error al ingresar captcha")

    number_account = '194-2232464-0-40'
    def click_continue_btn():
        btn_continue = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//ciam-form-session-card//form//bcp-button/button"))
        )
        btn_continue.click()
        return btn_continue

    retry_action(click_continue_btn, "Error al hacer clic en continuar")

    def select_account():
        card_account = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//ntlc-account-card//*[text()='{number_account}']"))
        )
        driver.execute_script("arguments[0].click();", card_account)
        return card_account

    try:
        retry_action(select_account, "Error al seleccionar cuenta")
        logger.info("Cuenta seleccionada exitosamente")
    except Exception as e:
        logger.error("No se logró iniciar sesión")
        raise

def generar_reporte(driver):
    actual_date = datetime.now()
    actual_date = actual_date.strftime("%d%m%Y")
    logger.info(f"Generando reporte para la fecha: {actual_date}")
    def wait_for_page():
        return WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='inputDateFrom']"))
        )
    retry_action(wait_for_page, "Error esperando carga de página")
    def get_date_since_click():
        date_since_clic = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "(//input[@name='inputDateFrom'])"))
        )
        date_since_clic.click()
        return date_since_clic
    
    retry_action(get_date_since_click, "Error al hacer clic en fecha desde")
    def get_date_since():
        date_since = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@name='inputDateFrom']"))
        )
        date_since.send_keys(actual_date)
        date_since.send_keys(Keys.TAB)
        return date_since
    retry_action(get_date_since, "Error al ingresar fecha desde")    
    retry_action(get_date_since_click, "Error al hacer segundo clic en fecha desde")

    def get_date_to():
        date_to = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@name='inputDateTo']"))
        )
        date_to.click()
        return date_to
    
    retry_action(get_date_to, "Error al hacer clic en fecha hasta")

    def enter_date_to():
        date_to = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@name='inputDateTo']"))
        )
        date_to.send_keys(actual_date)
        date_to.send_keys(Keys.TAB)
        return date_to

    retry_action(enter_date_to, "Error al ingresar fecha hasta")
    time.sleep(2)

    def click_dropdown():
        dropdown = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//*[@label='Tipo']"))
        )
        dropdown.click()
        return dropdown
    
    retry_action(click_dropdown, "Error al hacer clic en dropdown")
    time.sleep(2)
    
    def select_ingresos():
        opcion_ingresos = WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located((By.XPATH, "//div[@class='select-item']//*[text()=' Ingresos ']"))
        )
        opcion_ingresos.click()
        return opcion_ingresos

    retry_action(select_ingresos, "Error al seleccionar opción Ingresos")
    time.sleep(2)

    def click_aplicar():
        btn_aplicar = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "//bcp-button-bpbaaa//*[text()= ' Aplicar ']"))
        )
        btn_aplicar.click()
        return btn_aplicar

    retry_action(click_aplicar, "Error al hacer clic en Aplicar")
    logger.info("Filtro de fechas y tipo aplicado")

    time.sleep(2)

    def click_checkbox():
        checkbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@class='bcp-ffw-custom-control-input' and @type='checkbox' and @name='bcp-cb-64']"))
        )
        driver.execute_script("arguments[0].click();", checkbox)
        return checkbox

    retry_action(click_checkbox, "Error al hacer clic en checkbox")

    time.sleep(2)

    def click_seleccionar_todas():
        try:
            elementos = driver.find_elements(By.XPATH, "//a[@class='bcp-ffw-btn btn-text']//span[text()='Seleccionar todas']")
            if elementos:
                driver.execute_script("arguments[0].click();", elementos[0])
                logger.info("Botón 'Seleccionar todas' presionado")
                return elementos[0]
            else:
                logger.info("No se encontró el botón 'Seleccionar todas', se continúa sin error.")
        except Exception as e:
            logger.warning(f"Error al intentar buscar o hacer clic en 'Seleccionar todas': {e}")

    time.sleep(2)

    def click_exportar():
        boton_exportar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'bcp-ffw-btn')]//*[text()= ' Exportar ']"))
        )
        driver.execute_script("arguments[0].click();", boton_exportar)
        return boton_exportar

    retry_action(click_exportar, "Error al hacer clic en Exportar")
    logger.info("Botón Exportar presionado")

    def click_txt():
        button_txt = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='dropdown-export-item'][text()= 'TXT/CSV']"))
        )
        driver.execute_script("arguments[0].click();", button_txt)
        return button_txt

    retry_action(click_txt, "Error al hacer clic en TXT/CSV")

    def click_select():
        button_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@name, 'bcp-select-2')]//bcp-icon-bpbaaa"))
        )
        driver.execute_script("arguments[0].click();", button_select)
        return button_select

    retry_action(click_select, "Error al hacer clic en selector")

    def click_comma():
        button_comma = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'bcp-paragraph')]//p[text()=' Coma(,) ']"))
        )
        driver.execute_script("arguments[0].click();", button_comma)
        return button_comma

    retry_action(click_comma, "Error al seleccionar coma")
    logger.info("Formato de exportación seleccionado: TXT/CSV con separador coma")

def descarga_fichero(driver):
    """
    Función que gestiona la descarga del archivo
    """
    logger.info("Iniciando descarga del archivo exportado")
    time.sleep(2)
    button_export = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button//*[text()='Exportar']"))
    )
    driver.execute_script("arguments[0].click();", button_export)

    code = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//div[@class='bcp-ffw-modal-content']//div[contains(text(), '040_ultimos')]"))
    )

    n_code = re.search(r'solicitud N° (\d+)', code.text)
    if n_code is None:
        logger.error("No se pudo encontrar el código de solicitud")
        raise Exception("No se pudo encontrar el código de solicitud")
    n_code = n_code.group(1)
    logger.info(f"Código de solicitud obtenido: {n_code}")
    n_code = n_code.zfill(8)

    button_files = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//bcp-character//*[text()=' Ir a archivos solicitados ']"))
    )
    driver.execute_script("arguments[0].click();", button_files)

    time.sleep(4)

    row_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"//bcp-table-row-9nbaaa[.//p[normalize-space(.)='{n_code}']]"))
    )

    index = row_element.get_attribute("index")

    time.sleep(2)

    button_dwld = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"//bcp-table-row-9nbaaa[@index='{index}']//span[contains(@class, 'bcp-ffw-sr-only') and text()='Descargar .txt']"))
    )
    driver.execute_script("arguments[0].click();", button_dwld)

    time.sleep(2)

    button_txt = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button//span[text()=' Descargar .txt ']"))
    )
    driver.execute_script("arguments[0].click();", button_txt)

    time.sleep(2)
    logger.info("Archivo descargado exitosamente")


def bcp_cash_in_descarga_txt(cfg):
    """
    Función principal que ejecuta todo el proceso
    """
    driver = None
    try:
        logger.info("Iniciando proceso completo de descarga de movimientos BCP")
        driver = create_stealth_driver(cfg)
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
        generar_reporte(driver)
        descarga_fichero(driver)
        logger.info("Proceso de descarga de movimientos BCP finalizado correctamente")
    except Exception as e:
        logger.error(f"Ocurrió un error en bcp_cash_in_descarga_txt: {e}")
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Driver cerrado correctamente")
            except Exception:
                logger.warning("Error al cerrar el driver")

def bcp_cargar_gescom(cfg):
    """
    Función principal que ejecuta todo el proceso
    """
    try:
        ruta_archivo = Path(cfg['rutas']['ruta_input']) / "040_ultimos_movimientos.txt"
        ruta_archivo = Path(ruta_archivo)

        if not ruta_archivo.exists():
            logger.error(f"No se encontró el archivo: {ruta_archivo}")
            raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")

        with open(ruta_archivo, "rb") as archivo:
            contenido_b64 = base64.b64encode(archivo.read()).decode()

        payload = {
            "format": "Bcp_MovimientosDelDía",
            "fileName": f"043_ultimos_movimientos_{datetime.now().strftime('%Y-%m-%dT%H%M%S.%f')[:-3]}.txt",
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
        logger.info("Iniciando ejecución principal del bot BCP")
        bcp_cash_in_descarga_txt(cfg)
        resultado = True
        mensaje = "Descarga de archivo exitosa"
        if resultado:
            bcp_cargar_gescom(cfg)
            mensaje = "Carga de archivo exitosa"
            resultado = True
    except Exception as e:
        logger.error(f"Error en bot BCP: {e}")
        if platform.system() == 'Windows':
            os.system("taskkill /im chrome.exe /f")
        else:
            os.system("pkill -f chrome")
        raise Exception(f"Error en bot BCP: {e}") from e

    finally:
        logger.info("Navegador cerrado")
        return resultado, mensaje