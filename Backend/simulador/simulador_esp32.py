import argparse
import json
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

# Rangos de ejemplo por especie: (humedad, luz, temperatura) como (min, max).
# DEBEN coincidir con la tabla de referencia (CSV/BD) que use el backend.
ESPECIES = {
    "helecho": {"humedad": (60, 80), "luz": (200, 800), "temperatura": (16, 24)},
    "cactus": {"humedad": (10, 30), "luz": (5000, 20000), "temperatura": (20, 35)},
    "orquidea": {"humedad": (50, 70), "luz": (1000, 3000), "temperatura": (18, 28)},
}

# Límites físicos usados para que las lecturas "fuera de rango" sigan siendo válidas
PISOS_TECHOS = {"humedad": (0, 100), "luz": (0, 100000), "temperatura": (-10, 60)}

PROB_NORMAL = 0.75
PROB_FUERA_DE_RANGO = 0.15   # el 10 % restante son lecturas inválidas


def _normal(rango: Tuple[float, float]) -> float:
    minimo, maximo = rango
    margen = (maximo - minimo) * 0.1
    return round(random.uniform(minimo + margen, maximo - margen), 1)


def _fuera_de_rango(variable: str, rango: Tuple[float, float]) -> float:
    minimo, maximo = rango
    piso, techo = PISOS_TECHOS[variable]
    salto = (maximo - minimo) * random.uniform(0.2, 0.5)
    opciones = []
    if minimo - salto >= piso:
        opciones.append(round(minimo - salto, 1))
    if maximo + salto <= techo:
        opciones.append(round(maximo + salto, 1))
    return random.choice(opciones) if opciones else _normal(rango)


def _lectura_base(especie: str) -> Dict[str, object]:
    rangos = ESPECIES[especie]
    return {
        "marca_tiempo": datetime.now(timezone.utc).isoformat(),
        **{variable: _normal(rangos[variable]) for variable in rangos},
    }


def generar_lectura(especie: str) -> Tuple[str, Dict[str, object]]:
    """Devuelve (categoria, cuerpo) según las probabilidades definidas."""
    sorteo = random.random()
    cuerpo = _lectura_base(especie)

    if sorteo < PROB_NORMAL:
        return "normal", cuerpo

    if sorteo < PROB_NORMAL + PROB_FUERA_DE_RANGO:
        variable = random.choice(list(ESPECIES[especie]))
        cuerpo[variable] = _fuera_de_rango(variable, ESPECIES[especie][variable])
        return "fuera_de_rango", cuerpo

    falla = random.choice(["humedad_imposible", "texto", "campo_faltante", "fecha_mala"])
    if falla == "humedad_imposible":
        cuerpo["humedad"] = 140
    elif falla == "texto":
        cuerpo[random.choice(["humedad", "luz", "temperatura"])] = "mucha"
    elif falla == "campo_faltante":
        del cuerpo[random.choice(["humedad", "luz", "temperatura", "marca_tiempo"])]
    else:
        cuerpo["marca_tiempo"] = "ayer por la tarde"
    return "invalida(%s)" % falla, cuerpo


def enviar(url: str, token: str, cuerpo: Dict[str, object]) -> Tuple[Optional[int], str]:
    peticion = urllib.request.Request(
        url,
        data=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=10) as respuesta:
            return respuesta.status, respuesta.read().decode("utf-8")
    except urllib.error.HTTPError as error:       # 4xx / 5xx: la API sí respondió
        return error.code, error.read().decode("utf-8")
    except urllib.error.URLError as error:        # sin conexión
        return None, str(error.reason)


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulador de ESP32 de la matera")
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="URL base del backend")
    parser.add_argument("--dispositivo", required=True, help="id del dispositivo")
    parser.add_argument("--token", required=True, help="token_dispositivo")
    parser.add_argument("--especie", default="helecho", choices=sorted(ESPECIES))
    parser.add_argument("--intervalo", type=float, default=5.0, help="segundos entre lecturas")
    parser.add_argument("--cantidad", type=int, default=0, help="0 = infinito")
    parser.add_argument("--semilla", type=int, help="semilla para repetir la misma secuencia")
    parser.add_argument("--token-malo", action="store_true", help="envía un token falso (401)")
    parser.add_argument("--token-usuario", help="envía este token de usuario en vez del de dispositivo (403)")
    args = parser.parse_args()

    if args.intervalo <= 0:
        parser.error("--intervalo debe ser mayor que 0")
    if args.semilla is not None:
        random.seed(args.semilla)

    token = args.token
    if args.token_usuario:
        token = args.token_usuario
    if args.token_malo:
        token = "esto.no.es.un.jwt"

    endpoint = "%s/api/dispositivos/%s/lecturas" % (args.url.rstrip("/"), args.dispositivo)
    enviadas = 0
    try:
        while args.cantidad == 0 or enviadas < args.cantidad:
            categoria, cuerpo = generar_lectura(args.especie)
            codigo, respuesta = enviar(endpoint, token, cuerpo)
            hora = datetime.now().strftime("%H:%M:%S")
            print("[%s] %-32s -> %s %s" % (hora, categoria, codigo, respuesta.strip()))
            enviadas += 1
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\nSimulador detenido (%d lecturas enviadas)" % enviadas)


if __name__ == "__main__":
    main()