# Backend de Matera Inteligente — Fase 2
## 1. Qué es esto
Este backend Flask expone la API de evaluación y un adaptador de entrada para lecturas de dispositivos.
El adaptador valida JWT y traduce HTTP/JSON a un comando; las reglas de negocio corresponden al dominio.
El dominio real lo entrega otro integrante; temporalmente `app.py` usa `fakes_temporales.py`.
Para integrarlo, sustituye la creación de `FakeRegistrarLectura` en `app.py` por el caso de uso real que implemente `registrar(cmd)`.

## 2. Requisitos
- Python 3.9 o superior.
- Dependencias importadas: `flask`, `flask-cors`, `PyJWT`; no hay `requirements.txt` ni versiones fijadas.
- macOS/Linux, desde la raíz:

```bash
python3 -m venv Backend/.venv
source Backend/.venv/bin/activate
python3 -m pip install Flask flask-cors PyJWT
```
- Windows PowerShell, desde la raíz:

```powershell
py -3 -m venv Backend\.venv
Backend\.venv\Scripts\Activate.ps1
python -m pip install Flask flask-cors PyJWT
```
## 3. Estructura de carpetas relevante
```text
Backend/
├── app.py
├── adaptadores/entrada/{api_dispositivos.py,api_front.py,errores.py,peticiones.py,seguridad.py}
├── domain/{comandos.py,excepciones.py}
├── fakes_temporales.py
├── simulador/simulador_esp32.py
└── tests/{test_api.py,test_domain.py}
```

- `app.py`: configura Flask y registra el adaptador de dispositivos y los endpoints de evaluación.
- `api_dispositivos.py`: valida fecha y traduce JSON a `RegistrarLecturaCmd`; delega el registro.
- `seguridad.py`: valida JWT HS256 y roles; no emite tokens.
- `errores.py`: convierte excepciones conocidas a HTTP y registra errores inesperados como 500.
- `peticiones.py`: valida forma/tipos de los datos; no contiene reglas de negocio.
- `api_front.py`: define rutas de usuario, pero su blueprint no está registrado en `app.py`.
- `domain/comandos.py` y `domain/excepciones.py`: comando de lectura y excepciones requeridas por el adaptador.
- `fakes_temporales.py`: fake que solo rechaza humedad fuera de 0–100 y devuelve datos fijos.
- `simulador_esp32.py`: genera lecturas y las envía al endpoint de dispositivos.
- `tests/`: pruebas de API/dominio; no hay pruebas específicas de JWT o del simulador.

Los adaptadores traducen entre HTTP/JSON y comandos/respuestas; no sustituyen las reglas del dominio.

## 4. Variables de entorno
`MATERA_JWT_SECRET` es obligatoria, no tiene valor por defecto y debe ser igual en quien firma y quien verifica. Evita aceptar tokens firmados con un secreto conocido/inseguro. Si falta durante una petición, puede terminar como HTTP 500 por el manejador genérico. El código no consulta otras variables de entorno.

Genera un secreto local y exporta el mismo valor en cada terminal que ejecute la API o firme tokens:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
export MATERA_JWT_SECRET="TU_SECRETO_GENERADO"
```
En PowerShell, exporta el valor generado en esa terminal:

```powershell
$env:MATERA_JWT_SECRET = "TU_SECRETO_GENERADO"
```
## 5. Ejecutar el backend
Desde la raíz, activa el entorno virtual y ejecuta:

```bash
cd Backend
python3 app.py
```
El servidor usa el puerto 5000. Para comprobar qué responde y detectar un proceso que escucha:

```bash
curl -i http://127.0.0.1:5000/health
lsof -nP -iTCP:5000 -sTCP:LISTEN
```
En macOS AirPlay puede ocupar el puerto. `app.py` no permite configurar otro puerto por variable/argumento; desde `Backend`, usa:

```bash
python3 -c 'import app; app.app.run(debug=True, port=5001)'
curl -i http://127.0.0.1:5001/health
```
Con ese puerto, pasa `--url http://127.0.0.1:5001` al simulador.

## 6. Generar tokens de prueba
El algoritmo es HS256. `sub` identifica al sujeto y `exp` es la expiración Unix; ambos son obligatorios. El token de dispositivo requiere `tipo=dispositivo`, `scope=lecturas:escribir` y `planta_id`; el de usuario requiere `tipo=usuario`. El emisor JWT del adaptador de salida debe acordar el algoritmo, secreto y claims/valores con este verificador.

Con PyJWT instalado y `MATERA_JWT_SECRET` exportada, genera tokens ficticios de una hora:

