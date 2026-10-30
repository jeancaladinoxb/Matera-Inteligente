# API de Matera Inteligente

Contrato HTTP/JSON entre `matera-backend` y `matera-frontend`. Es el único
acoplamiento entre los dos repositorios: el front no importa código del back.

Base local: `http://127.0.0.1:5000`

- Todos los cuerpos son JSON (`Content-Type: application/json`).
- Los endpoints autenticados esperan `Authorization: Bearer <token>`.
- Los errores siempre tienen la forma `{"error": "mensaje legible"}`.

## Códigos de error

| Código | Cuándo | Excepción del dominio |
|---|---|---|
| 400 | Campo faltante, texto donde va un número, valor fuera de los límites físicos, correo mal formado, contraseña < 8 | `LecturaInvalida`, `ValorFueraDeRangoFisicoError`, `DatosInvalidos` |
| 401 | Token ausente, mal firmado o expirado; credenciales incorrectas | `CredencialesInvalidas` |
| 403 | Planta ajena, dispositivo inactivo, `{id}` distinto del `sub` del token, scope equivocado | `AccesoDenegado`, `DispositivoInactivo` |
| 404 | Especie, planta o dispositivo inexistente; planta todavía sin lecturas | `EspecieNoEncontradaError`, `PlantaNoEncontrada`, `DispositivoNoEncontrado`, `SinLecturas` |
| 409 | Correo ya registrado, dispositivo ya vinculado, dispositivo sin planta | `UsuarioYaExiste`, `DispositivoYaVinculado` |
| 500 | Cualquier otra cosa | — |

La traducción excepción → código la hace el adaptador de entrada. El dominio
no conoce ningún número de estado.

## Objeto `estado`

Lo devuelven `/estado`, `/historial` (como lista), `/evaluar` y la respuesta
de una lectura registrada. La forma es siempre la misma:

```json
{
  "planta_id": "p-001",
  "especie": "Orquidea",
  "dispositivo_id": "d-001",
  "marca_tiempo": "2026-10-30T04:54:10+00:00",
  "lecturas":  { "humedad": 52.0, "luz": 15200.0, "temperatura": 21.4 },
  "estados":   { "humedad": "OPTIMO", "luz": "OPTIMO", "temperatura": "OPTIMO" },
  "vitalidad": { "porcentaje": 100.0, "nivel": "EXCELENTE" }
}
```

- `estados`: `BAJO` | `OPTIMO` | `ALTO`
- `vitalidad.nivel`: `EXCELENTE` | `BUENO` | `REGULAR` | `CRITICO`
- `EXCELENTE` exige que los tres parámetros estén en rango.
- `marca_tiempo`: ISO 8601 con zona horaria (UTC).

---

## `POST /api/auth/registro` · pública

```json
{ "email": "david@matera.co", "password": "claveSegura1" }
```

`201` → `{"usuario_id": "...", "email": "..."}` · `400` datos inválidos · `409` correo repetido

## `POST /api/auth/login` · pública

```json
{ "email": "david@matera.co", "password": "claveSegura1" }
```

`200` → `{"token": "<jwt de usuario>"}` · `401` credenciales

## `GET /api/especies` · JWT usuario

`200` →

```json
[
  {
    "nombre": "Orquidea",
    "rangos": {
      "humedad": { "min": 40.0, "max": 70.0 },
      "luz": { "min": 10000.0, "max": 20000.0 },
      "temperatura": { "min": 18.0, "max": 25.0 }
    }
  }
]
```

Ordenado alfabéticamente.

## `POST /api/evaluar` · JWT usuario · R1

La validación de la fase 1. No guarda nada.

```json
{ "especie": "Orquidea", "humedad": 50.0, "luz": 15000.0, "temperatura": 20.0 }
```

`200` → objeto `estado` **sin** `planta_id`, `nombre`, `dispositivo_id` ni
`marca_tiempo` (no hay planta ni dispositivo):

```json
{
  "especie": "Orquidea",
  "lecturas":  { "humedad": 50.0, "luz": 15000.0, "temperatura": 20.0 },
  "estados":   { "humedad": "OPTIMO", "luz": "OPTIMO", "temperatura": "OPTIMO" },
  "vitalidad": { "porcentaje": 100.0, "nivel": "EXCELENTE" }
}
```

