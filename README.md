# Py Cash In Bancos

Sistema automatizado de procesamiento de cash-in para bancos peruanos (BCP y BBVA) utilizando Python y Selenium.

## 📋 Descripción

Este proyecto automatiza el proceso de cash-in para múltiples bancos peruanos mediante web scraping. El sistema incluye:

- **Bot 01**: Automatización para BCP
- **Bot 02**: Automatización para BBVA Soles
- **Bot 03**: Automatización para BBVA Dólares

El sistema utiliza Selenium con Chrome para interactuar con los portales bancarios y procesar transacciones de manera automatizada.

## 🏗️ Arquitectura

```
py_cash_in_bancos/
├── main.py                 # Punto de entrada principal
├── variables_globales.py   # Variables globales del sistema
├── config/                 # Configuración del sistema
│   ├── config.ini         # Archivo de configuración
│   └── config.py          # Cargador de configuración
├── modulos/               # Módulos de bots
│   ├── bot_00_configuracion.py
│   ├── bot_01_ci_bcp.py
│   ├── bot_02_bbva_ci_soles.py
│   └── bot_03_bbva_ci_dolares.py
├── utilidades/            # Utilidades del sistema
│   ├── logger.py          # Sistema de logging
│   ├── limpieza.py        # Limpieza de procesos
│   ├── excepciones.py     # Manejo de excepciones
│   ├── gmail_sender.py    # Envío de emails
│   ├── google_auth.py     # Autenticación Google
│   ├── google_drive.py    # Integración Google Drive
│   └── notificaiones_whook.py # Notificaciones webhook
├── cliente/               # Directorio de datos del cliente
│   ├── input/             # Archivos de entrada
│   ├── output/            # Archivos de salida
│   └── perfil/            # Perfiles de navegación
│       ├── bcp/
│       ├── bbva_soles/
│       └── bbva_dolares/
├── logs/                  # Archivos de log
├── dockerfile             # Configuración Docker
└── requirements.txt       # Dependencias Python
```

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.11+
- Docker y Docker Compose (opcional)
- Git

### Instalación con Docker (Recomendado)

1. **Clonar el repositorio:**
   ```bash
   git clone <url-del-repositorio>
   cd py_cash_in_bancos
   ```

2. **Configurar el archivo de configuración:**
   ```bash
   # Editar config/config.ini con tus credenciales
   nano config/config.ini
   ```

3. **Construir y ejecutar con Docker:**
   ```bash
   # Construir la imagen
   docker build -t py-cash-in-bancos .
   
   # Ejecutar el contenedor
   docker run -v $(pwd)/logs:/app/logs -v $(pwd)/cliente:/app/cliente py-cash-in-bancos
   ```

### Instalación Local

1. **Instalar Python 3.11:**
   ```bash
   # En Ubuntu/Debian
   sudo apt update
   sudo apt install python3.11 python3.11-pip python3.11-venv
   
   # En macOS
   brew install python@3.11
   
   # En Windows
   # Descargar desde python.org
   ```

2. **Crear entorno virtual:**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate  # Linux/macOS
   # o
   .venv\Scripts\activate     # Windows
   ```

3. **Instalar Chrome y ChromeDriver:**
   ```bash
   # Instalar Chrome
   wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
   echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
   sudo apt update
   sudo apt install google-chrome-stable
   
   # Instalar ChromeDriver (se instala automáticamente con webdriver-manager)
   pip install webdriver-manager
   ```

4. **Instalar dependencias Python:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Ejecutar el proyecto:**
   ```bash
   python main.py
   ```

## ⚙️ Configuración

### Archivo config.ini

El archivo `config/config.ini` contiene toda la configuración del sistema:

```ini
[general]
nombre_bot = py_cash_in_bancos
version = 1.0

[rutas]
ruta_bot = ./
ruta_log = ./logs/
ruta_input = ./cliente/input
ruta_output = ./cliente/output
ruta_perfil_bbva_soles = ./cliente/perfil/bbva_soles
ruta_perfil_bcp = ./cliente/perfil/bcp
ruta_perfil_bbva_dolares = ./cliente/perfil/bbva_dolares

[archivos]
archivos_log = log_ddmmyy_hhmmss.log

[api]
api_gescom_transacciones = "http://144.202.42.200:8080/transactions"

[reintentos]
reintentos_max = 3
```

### Variables de Entorno (Docker)

```bash
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
DEBIAN_FRONTEND=noninteractive
TZ=America/Lima
```

## 🎯 Uso

### Ejecución Manual

```bash
# Con Docker
docker build -t py-cash-in-bancos .
docker run -v $(pwd)/logs:/app/logs -v $(pwd)/cliente:/app/cliente py-cash-in-bancos

# Local
python main.py
```

### Ejecución Programada

Para ejecutar el bot de forma programada, puedes usar cron:

```bash
# Editar crontab
crontab -e

# Agregar línea para ejecutar cada hora
0 * * * * cd /path/to/py_cash_in_bancos && python main.py >> logs/cron.log 2>&1