```bash
export DEVICE_TOKEN="$(python3 -c 'import os,time,jwt; print(jwt.encode({"sub":"esp32-01","tipo":"dispositivo","scope":"lecturas:escribir","planta_id":"planta-1","exp":int(time.time())+3600}, os.environ["MATERA_JWT_SECRET"], algorithm="HS256"))')"
export USER_TOKEN="$(python3 -c 'import os,time,jwt; print(jwt.encode({"sub":"usuario-1","tipo":"usuario","exp":int(time.time())+3600}, os.environ["MATERA_JWT_SECRET"], algorithm="HS256"))')"
```
## 7. Ejecutar el simulador
Argumentos reales: `--url` (default `http://127.0.0.1:5000`), `--dispositivo` (obligatorio), `--token` (obligatorio), `--especie` (`cactus`, `helecho`, `orquidea`; default `helecho`), `--intervalo` (segundos, default 5; debe ser positivo), `--cantidad` (default 0, infinito), `--semilla`, `--token-malo` y `--token-usuario`.

Probabilidades aproximadas por lectura: 75 % normal, 15 % fuera del rango de la especie pero dentro de límites físicos y 10 % inválida (humedad imposible, tipo texto, campo faltante o fecha incorrecta). El fake aún solo valida el rango físico de humedad. Los rangos del simulador son ejemplos y pueden diferir del CSV.

Desde la raíz, con la API ejecutándose y `DEVICE_TOKEN` disponible:

```bash
python3 Backend/simulador/simulador_esp32.py --dispositivo esp32-01 --token "$DEVICE_TOKEN" --cantidad 1
python3 Backend/simulador/simulador_esp32.py --dispositivo esp32-01 --token "$DEVICE_TOKEN" --intervalo 2 --cantidad 10 --semilla 42 --especie cactus
python3 Backend/simulador/simulador_esp32.py --dispositivo esp32-01 --token "$DEVICE_TOKEN" --token-malo --cantidad 1
python3 Backend/simulador/simulador_esp32.py --dispositivo esp32-01 --token "$DEVICE_TOKEN" --token-usuario "$USER_TOKEN" --cantidad 1
```
`--token-malo` prevalece si se combina con `--token-usuario`.

## 8. Tabla de resultados esperados
Desde la raíz, define `BASE_URL` y, para los ejemplos autenticados, los tokens de la sección anterior. Crea un token expirado así:

```bash
export BASE_URL="http://127.0.0.1:5000"
export EXPIRED_TOKEN="$(python3 -c 'import os,time,jwt; print(jwt.encode({"sub":"esp32-01","tipo":"dispositivo","scope":"lecturas:escribir","planta_id":"planta-1","exp":int(time.time())-60}, os.environ["MATERA_JWT_SECRET"], algorithm="HS256"))')"
```
| Caso | Comando | HTTP | Respuesta esperada |
|---|---|---:|---|
| Lectura normal | `curl -sS -X POST "$BASE_URL/api/dispositivos/esp32-01/lecturas" -H "Authorization: Bearer $DEVICE_TOKEN" -H "Content-Type: application/json" -d '{"marca_tiempo":"2026-10-29T20:00:00Z","humedad":65,"luz":500,"temperatura":20}'` | 201 | `{"planta_id":"planta-1","vitalidad":100.0}` |
| Fuera del rango de especie, físicamente válido | `curl -sS -X POST "$BASE_URL/api/dispositivos/esp32-01/lecturas" -H "Authorization: Bearer $DEVICE_TOKEN" -H "Content-Type: application/json" -d '{"marca_tiempo":"2026-10-29T20:00:00Z","humedad":55,"luz":500,"temperatura":20}'` | 201 | La misma respuesta fija del fake |
| Humedad imposible | `curl -sS -X POST "$BASE_URL/api/dispositivos/esp32-01/lecturas" -H "Authorization: Bearer $DEVICE_TOKEN" -H "Content-Type: application/json" -d '{"marca_tiempo":"2026-10-29T20:00:00Z","humedad":140,"luz":500,"temperatura":20}'` | 400 | `{"error":"La humedad debe estar entre 0 y 100"}` |
| Texto en vez de número | `curl -sS -X POST "$BASE_URL/api/dispositivos/esp32-01/lecturas" -H "Authorization: Bearer $DEVICE_TOKEN" -H "Content-Type: application/json" -d '{"marca_tiempo":"2026-10-29T20:00:00Z","humedad":"mucha","luz":500,"temperatura":20}'` | 400 | Error: `humedad` no es numérico |
| Campo `temperatura` faltante | `curl -sS -X POST "$BASE_URL/api/dispositivos/esp32-01/lecturas" -H "Authorization: Bearer $DEVICE_TOKEN" -H "Content-Type: application/json" -d '{"marca_tiempo":"2026-10-29T20:00:00Z","humedad":65,"luz":500}'` | 400 | Error: falta `temperatura` o no es numérico |
| Fecha mal formada | `curl -sS -X POST "$BASE_URL/api/dispositivos/esp32-01/lecturas" -H "Authorization: Bearer $DEVICE_TOKEN" -H "Content-Type: application/json" -d '{"marca_tiempo":"ayer","humedad":65,"luz":500,"temperatura":20}'` | 400 | `{"error":"'marca_tiempo' no tiene formato ISO 8601"}` |
| Sin token | `curl -sS -X POST "$BASE_URL/api/dispositivos/esp32-01/lecturas" -H "Content-Type: application/json" -d '{}'` | 401 | `{"error":"Falta el token o el formato es incorrecto"}` |
| Token falso | `curl -sS -X POST "$BASE_URL/api/dispositivos/esp32-01/lecturas" -H "Authorization: Bearer esto.no.es.un.jwt" -H "Content-Type: application/json" -d '{}'` | 401 | `{"error":"Token inválido"}` |
| Token expirado | `curl -sS -X POST "$BASE_URL/api/dispositivos/esp32-01/lecturas" -H "Authorization: Bearer $EXPIRED_TOKEN" -H "Content-Type: application/json" -d '{}'` | 401 | `{"error":"El token expiró"}` |
| Dispositivo distinto al del token | `curl -sS -X POST "$BASE_URL/api/dispositivos/otro-id/lecturas" -H "Authorization: Bearer $DEVICE_TOKEN" -H "Content-Type: application/json" -d '{}'` | 403 | `{"error":"El token no corresponde a este dispositivo"}` |
| Token de usuario en ruta de dispositivo | `curl -sS -X POST "$BASE_URL/api/dispositivos/esp32-01/lecturas" -H "Authorization: Bearer $USER_TOKEN" -H "Content-Type: application/json" -d '{}'` | 403 | `{"error":"Este endpoint requiere un token de dispositivo"}` |

