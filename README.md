# Py Cash In Bancos

Sistema automatizado de procesamiento de cash-in para bancos peruanos (BCP y BBVA) utilizando Python y Selenium.

## 📋 Descripción

Este proyecto automatiza el proceso de cash-in para múltiples bancos peruanos mediante web scraping. El sistema incluye:

- **Bot 01**: Automatización para BCP
- **Bot 02**: Automatización para BBVA Soles
- **Bot 03**: Automatización para BBVA Dólares

El sistema utiliza Selenium con Chrome para interactuar con los portales bancarios y procesar transacciones de manera automatizada.

## Arquitectura

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
│   └── notificaiones_whook.py # Notificaciones webhook
├── cliente/               # Directorio de datos del cliente
│   ├── input/             # Archivos de entrada
│   └── output/            # Archivos de salida
└── logs/                  # Archivos de log
```

## Instalación y Configuración

### Prerrequisitos

- Docker y Docker Compose
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

3. **Construir y ejecutar con Docker Compose:**
   ```bash
   docker-compose up --build
   ```

### Instalación Local

1. **Instalar Python 3.11:**
   ```bash
   # En Ubuntu/Debian
   sudo apt update
   sudo apt install python3.11 python3.11-pip
   
   # En macOS
   brew install python@3.11
   ```

2. **Instalar Chrome y ChromeDriver:**
   ```bash
   # Instalar Chrome
   wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
   echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
   sudo apt update
   sudo apt install google-chrome-stable
   
   # Instalar ChromeDriver
   pip install webdriver-manager
   ```

3. **Instalar dependencias Python:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar el proyecto:**
   ```bash
   python main.py
   ```

## Configuración

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

[archivos]
archivos_input = factura_ventas.xlsx
archivos_output = factura_ventas_procesada_ddmmyy.xlsx
archivos_log = log_ddmmyy_hhmmss.log

[api]
api_gescom_transacciones = "http://144.202.42.200:8080/transactions"

[bd]
bd_host = "localhost"
bd_puerto = "5432"
bd_usuario = "postgres"
bd_clave = "password"
bd_esquema = "public"

[webhook]
webhook_rpa_url = "https://chat.googleapis.com/v1/spaces/..."
```

### Variables de Entorno (Docker)

```bash
PYTHONUNBUFFERED=1
TZ=America/Lima
```

## Uso

### Ejecución Manual

```bash
# Con Docker
docker-compose up

# Local
python main.py
```

### Ejecución Programada

Para ejecutar el bot de forma programada, puedes usar cron:

```bash
# Editar crontab
crontab -e

# Agregar línea para ejecutar cada hora
0 * * * * cd /path/to/py_cash_in_bancos && docker-compose up -d
```

### Monitoreo

Los logs se guardan en el directorio `logs/` con el formato:
- `log_ddmmyy_hhmmss.log`

Para monitorear en tiempo real:
```bash
# Con Docker
docker-compose logs -f

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
3. Agregar al orquestador en `main.py`

## Logs y Monitoreo

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

## Solución de Problemas

### Problemas Comunes

1. **Chrome no inicia en Docker:**
   ```bash
   # Verificar que el contenedor tiene acceso a X11
   docker run --rm -it --privileged -v /tmp/.X11-unix:/tmp/.X11-unix:rw py-cash-in-bancos
   ```

2. **Error de permisos:**
   ```bash
   # Dar permisos a los directorios
   chmod -R 755 logs cliente/
   ```

3. **Problemas de red:**
   ```bash
   # Verificar conectividad
   docker-compose exec py-cash-in-bancos ping google.com
   ```

### Debugging

Para ejecutar en modo debug:

```bash
# Con Docker
docker-compose run --rm py-cash-in-bancos python -u main.py

# Local
python -u main.py
```

## Seguridad

### Credenciales

- Nunca committear credenciales en el código
- Usar variables de entorno para datos sensibles
- Rotar credenciales regularmente

### Red

- Usar VPN si es necesario
- Configurar firewalls apropiadamente
- Monitorear conexiones salientes

## Rendimiento

### Optimizaciones

- Usar headless mode para Chrome en producción
- Implementar timeouts apropiados
- Usar conexiones persistentes cuando sea posible

### Monitoreo de Recursos

```bash
# Ver uso de recursos del contenedor
docker stats py-cash-in-bancos

# Ver logs de rendimiento
docker-compose logs | grep "tiempo_total"
```

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

Para soporte técnico o preguntas:

- Crear un issue en GitHub
- Contactar al equipo de desarrollo
- Revisar la documentación en la wiki

## Changelog

### v1.0.0
- Implementación inicial de bots para BCP y BBVA
- Sistema de configuración centralizado
- Logging y notificaciones webhook
- Soporte para Docker y Docker Compose 