# Para ejecutar con Docker
0 * * * * cd /path/to/py_cash_in_bancos && docker run --rm -v $(pwd)/logs:/app/logs -v $(pwd)/cliente:/app/cliente py-cash-in-bancos
```

### Monitoreo

Los logs se guardan en el directorio `logs/` con el formato:
- `log_ddmmyy_hhmmss.log`

Para monitorear en tiempo real:
```bash
# Con Docker
docker logs -f <container_id>

# Local
tail -f logs/log_*.log
```

## 🔧 Desarrollo

### Estructura de Módulos

Cada bot sigue la misma estructura:

```python
def bot_run(cfg, mensaje):
    """
    Función principal del bot
    
    Args:
        cfg: Configuración cargada
        mensaje: Mensaje acumulado de bots anteriores
    
    Returns:
        tuple: (success, message)
    """
    try:
        # Lógica del bot
        return True, "Bot ejecutado exitosamente"
    except Exception as e:
        return False, f"Error: {str(e)}"
```

### Agregar un Nuevo Bot

1. Crear archivo en `modulos/bot_XX_nombre.py`
2. Implementar función `bot_run(cfg, mensaje)`
3. Agregar al orquestador en `main.py`:

```python
from modulos.bot_XX_nombre import bot_run as Bot_XX_Nombre

# En la función main()
for bot_name, bot_function in [
    ("Bot 01 - BCP", Bot_01_CI_BCP),
    ("Bot 02 - BBVA Soles", Bot_02_CI_BBVA_SOLES),
    ("Bot 03 - BBVA Dólares", Bot_03_CI_BBVA_DOLARES),
    ("Bot XX - Nuevo Bot", Bot_XX_Nombre),  # Agregar aquí
]:
```

## 📊 Logs y Monitoreo

### Niveles de Log

- **INFO**: Información general del proceso
- **WARNING**: Advertencias no críticas
- **ERROR**: Errores que requieren atención
- **DEBUG**: Información detallada para desarrollo

### Notificaciones

El sistema envía notificaciones a través de webhook cuando:
- Inicia el proceso
- Completa cada bot
- Ocurre un error
- Finaliza el proceso

### Información del Sistema

El sistema recopila automáticamente información del sistema:
- Plataforma y versión de Python
- Procesador y uso de CPU
- Memoria disponible
- Número de núcleos CPU

## 🛠️ Solución de Problemas

### Problemas Comunes

1. **Chrome no inicia en Docker:**
   ```bash
   # Verificar que el contenedor tiene acceso a X11
   docker run --rm -it --privileged -v /tmp/.X11-unix:/tmp/.X11-unix:rw py-cash-in-bancos
   
   # Usar modo headless
   # El Dockerfile ya está configurado para modo headless
   ```

2. **Error de permisos:**
   ```bash
   # Dar permisos a los directorios
   chmod -R 755 logs cliente/
   
   # En Windows, ejecutar como administrador
   ```

3. **Problemas de red:**
   ```bash
   # Verificar conectividad
   docker run --rm py-cash-in-bancos ping google.com
   
   # Verificar DNS
   docker run --rm py-cash-in-bancos nslookup google.com
   ```

4. **Problemas con ChromeDriver:**
   ```bash
   # Verificar versión de Chrome
   google-chrome --version
   
   # Actualizar webdriver-manager
   pip install --upgrade webdriver-manager
   ```

### Debugging

Para ejecutar en modo debug:

```bash
# Con Docker
docker run --rm -it py-cash-in-bancos python -u main.py

# Local
python -u main.py
```

### Logs Detallados

Para obtener logs más detallados:

```bash
# Configurar nivel de log en el código
logging.getLogger().setLevel(logging.DEBUG)

# Ver logs en tiempo real
docker run --rm py-cash-in-bancos 2>&1 | tee debug.log
```

## 🔒 Seguridad

### Credenciales

- Nunca committear credenciales en el código
- Usar variables de entorno para datos sensibles
- Rotar credenciales regularmente
- Usar archivos `.env` para configuración local

### Red

- Usar VPN si es necesario
- Configurar firewalls apropiadamente
- Monitorear conexiones salientes
- Usar HTTPS para todas las comunicaciones

### Contenedores

- Ejecutar contenedores con privilegios mínimos
- Usar imágenes base oficiales
- Escanear imágenes regularmente
- Mantener dependencias actualizadas

## ⚡ Rendimiento

### Optimizaciones

- Usar headless mode para Chrome en producción
- Implementar timeouts apropiados
- Usar conexiones persistentes cuando sea posible
- Implementar reintentos inteligentes

### Monitoreo de Recursos

```bash
# Ver uso de recursos del contenedor
docker stats <container_id>

# Ver logs de rendimiento
docker logs <container_id> | grep "tiempo_total"

# Monitorear uso de memoria
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Configuración de Chrome

El sistema está optimizado para ejecutar Chrome en contenedores:

```python
# Opciones de Chrome para contenedores
chrome_options = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--headless',
    '--disable-web-security',
    '--disable-features=VizDisplayCompositor'
]
```

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Para soporte técnico o preguntas:

- Crear un issue en GitHub
- Contactar al equipo de desarrollo
- Revisar la documentación en la wiki
- Consultar los logs de error
