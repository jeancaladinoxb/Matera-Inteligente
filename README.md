#  Matera Inteligente

Este proyecto implementa el núcleo (Backend y Frontend) de una matera inteligente siguiendo los principios de la **Arquitectura Limpia** (Clean Architecture) y **SOLID**.

## Requisitos Previos

- Python 3.9 o superior
- Un navegador web moderno (Chrome, Firefox, Safari)

## Instrucciones de Ejecución del Backend

El backend está construido con Python y Flask, y responde exclusivamente con JSON. Sigue estos pasos para ejecutarlo:

1. Abre una terminal y ubícate en la raíz del proyecto (`MateraInteligente/`).
2. Activa tu entorno virtual (si estás usando uno):
   ```bash
   source .venv/bin/activate
   ```
3. Instala las dependencias necesarias (Flask y Flask-CORS):
   ```bash
   pip install flask flask-cors
   ```
4. Inicia el servidor de Flask ejecutando el archivo principal:
   ```bash
   python3 Backend/app.py
   ```
5. El servidor estará corriendo en `http://127.0.0.1:5000`.

##  Instrucciones de Ejecución del Frontend

El frontend es completamente independiente (HTML, CSS, JS estáticos) y se comunica con el backend mediante `fetch` asíncrono.

1. Asegúrate de que el Backend esté corriendo (Paso anterior).
2. Ve a la carpeta `Frontend/` en tu explorador de archivos.
3. Haz doble clic en el archivo `index.html` para abrirlo en tu navegador. 
   *(Alternativamente, puedes usar la extensión "Live Server" en VS Code).*
4. ¡Disfruta de la interfaz con estilo Glassmorphism! Selecciona tu planta, ingresa los datos y analiza su vitalidad sin recargar la página.

##  Pruebas Unitarias del Dominio

Las reglas de negocio (Dominio) están completamente desacopladas del framework web y de los datos reales. Para ejecutar las pruebas (que usan dobles de prueba/Mocks):

1. Abre una terminal.
2. Ingresa a la carpeta del Backend:
   ```bash
   cd Backend
   ```
3. Ejecuta el descubridor de pruebas de Python:
   ```bash
   python3 -m unittest discover -s tests
   ```
4. Verás que se ejecutan exitosamente (OK) las pruebas que validan los rangos, casos de error y los códigos HTTP.
