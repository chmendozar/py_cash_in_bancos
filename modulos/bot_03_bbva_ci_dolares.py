from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common import action_chains
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from selenium.webdriver.common.keys import Keys
from selenium_stealth import stealth
from selenium.webdriver.common.action_chains import ActionChains
from utilidades.notificaiones_whook import WebhookNotifier
import logging
import base64
from pathlib import Path
import requests
import os
import platform

logger = logging.getLogger("Bot 03 - BBVA CI Dolares")

#Función para imprimir la información de un elemento de html
def print_element_info(elemento):
    children = elemento.find_elements(By.CSS_SELECTOR, "*")
    # Imprimir tag y clase
    for child in children:
        print(child.tag_name, "-", child.get_attribute("class"))

def create_stealth_webdriver(cfg):
    """
    Crea un driver de Chrome configurado para descargar archivos en la ruta indicada en cfg['rutas']['ruta_input']
    """
    download_path = str(Path(cfg['rutas']['ruta_input']).absolute())
    profile_dir = str(Path(cfg['rutas']['ruta_perfil_bbva_dolares']).absolute())
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={profile_dir}")
    
    # Argumentos anti-detección mejorados
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-browser-side-navigation")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-first-run")
    options.add_argument("--no-service-autorun")
    options.add_argument("--password-store=basic")
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    
    # User agent más actualizado
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

    prefs = {
        "download.default_directory": download_path,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1,
        "profile.default_content_setting_values.cookies": 1,
        "profile.block_third_party_cookies": False,
        "profile.default_content_setting_values.plugins": 1,
        "profile.content_settings.plugin_whitelist.adobe-flash-player": 1,
        "profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player": 1
    }
    options.add_experimental_option("prefs", prefs)

    # Set longer timeout for ChromeDriver installation
    os.environ['PYDEVD_WARN_EVALUATION_TIMEOUT'] = '30'  # 30 seconds timeout
    os.environ['PYDEVD_UNBLOCK_THREADS_TIMEOUT'] = '30'  # Unblock threads after 30 seconds
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Ejecutar scripts anti-detección adicionales
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['es-ES', 'es']})")
    driver.execute_script("window.chrome = {runtime: {}}")

    stealth(driver,
        languages=["es-ES", "es"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    return driver


def bbva_ci_dolares_descarga_txt(cfg):
    """
    Función principal que ejecuta todo el proceso de descarga de movimientos BBVA DOLARES
    """
    driver = None
    try:
        logger.info("Iniciando proceso completo de descarga de movimientos BBVA DOLARES")
        driver = create_stealth_webdriver(cfg)

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
        
        # Reintentar desde selección de cobros si hay problemas
        max_flow_attempts = 3
        for flow_attempt in range(max_flow_attempts):
            try:
                logger.info(f"Intento de flujo desde cobros {flow_attempt + 1}/{max_flow_attempts}")
                select_charges(driver)
                select_paid_collection(driver)
                download_txt(driver)
                logger.info("Proceso de descarga de movimientos BBVA DOLARES finalizado correctamente")
                return True
            except Exception as e:
                logger.warning(f"Error en flujo intento {flow_attempt + 1}: {e}")
                if flow_attempt < max_flow_attempts - 1:
                    logger.info("Reiniciando desde selección de cobros...")
                    # Solo volver al contexto principal, no recargar página completa
                    driver.switch_to.default_content()
                    time.sleep(3)
                else:
                    logger.error("Se agotaron todos los intentos de flujo")
                    raise e
        
        return False
    except Exception as e:
        logger.error(f"Ocurrió un error en bbva_ci_dolares_descarga_txt: {e}")
        return False
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
        wait = WebDriverWait(driver, 15)

        # Limpiar cookies y storage
        driver.delete_all_cookies()
        driver.get("https://www.bbvanetcash.pe")
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        time.sleep(5)  # Espera para carga inicial

        # Ingresar código de empresa - esperar que esté presente y sea clickeable
        company_code_input = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='cod_emp']"))
        )
        company_code_input.clear()
        company_code_input.send_keys("331771")
        time.sleep(1)

        # Ingresar código de usuario - esperar que esté presente y sea clickeable
        user_code_input = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='cod_usu']"))
        )
        user_code_input.clear()
        user_code_input.send_keys("00000093")
        time.sleep(1)

        # Ingresar contraseña - esperar que esté presente y sea clickeable
        password_input = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//input[@name='eai_password']"))
        )
        password_input.clear()
        password_input.send_keys("EEDEtpp2024")
        time.sleep(3)

        # Click en Ingresar - esperar que el botón esté clickeable
        login_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Ingresar']"))
        )
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
    wait = WebDriverWait(driver, 15)
    time.sleep(5)
    
    # Esperar que el app-template esté presente
    app_template_host = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "bbva-btge-app-template"))
    )
    app_template_shadow_root = driver.execute_script("return arguments[0].shadowRoot", app_template_host)

    # Esperar que el sidebar-menu esté presente
    sidebar_menu_host = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "bbva-btge-sidebar-menu"))
    )
    sidebar_menu_shadow_root = driver.execute_script("return arguments[0].shadowRoot", sidebar_menu_host)

    # Esperar hasta que el elemento del menú de cargos esté clickeable
    # Nota: Para elementos dentro de shadow DOM, usamos JavaScript para verificar
    def charges_menu_clickable(driver):
        try:
            charges_menu_item = sidebar_menu_shadow_root.find_element(
                By.CSS_SELECTOR,
                "bbva-web-navigation-menu-item[icon='bbva:paysheetdollar']"
            )
            return charges_menu_item.is_enabled() and charges_menu_item.is_displayed()
        except:
            return False

    wait.until(charges_menu_clickable)
    
    charges_menu_item = sidebar_menu_shadow_root.find_element(
        By.CSS_SELECTOR,
        "bbva-web-navigation-menu-item[icon='bbva:paysheetdollar']"
    )
    charges_menu_item.click()
    time.sleep(3)