`400` valor imposible · `404` especie desconocida

## `POST /api/plantas` · JWT usuario

Vincula un dispositivo por su código de emparejamiento y crea la planta.

```json
{ "nombre": "Orquídea de la sala", "especie": "Orquidea", "codigo": "ABC123" }
```

`201` →

```json
{
  "planta_id": "p-001",
  "dispositivo_id": "d-001",
  "token_dispositivo": "<jwt de dispositivo>"
}
```

El `token_dispositivo` se entrega **una sola vez**: es el que recibe el
simulador en `--token`.

`400` campos vacíos · `404` código o especie inexistente · `409` ya vinculado

## `GET /api/plantas` · JWT usuario

`200` → solo las plantas del usuario del token:

```json
[
  {
    "planta_id": "p-001",
    "nombre": "Orquídea de la sala",
    "especie": "Orquidea"
  }
]
```

## `GET /api/plantas/{id}/estado` · JWT usuario

`200` → objeto `estado` · `403` planta ajena · `404` planta inexistente o sin
lecturas todavía

El front lo consulta cada 5 s (R6).

## `GET /api/plantas/{id}/historial?limite=20` · JWT usuario

`200` → lista de lecturas evaluadas, de la más reciente a la más antigua.
`limite` por defecto 20, máximo 200.

```json
[
  {
    "marca_tiempo": "2026-10-29T21:30:00+00:00",
    "lecturas":  { "humedad": 52.0, "luz": 15200.0, "temperatura": 21.4 },
    "estados":   { "humedad": "OPTIMO", "luz": "OPTIMO", "temperatura": "OPTIMO" },
    "vitalidad": { "porcentaje": 100.0, "nivel": "EXCELENTE" }
  }
]
```

Sin `planta_id`, `nombre` ni `especie`: son los mismos en todas las filas y el
cliente ya los tiene. En el dominio esto corresponde a `LecturaEvaluada`.

`403` planta ajena · `404` planta inexistente

## `POST /api/dispositivos/{id}/lecturas` · JWT dispositivo · R2

El único endpoint que usa el token de dispositivo. Lo llama el ESP32 (o el
simulador), nunca el front.

```json
{
  "marca_tiempo": "2026-10-29T21:30:00Z",
  "humedad": 52.0,
  "luz": 15200.0,
  "temperatura": 21.4
}
```

`201` si se guardó, `200` si era un reenvío de una lectura ya registrada:

```json
{
  "planta_id": "p-001",
  "marca_tiempo": "2026-10-30T04:54:10+00:00",
  "guardada": true,
  "vitalidad": { "porcentaje": 100.0, "nivel": "EXCELENTE" }
}
```

- `400` lectura inválida (campo faltante, texto, humedad 140, marca de tiempo mal formada)
- `401` token ausente o mal firmado
- `403` `{id}` distinto del `sub` del token, token de usuario en vez de dispositivo, o dispositivo inactivo
- `409` el dispositivo no está vinculado a ninguna planta

La lectura **no trae la especie**: el dominio la resuelve desde la planta. Si
se repite la misma `marca_tiempo` del mismo dispositivo, la respuesta es la
misma y no se duplica el registro.

---

## Tokens

| | Usuario | Dispositivo |
|---|---|---|
| `sub` | `usuario_id` | `dispositivo_id` |
| `tipo` | `"usuario"` | `"dispositivo"` |
| extra | — | `planta_id`, `scope: "lecturas:escribir"` |
| `exp` | 60 min | 365 días; se revoca con `activo = False` |
| se emite en | caso de uso de login | caso de uso de vinculación |
| se verifica en | `usuario_requerido` en `seguridad.py` | `dispositivo_requerido` en `seguridad.py` |

Los dos tokens llevan `exp`: el decodificador lo exige.

Un token de usuario no sirve en el endpoint del dispositivo y viceversa: el
scope es distinto y el decorador responde 403.

## CORS

El back debe permitir el origen del front (`MATERA_CORS_ORIGINS`, por ejemplo
`http://localhost:5500`) y la cabecera `Authorization`.
