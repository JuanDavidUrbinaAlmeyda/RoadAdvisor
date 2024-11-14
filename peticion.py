import requests

# Función para realizar la solicitud y extraer el valor de cada sensor
def obtener_valor_sensor(url, headers):
    response = requests.get(url, headers=headers)
    data = response.json()
    return data['value']

# Configuración del encabezado de autorización
headers = {
    'Authorization': 'SharedAccessSignature sr=cc242e64-705e-4325-80f9-71c5dff336b3&sig=bUQVFq9D55OsfvjL7t2t1OwqCqw%2FuXKB5aU1y6tx8%2FU%3D&skn=apitokenroadadvisor&se=1760737527135'
}

# URLs para cada sensor y vehículo
urls_por_vehiculo = {
    "vehiculo_1": {
        "gasolina": "https://roadadvisor.azureiotcentral.com/api/devices/h7r48b42yq/components/vehiculo_23h/telemetry/Gasolina?api-version=2022-07-31",
        "aceite": "https://roadadvisor.azureiotcentral.com/api/devices/h7r48b42yq/components/vehiculo_23h/telemetry/Aceite?api-version=2022-07-31",
        "presion": "https://roadadvisor.azureiotcentral.com/api/devices/h7r48b42yq/components/vehiculo_23h/telemetry/PresionLlantas?api-version=2022-07-31",
        "ubicacion": "https://roadadvisor.azureiotcentral.com/api/devices/h7r48b42yq/components/vehiculo_23h/telemetry/Ubicacion?api-version=2022-07-31",
        "velocidad": "https://roadadvisor.azureiotcentral.com/api/devices/h7r48b42yq/components/vehiculo_23h/telemetry/Velocidad?api-version=2022-07-31",

    },
    "vehiculo_2": {
        "gasolina": "https://roadadvisor.azureiotcentral.com/api/devices/1tmzcuqbcjy/components/vehiculo_23h/telemetry/Gasolina?api-version=2022-07-31",
        "aceite": "https://roadadvisor.azureiotcentral.com/api/devices/1tmzcuqbcjy/components/vehiculo_23h/telemetry/Aceite?api-version=2022-07-31",
        "presion": "https://roadadvisor.azureiotcentral.com/api/devices/1tmzcuqbcjy/components/vehiculo_23h/telemetry/PresionLlantas?api-version=2022-07-31",
        "ubicacion": "https://roadadvisor.azureiotcentral.com/api/devices/1tmzcuqbcjy/components/vehiculo_23h/telemetry/Ubicacion?api-version=2022-07-31",
        "velocidad": "https://roadadvisor.azureiotcentral.com/api/devices/1tmzcuqbcjy/components/vehiculo_23h/telemetry/Velocidad?api-version=2022-07-31",

    },
    "vehiculo_3": {
        "gasolina": "https://roadadvisor.azureiotcentral.com/api/devices/aljwou1sow/components/vehiculo_23h/telemetry/Gasolina?api-version=2022-07-31",
        "aceite": "https://roadadvisor.azureiotcentral.com/api/devices/aljwou1sow/components/vehiculo_23h/telemetry/Aceite?api-version=2022-07-31",
        "presion": "https://roadadvisor.azureiotcentral.com/api/devices/aljwou1sow/components/vehiculo_23h/telemetry/PresionLlantas?api-version=2022-07-31",
        "ubicacion": "https://roadadvisor.azureiotcentral.com/api/devices/aljwou1sow/components/vehiculo_23h/telemetry/Ubicacion?api-version=2022-07-31",
        "velocidad": "https://roadadvisor.azureiotcentral.com/api/devices/h7r48b42yq/components/vehiculo_23h/telemetry/Velocidad?api-version=2022-07-31",

    }
}

# URLs adicionales para estado de vía y accidente
url_estado_via = "https://roadadvisor.azureiotcentral.com/api/devices/bj4fhh0hrx/components/dron_2by/telemetry/estado?api-version=2022-07-31"
url_accidente = "https://roadadvisor.azureiotcentral.com/api/devices/bj4fhh0hrx/components/dron_2by/telemetry/accidente?api-version=2022-07-31"

# Diccionario para almacenar los valores de cada vehículo
valores_sensores_por_vehiculo = {}

# Obtener los valores de cada sensor por vehículo
for vehiculo, sensores in urls_por_vehiculo.items():
    valores_sensores_por_vehiculo[vehiculo] = {}
    for sensor, url in sensores.items():
        valor = obtener_valor_sensor(url, headers)
        valores_sensores_por_vehiculo[vehiculo][sensor] = valor

# Obtener los valores de estado de vía y accidente
estado_via = obtener_valor_sensor(url_estado_via, headers)
accidente = obtener_valor_sensor(url_accidente, headers)

# Mostrar los resultados
for vehiculo, sensores in valores_sensores_por_vehiculo.items():
    print(f"--- {vehiculo.upper()} ---")
    for sensor, valor in sensores.items():
        print(f"{sensor.capitalize()}: {valor}")
print("\nEstado de Vía:", estado_via)
print("Accidente:", accidente)
