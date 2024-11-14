import sqlite3

# Conectar a la base de datos
conexion = sqlite3.connect('roadadvisor.db')
cursor = conexion.cursor()

# Consultar todos los datos de la tabla usuarios
cursor.execute("SELECT * FROM soporte")
soportes = cursor.fetchall()

# Imprimir los resultados
print("Solicitudes en la tabla soportes:")
for soporte in soportes:
    print(soporte)
    
# Consultar todos los datos de la tabla usuarios
cursor.execute("SELECT * FROM alertas")
alertas = cursor.fetchall()

# Imprimir los resultados
print("Alertas en la tabla alertas:")
for alerta in alertas:
    print(alerta)
    
# Consultar todos los datos de la tabla usuarios
cursor.execute("SELECT * FROM vehiculos")
vehiculos = cursor.fetchall()

# Imprimir los resultados
print("Vehiculos en la tabla vehiculos:")
for vehiculo in vehiculos:
    print(vehiculo)

# Consultar todos los datos de la tabla usuarios
cursor.execute("SELECT * FROM usuarios")
usuarios = cursor.fetchall()

# Imprimir los resultados
print("Usuarios en la tabla usuarios:")
for usuario in usuarios:
    print(usuario)

# Consultar todos los datos de la tabla usuarios
cursor.execute("SELECT * FROM sensores")
sensores = cursor.fetchall()

# Imprimir los resultados
print("Telemetría en la tabla sensores:")
for sensor in sensores:
    print(sensor)

# Cerrar la conexión
conexion.close()

