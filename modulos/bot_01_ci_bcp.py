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
import os
import platform
import time
from datetime import datetime
from anticaptchaofficial.imagecaptcha import imagecaptcha
import re
from selenium_stealth import stealth
from selenium.webdriver.common.keys import Keys
from utilidades.google_drive import GoogleDriveUploader

logger = logging.getLogger("Bot 01 - BCP Cash In")

def create_stealth_webdriver(cfg):
    logger.info("Entrando a create_stealth_webdriver")
    """
    Crea un driver de Chrome configurado para descargar archivos en la ruta indicada en cfg['rutas']['ruta_input']
    """
    download_path = str(Path(cfg['rutas']['ruta_input']).absolute())
    profile_dir = str(Path(cfg['rutas']['ruta_perfil_bcp']).absolute())

    options = webdriver.ChromeOptions()

    options.add_argument(f"user-data-dir={profile_dir}")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")

    prefs = {
        "download.default_directory": download_path,  # <<< Aquí se fuerza la carpeta de descarga
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1,
        "profile.default_content_setting_values.cookies": 1,
        "profile.block_third_party_cookies": False
    }
    options.add_experimental_option("prefs", prefs)
    # Set longer timeout for ChromeDriver installation
    os.environ['PYDEVD_WARN_EVALUATION_TIMEOUT'] = '30'  # 30 seconds timeout
    os.environ['PYDEVD_UNBLOCK_THREADS_TIMEOUT'] = '30'  # Unblock threads after 30 seconds
    logger.info("Instalando ChromeDriver y creando instancia de webdriver.Chrome")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    logger.info("ChromeDriver creado correctamente")
    # Ejecutar scripts anti-detección adicionales
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es']})")
    driver.execute_script("window.chrome = {runtime: {}}")

    logger.info("Ejecutando stealth en el driver")
    stealth(driver,
        languages=["es-ES", "es"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    logger.info("Driver configurado y listo para usar")
    return driver

def retry_action(action, error_msg):
    logger.info(f"Entrando a retry_action para: {error_msg}")
    max_retries = 4
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            logger.info(f"Intento {attempt+1} de {max_retries} para {error_msg}")
            return action()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"{error_msg}: {str(e)}")
                raise
            logger.warning(f"{error_msg} (reintento {attempt+1}/{max_retries}): {str(e)}")
            time.sleep(retry_delay)

def login(driver, cfg):
    logger.info("Entrando a login")
    """
    Función que realiza el proceso de login en la página del BCP
    """    
    logger.info("Iniciando proceso de login en BCP")
    driver.get("https://www.tlcbcp.com/")
    time.sleep(10)
    def close_modal():
        logger.info("Intentando cerrar modal si existe")
        try:
            modal_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='bcp-modal-0']/div/bcp-modal-footer/div/bcp-button/button/bcp-character/span"))
            )
            driver.execute_script("arguments[0].click();", modal_button)
            time.sleep(1)
            logger.info("Modal cerrado exitosamente")
        except:
            logger.info("No se encontró modal para cerrar")
            pass
    
    retry_action(close_modal, "Error al cerrar modal")
    time.sleep(10)
    def enter_card():
        logger.info("Buscando campo de tarjeta para ingresar número")
        campo_tarjeta = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//input[contains(@name, 'ciam-input-card')]"))
        )
        campo_tarjeta.clear()
        campo_tarjeta.send_keys(cfg['env_vars']['bcp']['tarjeta'])
        logger.info("Número de tarjeta ingresado")
        return campo_tarjeta
    
    retry_action(enter_card, "Error al ingresar número de tarjeta")
    
    def click_continue():
        logger.info("Buscando botón continuar")
        boton_continuar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'keyboard-input')]"))
        )
        boton_continuar.click()
        logger.info("Botón continuar presionado")
        return boton_continuar

    retry_action(click_continue, "Error al hacer clic en continuar")
    
    digitos = cfg['env_vars']['bcp']['password'].split(',')
    
    def enter_digits():
        logger.info("Ingresando clave mediante teclado virtual")
        for digito in digitos:
            elemento = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//bcp-keyboard//*[text()='{digito}']"))
            )
            elemento.click()
            time.sleep(0.5)
        logger.info("Clave ingresada mediante teclado virtual")
    
    retry_action(enter_digits, "Error al ingresar dígitos")
    
    def get_captcha_image():
        logger.info("Buscando imagen captcha")
        img_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'captcha-container')]//bcp-img/img"))
        )
        logger.info("Imagen captcha encontrada")
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
    api_key = cfg['env_vars']['anticaptcha']['api_key']
    
    def solve_captcha():
        logger.info("Enviando captcha a anticaptcha")
        solver = imagecaptcha()
        solver.set_verbose(1)
        solver.set_key(api_key)
        captcha_text = solver.solve_and_return_solution(ruta_imagen)
        if captcha_text == 0:
            logger.error(f"Error al resolver captcha: {solver.error_code}")
            raise Exception(f"Error: {solver.error_code}")
        logger.info(f"Captcha resuelto: {captcha_text}")
        return captcha_text
    
    captcha_text = retry_action(solve_captcha, "Error al resolver captcha")
    logger.info(f"Captcha resuelto: {captcha_text}")

    def click_out():
        logger.info("Haciendo clic en título para salir del campo captcha")
        out = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,"//ciam-form-session-card//form//bcp-title/h2"))
        )
        out.click()
        logger.info("Clic en título realizado")
        return out

    retry_action(click_out, "Error al hacer clic en título")

    def enter_captcha():
        logger.info("Ingresando texto captcha en campo correspondiente")
        input_captcha = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'bcp-ffw-form-group')]//*[@placeholder='Código']"))
        )
        input_captcha.click()
        input_captcha.send_keys(captcha_text)
        logger.info("Captcha ingresado")
        return input_captcha

    retry_action(enter_captcha, "Error al ingresar captcha")

    number_account = cfg['env_vars']['bcp_cuenta']
    def click_continue_btn():
        logger.info("Buscando botón continuar para login")
        btn_continue = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//ciam-form-session-card//form//bcp-button/button"))
        )
        btn_continue.click()
        logger.info("Botón continuar presionado")
        return btn_continue

    retry_action(click_continue_btn, "Error al hacer clic en continuar")

    def select_account():
        logger.info(f"Buscando cuenta {number_account} para seleccionar")
        card_account = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//ntlc-account-card//*[text()='{number_account}']"))
        )
        driver.execute_script("arguments[0].click();", card_account)
        logger.info("Cuenta seleccionada")
        return card_account

    try:
        retry_action(select_account, "Error al seleccionar cuenta")
        logger.info("Cuenta seleccionada exitosamente")
    except Exception as e:
        logger.error("No se logró iniciar sesión")
        raise

