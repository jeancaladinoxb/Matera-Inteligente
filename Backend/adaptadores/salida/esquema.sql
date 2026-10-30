CREATE TABLE IF NOT EXISTS usuarios     (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS plantas      (id TEXT PRIMARY KEY, usuario_id TEXT NOT NULL REFERENCES usuarios(id), nombre TEXT NOT NULL, especie TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS dispositivos (id TEXT PRIMARY KEY, codigo_emparejamiento TEXT UNIQUE NOT NULL, planta_id TEXT REFERENCES plantas(id), activo INTEGER NOT NULL DEFAULT 1);
-- especie se guarda en cada lectura para reconstruir EvaluacionMatera.nombre_especie al leer el historial
CREATE TABLE IF NOT EXISTS lecturas     (id INTEGER PRIMARY KEY AUTOINCREMENT, planta_id TEXT NOT NULL REFERENCES plantas(id), dispositivo_id TEXT NOT NULL,
                           marca_tiempo TEXT NOT NULL, especie TEXT NOT NULL, humedad REAL, luz REAL, temperatura REAL,
                           estado_humedad TEXT, estado_luz TEXT, estado_temperatura TEXT, vitalidad REAL, nivel TEXT,
                           UNIQUE (dispositivo_id, marca_tiempo));
CREATE TABLE IF NOT EXISTS especies     (nombre TEXT PRIMARY KEY, humedad_min REAL, humedad_max REAL, luz_min REAL, luz_max REAL, temp_min REAL, temp_max REAL, fuente TEXT);
