# Matera Inteligente · Backend (Fase 2)

API Flask con arquitectura hexagonal. El dominio (`domain/`) no importa Flask,
JWT, CSV ni SQLite: todo eso vive en `adaptadores/` y se conecta en un único
punto, `app.py`.

El frontend está en su propio repositorio (`matera-frontend`) y solo habla con
esta API por el contrato de `docs/API.md`.

## Requisitos

Python 3.9 o superior.

```bash
cd Backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Variables de entorno

```bash
export MATERA_JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export MATERA_TABLA=csv                        # csv | bd
export MATERA_DB=matera.db
export MATERA_CORS_ORIGINS=http://localhost:5500
```

`MATERA_JWT_SECRET` es obligatoria y debe medir al menos 16 caracteres: sin
ella la aplicación no arranca, para que nunca corra con un secreto conocido.
Las demás tienen valor por defecto. Con `python-dotenv` instalado se puede
poner todo en un archivo `.env` (que está en `.gitignore`).

## Preparar la base de datos

```bash
python3 scripts/cargar_datos.py --db matera.db --dispositivos 3
```

Crea las tablas, carga `infrastructure/especies.csv` en la tabla `especies` y
genera dispositivos de fábrica con su código de emparejamiento. Anota uno de
esos códigos: es el que se escribe en el front para vincular la planta.

## Ejecutar

**Terminal 1 — backend** (puerto 5000):

```bash
cd Backend && source .venv/bin/activate
python3 app.py
curl http://127.0.0.1:5000/health
```

**Terminal 2 — frontend** (repositorio `matera-frontend`, puerto 5500):

```bash
cd matera-frontend
python3 -m http.server 5500
```

El puerto de aquí y el de `MATERA_CORS_ORIGINS` tienen que ser el mismo, y
`config.js` del front debe apuntar a `http://127.0.0.1:5000`.

**Terminal 3 — simulador del ESP32.** Primero regístrate en el front, vincula
la planta con el código de emparejamiento y copia el token de dispositivo que
aparece una sola vez:

```bash
cd Backend && source .venv/bin/activate
python3 simulador/simulador_esp32.py \
  --url http://127.0.0.1:5000 \
  --dispositivo <id del dispositivo> \
  --token <token_dispositivo> \
  --especie orquidea \
  --intervalo 5
```

El simulador genera ~75 % de lecturas normales, ~15 % fuera del rango de la
especie (se guardan como BAJO/ALTO) y ~10 % inválidas (humedad 140, texto en
vez de número, campo faltante, fecha mal formada), que la API rechaza con 400
sin guardarlas. `--token-malo` demuestra el 401 y `--token-usuario` el 403.

Sus rangos están copiados de `infrastructure/especies.csv`: si se edita el CSV,
hay que editarlos también, o las lecturas "normales" llegarán fuera de rango.

## Pruebas

```bash
cd Backend
python3 -m unittest discover
```

128 pruebas. Las de `tests/dominio/` corren sin servidor, sin archivos y sin
base de datos, con dobles de prueba de los puertos de salida.
`tests/test_extremo_a_extremo.py` levanta la aplicación real contra una base
temporal y recorre el flujo completo **dos veces**: una con `MATERA_TABLA=csv`
y otra con `bd`. Que las dos pasen es la prueba de que la tabla de referencia
es intercambiable sin tocar el dominio.

## Demostración

1. Los tres procesos arriba; las lecturas aparecen solas en el front cada 5 s.
2. `export MATERA_TABLA=bd`, reiniciar el backend, recargar el front: mismo
   resultado, `domain/` intacto.
3. Un segundo usuario pide `GET /api/plantas/{id}/estado` de la planta ajena:
   403.
4. `git show --stat <hash>` del commit del adaptador de dispositivos y el
   simulador: ni una línea de `domain/`.

## Estructura

```
Backend/
  app.py                  create_app(): ÚNICO punto de composición
  config.py               lectura de variables de entorno
  domain/                 sin flask, jwt, csv, sqlite3 ni json
    modelo.py  validador.py  servicios.py  servicios_cuentas.py
    comandos.py  resultados.py  excepciones.py  excepciones_cuentas.py
    puertos/entrada.py  puertos/salida.py
  adaptadores/
    entrada/  api_auth.py  api_front.py  api_dispositivos.py
              seguridad.py  errores.py  peticiones.py
    salida/   tabla_csv.py  tabla_bd.py  historial_bd.py  planta_bd.py
              dispositivo_bd.py  usuario_bd.py  emisor_jwt.py
              hasher_password.py  bd.py
  simulador/simulador_esp32.py
  scripts/cargar_datos.py
  infrastructure/especies.csv
  tests/dominio/  tests/salida/  tests/test_extremo_a_extremo.py
  docs/API.md
```