def generar_reporte(driver):
    logger.info("Entrando a generar_reporte")
    actual_date = datetime.now()
    actual_date = actual_date.strftime("%d%m%Y")
    logger.info(f"Generando reporte para la fecha: {actual_date}")
    def wait_for_page():
        logger.info("Esperando carga de página para inputDateFrom")
        return WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='inputDateFrom']"))
        )
    retry_action(wait_for_page, "Error esperando carga de página")
    def get_date_since_click():
        logger.info("Haciendo clic en campo fecha desde")
        date_since_clic = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "(//input[@name='inputDateFrom'])"))
        )
        date_since_clic.click()
        logger.info("Clic en campo fecha desde realizado")
        return date_since_clic
    
    retry_action(get_date_since_click, "Error al hacer clic en fecha desde")
    def get_date_since():
        logger.info("Ingresando fecha desde")
        date_since = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@name='inputDateFrom']"))
        )
        date_since.send_keys(actual_date)
        date_since.send_keys(Keys.TAB)
        logger.info("Fecha desde ingresada")
        return date_since
    retry_action(get_date_since, "Error al ingresar fecha desde")    
    retry_action(get_date_since_click, "Error al hacer segundo clic en fecha desde")

    def get_date_to():
        logger.info("Haciendo clic en campo fecha hasta")
        date_to = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@name='inputDateTo']"))
        )
        date_to.click()
        logger.info("Clic en campo fecha hasta realizado")
        return date_to
    
    retry_action(get_date_to, "Error al hacer clic en fecha hasta")

    def enter_date_to():
        logger.info("Ingresando fecha hasta")
        date_to = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@name='inputDateTo']"))
        )
        date_to.send_keys(actual_date)
        date_to.send_keys(Keys.TAB)
        logger.info("Fecha hasta ingresada")
        return date_to

    retry_action(enter_date_to, "Error al ingresar fecha hasta")
    time.sleep(2)

    def click_dropdown():
        logger.info("Haciendo clic en dropdown de tipo")
        dropdown = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//*[@label='Tipo']"))
        )
        dropdown.click()
        logger.info("Dropdown de tipo abierto")
        return dropdown
    
    retry_action(click_dropdown, "Error al hacer clic en dropdown")
    time.sleep(2)
    
    def select_ingresos():
        logger.info("Seleccionando opción Ingresos")
        opcion_ingresos = WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located((By.XPATH, "//div[@class='select-item']//*[text()=' Ingresos ']"))
        )
        opcion_ingresos.click()
        logger.info("Opción Ingresos seleccionada")
        return opcion_ingresos

    retry_action(select_ingresos, "Error al seleccionar opción Ingresos")
    time.sleep(2)

    def click_aplicar():
        logger.info("Haciendo clic en botón Aplicar")
        btn_aplicar = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "//bcp-button-bpbaaa//*[text()= ' Aplicar ']"))
        )
        btn_aplicar.click()
        logger.info("Botón Aplicar presionado")
        return btn_aplicar

    retry_action(click_aplicar, "Error al hacer clic en Aplicar")
    logger.info("Filtro de fechas y tipo aplicado")

    time.sleep(2)

    def click_checkbox():
        logger.info("Haciendo clic en checkbox de selección")
        checkbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@class='bcp-ffw-custom-control-input' and @type='checkbox' and @name='bcp-cb-64']"))
        )
        driver.execute_script("arguments[0].click();", checkbox)
        logger.info("Checkbox seleccionado")
        return checkbox

    retry_action(click_checkbox, "Error al hacer clic en checkbox")

    time.sleep(2)

    def click_seleccionar_todas():
        logger.info("Buscando y haciendo clic en 'Seleccionar todas' si existe")
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
        logger.info("Haciendo clic en botón Exportar")
        boton_exportar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'bcp-ffw-btn')]//*[text()= ' Exportar ']"))
        )
        driver.execute_script("arguments[0].click();", boton_exportar)
        logger.info("Botón Exportar presionado")
        return boton_exportar

    retry_action(click_exportar, "Error al hacer clic en Exportar")
    logger.info("Botón Exportar presionado")

    def click_txt():
        logger.info("Seleccionando opción TXT/CSV")
        button_txt = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='dropdown-export-item'][text()= 'TXT/CSV']"))
        )
        driver.execute_script("arguments[0].click();", button_txt)
        logger.info("Opción TXT/CSV seleccionada")
        return button_txt

    retry_action(click_txt, "Error al hacer clic en TXT/CSV")

    def click_select():
        logger.info("Haciendo clic en selector de formato")
        button_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@name, 'bcp-select-2')]//bcp-icon-bpbaaa"))
        )
        driver.execute_script("arguments[0].click();", button_select)
        logger.info("Selector de formato abierto")
        return button_select

    retry_action(click_select, "Error al hacer clic en selector")

    def click_comma():
        logger.info("Seleccionando separador coma")
        button_comma = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'bcp-paragraph')]//p[text()=' Coma(,) ']"))
        )
        driver.execute_script("arguments[0].click();", button_comma)
        logger.info("Separador coma seleccionado")
        return button_comma

    retry_action(click_comma, "Error al seleccionar coma")
    logger.info("Formato de exportación seleccionado: TXT/CSV con separador coma")

