import sqlite3

# Conexión a la base de datos
conexion = sqlite3.connect('roadadvisor.db')
cursor = conexion.cursor()

# Borrar las tablas si ya existen
cursor.execute("DROP TABLE IF EXISTS usuarios")
cursor.execute("DROP TABLE IF EXISTS pagos")
cursor.execute("DROP TABLE IF EXISTS rutas")
cursor.execute("DROP TABLE IF EXISTS sensores")
cursor.execute("DROP TABLE IF EXISTS alertas")
cursor.execute("DROP TABLE IF EXISTS vehiculos")
cursor.execute("DROP TABLE IF EXISTS soporte")

# Tabla de usuarios
cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        rol TEXT NOT NULL,
        correo TEXT NOT NULL,
        contraseña TEXT NOT NULL,
        img_usr TEXT  -- Campo para la URL de la imagen del perfil del usuario
    )
''')

# Tabla de pagos
cursor.execute('''
    CREATE TABLE IF NOT EXISTS pagos (
        id_pago INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        cantidad REAL NOT NULL
    )
''')

# Tabla de rutas
cursor.execute('''
    CREATE TABLE IF NOT EXISTS rutas (
        id_ruta INTEGER PRIMARY KEY AUTOINCREMENT,
        accidente BOOLEAN NOT NULL,
        estado TEXT NOT NULL
    )
''')

# Tabla de sensores
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sensores (
        id_sensor INTEGER PRIMARY KEY AUTOINCREMENT,
        aceite REAL NOT NULL,
        gasolina REAL NOT NULL,
        presion REAL NOT NULL,
        ubicacion TEXT NOT NULL,  -- Guardamos las coordenadas como texto
        velocidad REAL NOT NULL,
        id_veh INTEGER,
        FOREIGN KEY (id_veh) REFERENCES vehiculos(id_veh)
    )
''')

# Tabla de alertas con relación a id_veh
cursor.execute('''
    CREATE TABLE IF NOT EXISTS alertas (
        id_alerta INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        id_veh INTEGER,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_veh) REFERENCES vehiculos(id_veh)
    )
''')

# Tabla de vehiculos
cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehiculos (
        id_veh INTEGER PRIMARY KEY AUTOINCREMENT,
        placa TEXT NOT NULL,
        modelo TEXT NOT NULL,
        color TEXT NOT NULL,
        id_conductor INTEGER,
        id_admin INTEGER,
        img_veh TEXT,  -- Campo para la URL de la imagen del vehículo
        FOREIGN KEY (id_conductor) REFERENCES usuarios(id_usuario),
        FOREIGN KEY (id_admin) REFERENCES usuarios(id_usuario)
    )
''')

# Tabla de soporte
cursor.execute('''
    CREATE TABLE IF NOT EXISTS soporte (
        id_solicitud INTEGER PRIMARY KEY AUTOINCREMENT,
        motivo TEXT NOT NULL,
        descripcion TEXT NOT NULL
    )
''')

# Confirmar la creación de tablas
conexion.commit()

# Verificar la lista de tablas creadas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tablas en la base de datos:", cursor.fetchall())

# Cerrar la conexión
conexion.close()