def select_paid_collection(driver):
    wait = WebDriverWait(driver, 15)
    
    # Step 1: esperar que el shadow host principal esté presente
    main_shadow_host = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "bbva-btge-menurization-landing-solution-page"))
    )
    main_shadow_root = driver.execute_script("return arguments[0].shadowRoot", main_shadow_host)

    # Step 2: esperar el iframe dentro del primer shadow DOM
    def iframe_host_present(driver):
        try:
            iframe_host = main_shadow_root.find_element(By.CSS_SELECTOR, "bbva-core-iframe")
            return iframe_host is not None
        except:
            return False

    wait.until(iframe_host_present)
    iframe_host = main_shadow_root.find_element(By.CSS_SELECTOR, "bbva-core-iframe")
    iframe_shadow_root = driver.execute_script("return arguments[0].shadowRoot", iframe_host)
    
    # Esperar que el iframe esté presente y cambiar a él
    def core_iframe_present(driver):
        try:
            core_iframe_element = iframe_shadow_root.find_element(By.CSS_SELECTOR, "iframe")
            return core_iframe_element is not None
        except:
            return False

    wait.until(core_iframe_present)
    core_iframe_element = iframe_shadow_root.find_element(By.CSS_SELECTOR, "iframe")
    driver.switch_to.frame(core_iframe_element)

    # Step 3: esperar que el segundo shadow host esté presente dentro del iframe
    layout_shadow_host = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "bbva-btge-menurization-landing-solution-home-page"))
    )
    layout_shadow_root = driver.execute_script("return arguments[0].shadowRoot", layout_shadow_host)

    # Step 4: esperar que los links estén presentes y buscar 'Recaudos pagados'
    def recaudos_link_present(driver):
        try:
            link_elements = layout_shadow_root.find_elements(By.CSS_SELECTOR, "bbva-web-link")
            for link_element in link_elements:
                if link_element.text.strip() == "Recaudos pagados":
                    return link_element
            return False
        except:
            return False

    recaudos_link = wait.until(recaudos_link_present)
    print("Found 'Recaudos pagados', clicking the link.")
    recaudos_link.click()

    # Step 6: esperar que la siguiente página se cargue
    time.sleep(5)