def descarga_fichero(driver):
    logger.info("Entrando a descarga_fichero")
    """
    Función que gestiona la descarga del archivo
    """
    logger.info("Iniciando descarga del archivo exportado")
    time.sleep(2)
    button_export = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button//*[text()='Exportar']"))
    )
    driver.execute_script("arguments[0].click();", button_export)
    logger.info("Botón Exportar presionado en modal de descarga")

    code = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//div[@class='bcp-ffw-modal-content']//div[contains(text(), '040_ultimos')]"))
    )
    logger.info(f"Texto de código de solicitud: {code.text}")

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
    logger.info("Botón 'Ir a archivos solicitados' presionado")

    time.sleep(4)

    row_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"//bcp-table-row-9nbaaa[.//p[normalize-space(.)='{n_code}']]"))
    )
    logger.info(f"Fila de archivo encontrada para código: {n_code}")

    index = row_element.get_attribute("index")
    logger.info(f"Índice de la fila: {index}")

    time.sleep(2)

    button_dwld = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"//bcp-table-row-9nbaaa[@index='{index}']//span[contains(@class, 'bcp-ffw-sr-only') and text()='Descargar .txt']"))
    )
    driver.execute_script("arguments[0].click();", button_dwld)
    logger.info("Botón de descarga .txt presionado")

    time.sleep(2)

    button_txt = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button//span[text()=' Descargar .txt ']"))
    )
    driver.execute_script("arguments[0].click();", button_txt)
    logger.info("Botón final de descarga .txt presionado")

    time.sleep(2)
    logger.info("Archivo descargado exitosamente")


