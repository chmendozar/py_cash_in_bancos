# Importación de librerías necesarias
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import os
import time
from datetime import datetime
from anticaptchaofficial.imagecaptcha import imagecaptcha
import re
from selenium_stealth import stealth
from selenium.webdriver.common.keys import Keys


def create_stealth_driver():
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

def retry_action(action, error_msg):
    max_retries = 4
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            return action()
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"{error_msg}: {str(e)}")
                raise
            time.sleep(retry_delay)

def login(driver):
    """
    Función que realiza el proceso de login en la página del BCP
    """
    
    # Paso 1: Acceder a la página
    driver.get("https://www.tlcbcp.com/")
    time.sleep(10)
    # Paso 1.5: Cerrar modal si existe
    def close_modal():
        try:
            modal_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='bcp-modal-0']/div/bcp-modal-footer/div/bcp-button/button/bcp-character/span"))
            )
            driver.execute_script("arguments[0].click();", modal_button)
            time.sleep(1)
        except:
            # Si no existe el modal, continuar normalmente
            pass
    
    retry_action(close_modal, "Error al cerrar modal")
    time.sleep(10)
    # Paso 2: Ingresar número de tarjeta
    def enter_card():
        campo_tarjeta = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//input[contains(@name, 'ciam-input-card')]"))
        )
        campo_tarjeta.clear()
        campo_tarjeta.send_keys("0006000003532706")
        return campo_tarjeta
    
    retry_action(enter_card, "Error al ingresar número de tarjeta")
    
    # Paso 3: Activar teclado virtual
    def click_continue():
        boton_continuar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'keyboard-input')]"))
        )
        boton_continuar.click()
        return boton_continuar

    retry_action(click_continue, "Error al hacer clic en continuar")
    
    # Paso 4: Ingresar clave mediante teclado virtual
    digitos = ["2", "1", "0", "5", "9", "3"]
    
    def enter_digits():
        for digito in digitos:
            elemento = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//bcp-keyboard//*[text()='{digito}']"))
            )
            elemento.click()
            time.sleep(0.5)
    
    retry_action(enter_digits, "Error al ingresar dígitos")
    
    # Paso 5: Obtener y procesar imagen del captcha
    def get_captcha_image():
        img_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'captcha-container')]//bcp-img/img"))
        )
        return img_element
    
    img_element = retry_action(get_captcha_image, "Error al obtener imagen captcha")
    
    # Procesamiento de la imagen del captcha
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
    
    # Guardar imagen del captcha
    with open('./cliente/input/captcha.jpg', 'wb') as f:
        f.write(img_data)

    # Paso 6: Resolver captcha usando API
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

    # Paso 7: Interactuar con el formulario de captcha
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

    # Paso 8: Seleccionar cuenta
    number_account = '194-2232464-0-40'

    def click_continue_btn():
        btn_continue = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//ciam-form-session-card//form//bcp-button/button"))
        )
        btn_continue.click()
        return btn_continue

    retry_action(click_continue_btn, "Error al hacer clic en continuar")

    def select_account():
        card_account = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, f"//ntlc-account-card//*[text()='{number_account}']"))
        )
        driver.execute_script("arguments[0].click();", card_account)
        return card_account

    try:
        retry_action(select_account, "Error al seleccionar cuenta")
    except Exception as e:
        print("No se logro iniciar sesión")
        raise