def download_txt(driver):
    wait = WebDriverWait(driver, 15)
    time.sleep(5)

    # Step 0: regresar al DOM principal
    driver.switch_to.default_content()
    
    # Esperar que legacy-page esté presente
    legacy_page_host = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "legacy-page"))
    )

    # Step 1: entrar al shadowRoot de legacy-page
    legacy_page_shadow_root = driver.execute_script("return arguments[0].shadowRoot", legacy_page_host)

    # Step 2: esperar y entrar al shadowRoot de bbva-core-iframe
    def iframe_host_in_legacy_present(driver):
        try:
            iframe_host = legacy_page_shadow_root.find_element(By.CSS_SELECTOR, "bbva-core-iframe")
            return iframe_host is not None
        except:
            return False

    wait.until(iframe_host_in_legacy_present)
    iframe_host = legacy_page_shadow_root.find_element(By.CSS_SELECTOR, "bbva-core-iframe")
    iframe_shadow_root = driver.execute_script("return arguments[0].shadowRoot", iframe_host)

    # Step 3: esperar y cambiar al iframe interno
    def core_iframe_in_legacy_present(driver):
        try:
            core_iframe_element = iframe_shadow_root.find_element(By.CSS_SELECTOR, "iframe")
            return core_iframe_element is not None
        except:
            return False

    wait.until(core_iframe_in_legacy_present)
    core_iframe_element = iframe_shadow_root.find_element(By.CSS_SELECTOR, "iframe")
    driver.switch_to.frame(core_iframe_element)

    print("Inside iframe#bbvaIframe")

    # Step 4: esperar iframe#kyop-central-load-area y cambiar a él
    kyop_iframe_element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#kyop-central-load-area"))
    )
    driver.switch_to.frame(kyop_iframe_element)

    print("Inside iframe#kyop-central-load-area")
    time.sleep(10)

    # Step 5: esperar y hacer clic en el enlace de cuenta deseado (LIGO-LA MAGICA DOLARES)
    dolares_account_link = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'LIGO-LA MAGICA DOLARES')]"))
    )
    ActionChains(driver).move_to_element(dolares_account_link).click().perform()
    time.sleep(5)
    
    # Esperar que el campo de fecha inicial esté presente y clickeable
    start_date_input = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//input[@name='fecini']"))
    )
    
    # Movimiento más humano para interactuar con campos de fecha
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", start_date_input)
    time.sleep(1)
    ActionChains(driver).move_to_element(start_date_input).click().perform()
    time.sleep(2)  # Pausa más larga como lo haría un humano
    start_date_input.send_keys(Keys.ENTER)
    time.sleep(1)
    start_date_input.send_keys(Keys.TAB)
    time.sleep(3)  # Pausa entre campos

    # Esperar que el campo de fecha final esté presente y clickeable
    end_date_input = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//input[@name='fecfin']"))
    )
    
    # Movimiento más humano para el segundo campo
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", end_date_input)
    time.sleep(1)
    ActionChains(driver).move_to_element(end_date_input).click().perform()
    time.sleep(2)
    end_date_input.send_keys(Keys.ENTER)
    time.sleep(1)
    end_date_input.send_keys(Keys.TAB)
    time.sleep(3)

    def click_consultar():
        try:
            logger.info("Esperando el botón 'Consultar'...")

            # Espera hasta que el botón esté presente y clickeable
            consult_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@value='Consultar']"))
            )

            # Scroll hacia el botón para asegurar que esté visible
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", consult_button)
            time.sleep(2)  # Esperar que termine el scroll

            # Simular movimiento de mouse humano
            ActionChains(driver).move_to_element(consult_button).perform()
            time.sleep(1)  # Pausa como lo haría un humano

            # Intentar clic normal primero
            try:
                consult_button.click()
                logger.info("Se hizo clic en el botón 'Consultar' con click normal.")
            except:
                # Si falla, usar JavaScript como respaldo
                driver.execute_script("arguments[0].click();", consult_button)
                logger.info("Se hizo clic en el botón 'Consultar' con JavaScript.")

            # Esperar más tiempo después del clic para permitir procesamiento
            time.sleep(5)

        except Exception as e:
            logger.error(f"Error al intentar hacer clic en el botón 'Consultar': {e}")
            raise e

    click_consultar()
    
    # Verificar si aparece el botón de descarga TXT en 60 segundos
    try:
        download_link = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@title='Descargar Txt']"))
        )
        logger.info("Botón de descarga TXT encontrado exitosamente")
        
        # Scroll hacia el link de descarga y hacer clic más humano
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", download_link)
        time.sleep(2)
        ActionChains(driver).move_to_element(download_link).click().perform()
        time.sleep(10)
        
    except Exception as e:
        logger.warning(f"No se encontró el botón de descarga TXT en 60 segundos: {e}")
        # Si no aparece el botón de descarga, lanzar excepción para reiniciar desde cobros
        raise Exception("Botón de descarga TXT no encontrado - se requiere reinicio desde selección de cobros")

MAX_ATTEMPTS_FLOW = 3

def bbva_ci_dolares_cargar_gescom(cfg):
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
            contenido_b64 = base64.b64encode(archivo.read())

        payload = {
            "format": "Bbva_Recaudación",
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
        logger.info("Iniciando ejecución principal del bot BBVA DOLARES")
        
        webhook = WebhookNotifier(cfg['webhook']['webhook_rpa_url'])        
        resultado = bbva_ci_dolares_descarga_txt(cfg)
        webhook.send_notification(f"Bot BBVA DOLARES - Archivo descargado")
        if resultado:
            webhook.send_notification(f"Bot BBVA DOLARES: Cargar archivo a GESCOM")
            bbva_ci_dolares_cargar_gescom(cfg)
            mensaje = "Carga de archivo exitosa"
            webhook.send_notification(f"Bot BBVA DOLARES: Carga de archivo exitosa")
            resultado = True

    except Exception as e:
        logger.error(f"Error en bot BBVA DOLARES: {e}")
        if platform.system() == 'Windows':
            os.system("taskkill /im chrome.exe /f")
        else:
            os.system("pkill -f chrome")
        raise Exception(f"Error en bot BBVA DOLARES: {e}") from e

    finally:
        logger.info("Navegador cerrado")
        return resultado, mensaje