def bcp_cash_in_descarga_txt(cfg):
    logger.info("Entrando a bcp_cash_in_descarga_txt")
    """
    Función principal que ejecuta todo el proceso
    """
    driver = None
    try:
        logger.info("Iniciando proceso completo de descarga de movimientos BCP")
        driver = create_stealth_webdriver(cfg)
        def retry_login(max_attempts=2):
            logger.info("Entrando a retry_login")
            for attempt in range(max_attempts):
                try:
                    logger.info(f"Intento de login {attempt + 1}/{max_attempts}")
                    login(driver, cfg)
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
        logger.info("Login realizado, generando reporte")
        generar_reporte(driver)
        logger.info("Reporte generado, descargando fichero")
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
    logger.info("Entrando a bcp_cargar_gescom")
    """
    Función principal que ejecuta todo el proceso
    """
    try:
        json_data = cfg['env_vars']['gcp']['service_account_json']
        uploader = GoogleDriveUploader(authenticator=False, service_account_json=json_data)        
        folder_id = cfg['env_vars']['gcp']['folder_id']
        ruta_archivo = Path(cfg['rutas']['ruta_input']) / "040_ultimos_movimientos.txt"
        ruta_archivo = Path(ruta_archivo)
        file_name = f"040_ultimos_movimientos_{datetime.now().strftime('%Y-%m-%dT%H%M%S.%f')[:-3]}.txt"
        logger.info(f"Subiendo archivo a Google Drive: {file_name}")
        uploader.upload_file(ruta_archivo, file_name=file_name, folder_id=folder_id)

        if not ruta_archivo.exists():
            logger.error(f"No se encontró el archivo: {ruta_archivo}")
            raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")

        with open(ruta_archivo, "rb") as archivo:
            logger.info(f"Codificando archivo {ruta_archivo} a base64")
            contenido_b64 = base64.b64encode(archivo.read()).decode()

        payload = {
            "format": "Bcp_MovimientosDelDía",
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
    
def bot_run(cfg, mensaje = "Bot 01 - BCP Cash In"):
    logger.info(f"Ejecutando  {mensaje}")
    try:
        resultado = False
        logger.info("Iniciando ejecución principal del bot BCP")
        bcp_cash_in_descarga_txt(cfg)
        resultado = True
        mensaje = "Descarga de archivo exitosa"
        if resultado:
            logger.info("Descarga exitosa, iniciando carga a GESCOM")
            bcp_cargar_gescom(cfg)
            mensaje = "Carga de archivo exitosa"
            resultado = True
    except Exception as e:
        logger.error(f"Error en bot BCP: {e}")
        if platform.system() == 'Windows':
            logger.info("Cerrando procesos chrome en Windows")
            os.system("taskkill /im chrome.exe /f")
        else:
            logger.info("Cerrando procesos chrome en Linux/Unix")
            os.system("pkill -f chrome")
        raise Exception(f"Error en bot BCP: {e}") from e

    finally:
        logger.info("Navegador cerrado")
        return resultado, mensaje