def generar_reporte(driver):
    # Obtener fecha actual
    actual_date = datetime.now()

    # Formatear la fecha según lo necesites
    actual_date = actual_date.strftime("%d%m%Y") # Formato DD/MM/YYYY

    # Esperar a que la página cargue completamente
    def wait_for_page():
        return WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='inputDateFrom']"))
        )
    retry_action(wait_for_page, "Error esperando carga de página")

    #Agregar fecha desde
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
    
    
    #Agregar fecha hasta
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

    # Hacer clic en el dropdown
    def click_dropdown():
        dropdown = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//*[@label='Tipo']"))
        )
        dropdown.click()
        return dropdown
    
    retry_action(click_dropdown, "Error al hacer clic en dropdown")
    
    # Seleccionar opción "Ingresos"
    def select_ingresos():
        opcion_ingresos = WebDriverWait(driver, 2).until(
            EC.visibility_of_element_located((By.XPATH, "//div[@class='select-item']//*[text()=' Ingresos ']"))
        )
        opcion_ingresos.click()
        return opcion_ingresos

    retry_action(select_ingresos, "Error al seleccionar opción Ingresos")

    # Esperar cierre dropdown
    def wait_dropdown_close():
        return WebDriverWait(driver, 5).until(
            EC.invisibility_of_element_located((By.CLASS_NAME, "select-item"))
        )
    retry_action(wait_dropdown_close, "Error esperando cierre de dropdown")

    def click_aplicar():
        btn_aplicar = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located((By.XPATH, "//bcp-button-bpbaaa//*[text()= ' Aplicar ']"))
        )
        btn_aplicar.click()
        return btn_aplicar

    retry_action(click_aplicar, "Error al hacer clic en Aplicar")

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
        btn_seleccionar_todas = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='bcp-ffw-btn btn-text']//span[text()='Seleccionar todas']"))
        )
        driver.execute_script("arguments[0].click();", btn_seleccionar_todas)
        return btn_seleccionar_todas

    retry_action(click_seleccionar_todas, "Error al hacer clic en Seleccionar todas")

    time.sleep(2)


    def click_exportar():
        boton_exportar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'bcp-ffw-btn')]//*[text()= ' Exportar ']"))
        )
        driver.execute_script("arguments[0].click();", boton_exportar)
        return boton_exportar

    retry_action(click_exportar, "Error al hacer clic en Exportar")

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


def descarga_fichero(driver):
    """
    Función que gestiona la descarga del archivo
    """
    # Paso 1: Seleccionar opciones de usuario
    button_user = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox' and @value='userId']"))
    )
    driver.execute_script("arguments[0].click();", button_user)

    # Paso 2: Iniciar exportación
    button_export = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button//*[text()='Exportar']"))
    )
    driver.execute_script("arguments[0].click();", button_export)

    # Paso 3: Obtener código de solicitud
    code = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//div[@class='bcp-ffw-modal-content']//div[contains(text(), '040_ultimos')]"))
    )

    n_code = re.search(r'solicitud N° (\d+)', code.text)
    n_code = n_code.group(1)
    print(n_code)
    n_code = n_code.zfill(8)

    # Paso 4: Navegar a archivos solicitados
    button_files = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//bcp-button[@class='bcp-button-host-4-22-0 hydrated']//*[text()=' Ir a archivos solicitados ']"))
    )
    driver.execute_script("arguments[0].click();", button_files)

    # Paso 5: Localizar y descargar archivo
    row_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"//bcp-table-row-9nbaaa[.//p[normalize-space(.)='{n_code}']]"))
    )

    index = row_element.get_attribute("index")

    button_dwld = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, f"//bcp-table-row-9nbaaa[@index='{index}']//span[contains(@class, 'bcp-ffw-sr-only') and text()='Descargar .txt']"))
    )
    driver.execute_script("arguments[0].click();", button_dwld)

    button_txt = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button//span[text()=' Descargar .txt ']"))
    )
    driver.execute_script("arguments[0].click();", button_txt)

    # Esperar descarga
    time.sleep(2)


def bcp_cash_in_descarga_txt():
    """
    Función principal que ejecuta todo el proceso
    """
    driver = create_stealth_driver()
    def retry_login(max_attempts=2):
        """
        Función que reintenta el login hasta 3 veces, actualizando la página en cada intento
        """
        for attempt in range(max_attempts):
            try:
                print(f"Intento de login {attempt + 1}/{max_attempts}")
                login(driver)
                print("Login exitoso")
                return True
            except Exception as e:
                print(f"Error en intento {attempt + 1}: {e}")
                if attempt < max_attempts - 1:  # Si no es el último intento
                    print("Actualizando página y reintentando...")
                    driver.refresh()
                    time.sleep(5)  # Esperar a que la página cargue
                else:
                    print("Se agotaron todos los intentos de login")
                    raise e
        
        return False
    
    # Ejecutar login con reintentos
    retry_login()
    generar_reporte(driver)
    descarga_fichero(driver)
    driver.quit()

# Ejecución principal con manejo de errores
def bot_run(cfg, mensaje):
    try:
        bcp_cash_in_descarga_txt()

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Cerrar navegador
        print("Navegador cerrado")    