## 9. Endpoints disponibles hoy
| Método y ruta | Autenticación | Ejemplo de cuerpo y respuesta |
|---|---|---|
| `GET /health` | Ninguna | Respuesta: `{"estado":"OK","mensaje":"API de Matera Inteligente funcionando"}` |
| `GET /api/v1/especies` | Ninguna | Sin cuerpo. Respuesta incluye `{"nombre":"Orquidea","rangos":{"humedad":{"min":40.0,"max":70.0},"luz":{"min":10000.0,"max":20000.0},"temperatura":{"min":18.0,"max":25.0}}}`; el CSV actual tiene cinco especies. |
| `POST /api/v1/evaluar` | Ninguna | Cuerpo: `{"especie":"Orquidea","humedad":50,"luz":15000,"temperatura":20}`. Respuesta: `{"exito":true,"mensaje":"Evaluacion realizada con exito.","especie":"Orquidea","humedad_medida":50.0,"luz_medida":15000.0,"temperatura_medida":20.0,"estado_humedad":"OPTIMO","estado_luz":"OPTIMO","estado_temperatura":"OPTIMO","porcentaje_vitalidad":100.0,"nivel_vitalidad":"EXCELENTE"}` |
| `POST /api/dispositivos/<id>/lecturas` | JWT de dispositivo | Cuerpo: `{"marca_tiempo":"2026-10-29T20:00:00Z","humedad":65,"luz":500,"temperatura":20}`. Respuesta fake (201): `{"planta_id":"planta-1","vitalidad":100.0}`. |
El adaptador de dispositivos requiere `Authorization: Bearer <token>`. Las rutas de `api_front.py` (`/api/especies`, `/api/evaluar` y `/api/plantas...`) no están conectadas ni disponibles en la aplicación actual.
## 10. Problemas frecuentes
- `ModuleNotFoundError`: activa el entorno virtual e inicia desde `Backend` para resolver los imports locales.
- HTTP 500 al validar un token: `_secreto()` lanza `RuntimeError` (no `KeyError`) si falta `MATERA_JWT_SECRET`; define la variable en la terminal del servidor.
- HTTP 401 con token aparentemente correcto: confirma que el secreto coincide, que el token no expiró y que está firmado con HS256.
- HTTP 403 inesperado: revisa `tipo`, `scope=lecturas:escribir` y que `sub` coincida con el `<id>` de la ruta.
- Mayúsculas en macOS/Linux: las rutas reales de entrada son minúsculas (`Backend/adaptadores/entrada/`); Git también contiene rutas antiguas con mayúsculas (`Backend/Adaptadores/Entrada/`). macOS puede ocultar colisiones que fallan en Linux.
- Conexión rechazada: verifica que Flask esté activo y que el puerto de `--url` coincida.

## 11. Pendientes
- Reemplazar `FakeRegistrarLectura` por el caso de uso y dominio real. Hoy devuelve siempre `planta-1`/vitalidad `100.0` y solo valida humedad de 0–100.
- Acordar con el emisor JWT el secreto, HS256 y los claims/valores `sub`, `tipo`, `scope` y `planta_id`.
- Registrar `crear_blueprint_front` cuando existan sus puertos/casos de uso; sus seis rutas están definidas pero no conectadas.
- Alinear nombres y rangos de especies del simulador (minúsculas, ejemplos) con el CSV (nombres capitalizados y rangos distintos).
- Crear `requirements.txt` y fijar dependencias. `test_domain.py` tiene un fake que no implementa `obtener_todas_las_especies`, método abstracto del repositorio.
