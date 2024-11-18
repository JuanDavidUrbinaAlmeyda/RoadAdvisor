import streamlit as st
import sqlite3
import pydeck as pdk
from PIL import Image
from sensores.peticion import obtener_valor_sensor, urls_por_vehiculo,url_accidente,url_estado_via, headers  # Importamos la función y URLs
from alertas.email_alert import enviar_alerta_correo
from pagos.payments import crear_pago_paypal  # Importa tu función de pagos
import matplotlib.pyplot as plt



# Configuración de la página
st.set_page_config(page_title="RoadAdvisor", layout="wide")

# Conexión a la base de datos SQLite
def obtener_conexion():
    return sqlite3.connect('roadadvisor.db')

# Función para registrar un nuevo usuario en la base de datos
def registrar_usuario(nombre, correo, password, rol="admin"):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            INSERT INTO usuarios (nombre, correo, contraseña, rol)
            VALUES (?, ?, ?, ?)
        ''', (nombre, correo, password, rol))
        conexion.commit()
        st.success("Registro exitoso.")
    except sqlite3.IntegrityError:
        st.error("El correo ya está registrado. Usa uno diferente.")
    finally:
        conexion.close()

# Función para autenticar un usuario en la base de datos
def autenticar_usuario(correo, password):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT id_usuario, rol FROM usuarios WHERE correo = ? AND contraseña = ?
    ''', (correo, password))
    resultado = cursor.fetchone()
    conexion.close()
    return (True, resultado[0], resultado[1]) if resultado else (False, None, None)

# Función para obtener datos de usuario
def obtener_datos_usuario(id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre, rol, correo FROM usuarios WHERE id_usuario = ?", (id_usuario,))
    usuario = cursor.fetchone()
    conexion.close()
    return usuario

# Función para contar vehículos de un administrador (sin límite si es admin_premium)
def contar_vehiculos(id_admin, rol):
    if rol == "admin_premium":
        return None  # No hay límite para admin_premium

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM vehiculos WHERE id_admin = ?", (id_admin,))
    cantidad_vehiculos = cursor.fetchone()[0]
    conexion.close()
    return cantidad_vehiculos


# Función para obtener lista de conductores
def obtener_conductores():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_usuario, nombre FROM usuarios WHERE rol = 'conductor'")
    conductores = cursor.fetchall()
    conexion.close()
    return conductores

# Función para obtener lista de dueños
def obtener_duenos():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_usuario, nombre FROM usuarios WHERE rol IN ('admin', 'admin_premium')")
    duenos = cursor.fetchall()
    conexion.close()
    return duenos

# Función para registrar vehículo
def registrar_vehiculo(placa, modelo, color, id_conductor, id_admin, img_veh_url):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            INSERT INTO vehiculos (placa, modelo, color, id_conductor, id_admin, img_veh)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (placa, modelo, color, id_conductor, id_admin, img_veh_url))
        conexion.commit()
        id_vehiculo = cursor.lastrowid  # Obtener el ID del último vehículo insertado
        return id_vehiculo
    except sqlite3.IntegrityError:
        return None
    finally:
        conexion.close()

# Función para obtener vehículos del usuario
def obtener_vehiculos_usuario(id_usuario, rol):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    if rol in ["admin", "admin_premium"]:
        cursor.execute("SELECT id_veh, placa, modelo, color, img_veh FROM vehiculos WHERE id_admin = ?", (id_usuario,))
    elif rol == "conductor":
        cursor.execute("SELECT id_veh, placa, modelo, color, img_veh FROM vehiculos WHERE id_conductor = ?", (id_usuario,))
    vehiculos = cursor.fetchall()
    conexion.close()
    return vehiculos

# Función para obtener datos del vehículo
def obtener_datos_vehiculo(id_veh):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT id_veh, placa, modelo, color, id_conductor FROM vehiculos WHERE id_veh = ?
    ''', (id_veh,))
    vehiculo = cursor.fetchone()
    conexion.close()
    return vehiculo

# Función para obtener datos del conductor
def obtener_datos_conductor(id_conductor):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre, correo FROM usuarios WHERE id_usuario = ?", (id_conductor,))
    conductor = cursor.fetchone()
    conexion.close()
    return conductor

# Función para la pantalla Crear Vehículo
def crear_vehiculo_page():
    st.title("Crear Vehículo")
    placa = st.text_input("Placa", max_chars=6)
    modelo = st.text_input("Modelo", max_chars=30)
    color = st.text_input("Color", max_chars=30)
    img_veh_url = st.text_input("URL de la Imagen del Vehículo")  # Nuevo campo para la URL de la imagen

    # Obtener y mostrar la lista de conductores y dueños
    conductores = obtener_conductores()
    conductor_options = {nombre: id_usuario for id_usuario, nombre in conductores}
    conductor_seleccionado = st.selectbox("Seleccione un Conductor", list(conductor_options.keys()))
    duenos = obtener_duenos()
    dueno_options = {nombre: id_usuario for id_usuario, nombre in duenos}
    dueno_seleccionado = st.selectbox("Seleccione un Dueño", list(dueno_options.keys()))
    id_admin = dueno_options[dueno_seleccionado]

    # Comprobación del límite de vehículos para el administrador
    cantidad_vehiculos = contar_vehiculos(id_admin, st.session_state.rol)  # Pasamos id_admin y rol
    if st.session_state.rol == "admin" and cantidad_vehiculos is not None and cantidad_vehiculos >= 3:
        st.error("Cada administrador solo puede crear hasta 3 vehículos.")
    else:
        # Botón para registrar el vehículo
        if st.button("Registrar Vehículo"):
            if not placa or not modelo or not color or not img_veh_url:
                st.warning("Completa todos los campos para registrar el vehículo.")
            else:
                # Obtener el id_conductor seleccionado
                id_conductor = conductor_options[conductor_seleccionado]
                
                # Registrar el vehículo con la URL de la imagen
                id_vehiculo = registrar_vehiculo(placa, modelo, color, id_conductor, id_admin, img_veh_url)
                
                if id_vehiculo:
                    # Guardar el id_vehiculo en el estado de sesión para redirigir al dashboard
                    st.session_state.vehiculo_seleccionado = id_vehiculo
                    st.success("Vehículo registrado exitosamente.")
                else:
                    st.error("Error al registrar el vehículo.")


# Función para la pantalla Crear Conductor
def crear_conductor_page():
    st.title("Crear Conductor")
    nombre = st.text_input("Nombre Completo", key="conductor_nombre", max_chars=30)
    correo = st.text_input("Correo Electrónico", key="conductor_correo", max_chars=30)
    password = st.text_input("Contraseña", type="password", key="conductor_password")
    if st.button("Registrar Conductor"):
        if not nombre or not correo or not password:
            st.warning("Por favor, completa todos los campos para registrar al conductor.")
        else:
            registrar_usuario(nombre, correo, password, rol="conductor")
            st.success("Conductor registrado exitosamente.")

# Función para la pantalla principal (Home)
def home_page():
    st.title("Bienvenido a RoadAdvisor")
    st.subheader("Tus Vehículos")
    vehiculos = obtener_vehiculos_usuario(st.session_state.id_usuario, st.session_state.rol)
    
    # Dividir los vehículos en grupos de 3 para mantener uniformidad en las filas
    num_vehiculos_por_fila = 3
    for i in range(0, len(vehiculos), num_vehiculos_por_fila):
        cols = st.columns(num_vehiculos_por_fila)
        for idx, vehiculo in enumerate(vehiculos[i:i + num_vehiculos_por_fila]):
            id_veh, placa, modelo, color, img_veh_url = vehiculo  # Modificada para obtener img_veh_url
            with cols[idx]:  # Colocar en la columna correspondiente
                # Mostrar la imagen del vehículo si la URL es válida
                if img_veh_url:
                    st.image(img_veh_url, width=250, caption=placa)
                else:
                    st.write("Imagen no disponible")
                st.write(f"**Placa:** {placa}")
                st.write(f"**Modelo:** {modelo}")
                st.write(f"**Color:** {color}")
                if st.button("Ver", key=f"ver_{placa}"):
                    st.session_state.vehiculo_seleccionado = id_veh
                    st.session_state.nav_option = "Dashboard Vehículo"


    # Sección "Acerca De"
    st.markdown("<h1 style='text-align: left;'>Acerca De</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: left;'>En RoadAdvisor, nos enfocamos en ofrecer un servicio de alta calidad con tres pilares fundamentales:</p>", unsafe_allow_html=True)

    # Tres columnas para los valores de la empresa
    col1, col2, col3 = st.columns(3)

    # Ajuste para cada columna
    with col1:
        st.image(
            "https://cdn.autobild.es/sites/navi.axelspringer.es/public/media/image/2018/10/cuatro-formas-mejorar-seguridad-coche.jpg?tf=3840x", 
            width=250
        )
        st.subheader("Seguridad")
        st.write("Nuestra prioridad es tu seguridad. Ofrecemos monitoreo constante y alertas automáticas para mantenerte informado sobre cualquier anomalía en el estado de tus vehículos.")

    with col2:
        st.image(
            "https://www.eucapacito.com.br/wp-content/uploads/2021/12/vantagens-de-usar-data-science-scaled-1.jpeg", 
            width=250
        )
        st.subheader("Actualización")
        st.write("Los datos de nuestros sensores se actualizan en tiempo real, permitiéndote tomar decisiones rápidas y precisas para gestionar tu flota de manera efectiva.")

    with col3:
        st.image(
            "https://blog-cdn.kitalulus.com/blog/wp-content/uploads/2024/02/20100132/628a6a9328633db5f32331fd_Desainer-UI-UX-adalah.jpg", 
            width=250
        )
        st.subheader("Intuitividad")
        st.write("Hemos diseñado una plataforma fácil de usar e intuitiva, para que puedas acceder a la información que necesitas sin complicaciones.")

# Función para la pantalla de soporte
def soporte_page():
    st.title("Contáctanos")
    st.write("Si tienes alguna pregunta o necesitas ayuda, completa el formulario a continuación y te contactaremos.")

    motivo = st.text_input("Motivo", max_chars=30)
    mensaje_soporte = st.text_area("Solicitud de Soporte", height=150, max_chars=200)

    if st.button("Enviar"):
        if motivo and mensaje_soporte:
            # Guardar la solicitud en la base de datos
            conexion = obtener_conexion()
            cursor = conexion.cursor()
            try:
                cursor.execute('''
                    INSERT INTO soporte (motivo, descripcion)
                    VALUES (?, ?)
                ''', (motivo, mensaje_soporte))
                conexion.commit()
                st.success("Tu solicitud de soporte ha sido enviada y registrada. Nos pondremos en contacto contigo pronto.")
            except Exception as e:
                st.error(f"Error al registrar la solicitud de soporte: {e}")
            finally:
                conexion.close()
        else:
            st.error("Por favor, completa todos los campos antes de enviar tu solicitud.")
            
# Función para la pantalla de Planes
def planes_page():
    st.markdown("<h1 style='text-align: center;'>Planes</h1>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    # Definir estilos comunes
    card_style = """
        <div style='border: 2px solid #ccc; border-radius: 10px; padding: 15px; margin: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); height: 300px; display: flex; flex-direction: column; justify-content: space-between;'>
            <h2 style='text-align: center;'>Plan {}</h2>
            <p style='text-align: center;'>
                <ul style='list-style-position: inside; padding-left: 0;'>
                    {}
                </ul>
            </p>
            <p style='text-align: center; color: {}; font-size: 20px; font-weight: bold;'>{}</p>
        </div>
    """

    with col1:
        caracteristicas_gratuito = "<li>Máximo 3 vehículos por administrador</li><li>Monitoreo limitado</li>"
        st.markdown(
            card_style.format(
                "Gratuito",
                caracteristicas_gratuito,
                "#32CD32",  # Color verde
                "Gratis"
            ),
            unsafe_allow_html=True
        )

    with col2:
        caracteristicas_premium = "<li>Número ilimitado de vehículos</li><li>Monitoreo completo</li><li>Futuras mejoras y actualizaciones</li>"
        st.markdown(
            card_style.format(
                "Premium",
                caracteristicas_premium,
                "#DAA520",  # Color dorado
                "30$"
            ),
            unsafe_allow_html=True
        )

    # Centrar el botón debajo de las columnas
    st.markdown("<div style='text-align: center; margin-top: 20px;'>", unsafe_allow_html=True)
    if st.button("Pagar"):
        st.session_state.nav_option = "Pasarela"  # Cambiar la opción de navegación al presionar "Pagar"
    st.markdown("</div>", unsafe_allow_html=True)
    
#Alertas
def alertas_page():
    st.title("Alertas del Sistema")
    
    # Obtener el ID del usuario y su rol desde el estado de sesión
    id_usuario = st.session_state.id_usuario
    rol_usuario = st.session_state.rol

    # Conectar a la base de datos para obtener las alertas correspondientes
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        # Consulta para obtener las alertas de los vehículos asociados al usuario actual
        if rol_usuario in ["admin", "admin_premium"]:
            # Si es admin o admin_premium, mostrar alertas de vehículos que administra
            cursor.execute('''
                SELECT alertas.id_veh, alertas.nombre, alertas.descripcion, alertas.fecha_creacion 
                FROM alertas
                INNER JOIN vehiculos ON alertas.id_veh = vehiculos.id_veh
                WHERE vehiculos.id_admin = ?
            ''', (id_usuario,))
        elif rol_usuario == "conductor":
            # Si es conductor, mostrar alertas de vehículos que conduce
            cursor.execute('''
                SELECT alertas.id_veh, alertas.nombre, alertas.descripcion, alertas.fecha_creacion 
                FROM alertas
                INNER JOIN vehiculos ON alertas.id_veh = vehiculos.id_veh
                WHERE vehiculos.id_conductor = ?
            ''', (id_usuario,))
        else:
            # Si no hay rol definido o es otro tipo de usuario, no mostrar alertas
            alertas = []
        
        # Obtener las alertas
        alertas = cursor.fetchall()
        
        # Mostrar las alertas si hay alguna
        if alertas:
            for alerta in alertas:
                id_veh, nombre, descripcion, fecha_creacion = alerta
                st.markdown(f"""
                    <div style='border: 1px solid #ccc; border-radius: 10px; padding: 10px; margin: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);'>
                        <h4 style='margin: 0;'>Alerta: {nombre}</h4>
                        <p><strong>Descripción:</strong> {descripcion}</p>
                        <p><strong>ID Vehículo:</strong> {id_veh}</p>
                        <p><strong>Fecha y Hora:</strong> {fecha_creacion}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No se encontraron alertas para los vehículos asociados.")
    except Exception as e:
        st.error(f"Error al obtener las alertas: {e}")
    finally:
        conexion.close()


def pasarela_page():
    st.title("Formulario de Pago")
    
    # División del formulario en dos columnas
    col1, col2 = st.columns(2)

    with col1:
        nombre_titular = st.text_input("Nombre del Titular de la Tarjeta", max_chars=30)
        tipo_persona = st.selectbox("Tipo de Persona", ["Natural", "Jurídica"])
        banco = st.selectbox("Banco", ["Bancolombia", "Banco de Bogotá", "Nequi", "Davivienda", "Nu", "Lulo", "BBVA"])
    
    with col2:
        numero_tarjeta = st.text_input("Número de Tarjeta", max_chars=20)
        cvc = st.text_input("CVC", type="password", max_chars=3)
        fecha_vencimiento = st.date_input("Fecha de Vencimiento")
    
    # Mostrar el valor final
    st.markdown("<h3 style='text-align: center;'>Valor Final: 30 $</h3>", unsafe_allow_html=True)
    
    # Botón para finalizar el pago
    if st.button("Finalizar Pago"):
        # Verificar que todos los campos estén llenos
        if not nombre_titular or not numero_tarjeta or not cvc or not fecha_vencimiento:
            st.warning("Por favor, complete todos los campos antes de finalizar el pago.")
        else:
            url_pago = crear_pago_paypal()  # Llamar a la función de pago
            if url_pago:
                st.session_state.approval_url = url_pago  # Guardar el enlace de aprobación en el estado de sesión
                st.session_state.nav_option = "Pago Realizado"  # Cambiar la opción de navegación a "Pago Realizado"
            else:
                st.error("Hubo un error al crear el pago.")
                
def pago_realizado_page():
    st.title("Pago Realizado")
    st.success("Pago creado con éxito.")
    
    # Mostrar el enlace de aprobación si está disponible en el estado de sesión
    if 'approval_url' in st.session_state and st.session_state.approval_url:
        st.markdown(f"[Haz clic aquí para aprobar el pago]({st.session_state.approval_url})")
    
    # Habilitar la creación de más vehículos para el administrador en sesión
    if st.session_state.rol == "admin":
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        try:
            cursor.execute('''
                UPDATE usuarios
                SET rol = 'admin_premium'
                WHERE id_usuario = ?
            ''', (st.session_state.id_usuario,))
            conexion.commit()
            st.info("Se ha habilitado la creación de un número ilimitado de vehículos para este administrador.")
        except Exception as e:
            st.error(f"Error al actualizar el rol del usuario: {e}")
        finally:
            conexion.close()

# Función para obtener la URL de la imagen de usuario
def obtener_imagen_usuario(id_usuario):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT img_usr FROM usuarios WHERE id_usuario = ?", (id_usuario,))
    resultado = cursor.fetchone()
    conexion.close()
    return resultado[0] if resultado else None

# Función para actualizar la imagen del usuario en la base de datos
def actualizar_imagen_usuario(id_usuario, nueva_url_img):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            UPDATE usuarios
            SET img_usr = ?
            WHERE id_usuario = ?
        ''', (nueva_url_img, id_usuario))
        conexion.commit()
    except Exception as e:
        st.error(f"Error al actualizar la imagen de perfil: {e}")
    finally:
        conexion.close()

def guardar_datos_sensores(id_veh, aceite, gasolina, presion, ubicacion, velocidad):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            INSERT INTO sensores (aceite, gasolina, presion, ubicacion, velocidad, id_veh)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (aceite, gasolina, presion, ubicacion, velocidad, id_veh))
        conexion.commit()
    except Exception as e:
        st.error(f"Error al guardar datos de sensores: {e}")
    finally:
        conexion.close()


#DATOS PARA GRÁFICAS
#VELOCIDAD
def obtener_ultimas_medidas_velocidad(id_veh, limite=5):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT velocidad FROM sensores
        WHERE id_veh = ?
        ORDER BY id_sensor DESC
        LIMIT ?
    ''', (id_veh, limite))
    resultados = cursor.fetchall()
    conexion.close()
    # Convertir resultados a una lista de velocidades
    return [fila[0] for fila in resultados]

def obtener_ultimas_medidas_gasolina(id_veh):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT gasolina FROM sensores
        WHERE id_veh = ?
        ORDER BY id_sensor DESC
        LIMIT 5
    ''', (id_veh,))
    resultados = cursor.fetchall()
    conexion.close()
    return [fila[0] for fila in resultados]

def obtener_ultimas_medidas_presion(id_veh):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT presion FROM sensores
        WHERE id_veh = ?
        ORDER BY id_sensor DESC
        LIMIT 5
    ''', (id_veh,))
    resultados = cursor.fetchall()
    conexion.close()
    return [fila[0] for fila in resultados]

def obtener_ultimas_medidas_aceite(id_veh):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT aceite FROM sensores
        WHERE id_veh = ?
        ORDER BY id_sensor DESC
        LIMIT 5
    ''', (id_veh,))
    resultados = cursor.fetchall()
    conexion.close()
    return [fila[0] for fila in resultados]



def mostrar_grafica_velocidad(id_veh):
    # Obtener las últimas 5 medidas de velocidad asociadas al vehículo
    velocidades = obtener_ultimas_medidas_velocidad(id_veh)
    
    # Imprimir las velocidades para depuración
    st.write(f"Velocidades obtenidas: {velocidades}")
    
    if velocidades:
        # Crear un gráfico de línea con las medidas de velocidad
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(range(1, len(velocidades) + 1), velocidades, marker='o', linestyle='-', color='b')
        ax.set_xlabel('Medida')
        ax.set_ylabel('Velocidad')
        ax.set_title('Últimas medidas de velocidad')
        ax.grid(True)
        ax.set_xticks(range(1, len(velocidades) + 1))
        st.pyplot(fig)  # Usar st.pyplot() para mostrar la figura en Streamlit
    else:
        st.write("No hay medidas de velocidad disponibles para este vehículo.")      
 
def mostrar_grafica_gasolina(id_veh):
    gasolinas = obtener_ultimas_medidas_gasolina(id_veh)
    st.write(f"Gasolina obtenida: {gasolinas}")
    
    if gasolinas:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(range(1, len(gasolinas) + 1), gasolinas, marker='o', linestyle='-', color='g')
        ax.set_xlabel('Medida')
        ax.set_ylabel('Gasolina')
        ax.set_title('Últimas medidas de gasolina')
        ax.grid(True)
        ax.set_xticks(range(1, len(gasolinas) + 1))
        st.pyplot(fig)
    else:
        st.write("No hay medidas de gasolina disponibles para este vehículo.")

def mostrar_grafica_presion(id_veh):
    presiones = obtener_ultimas_medidas_presion(id_veh)
    st.write(f"Presiones obtenidas: {presiones}")
    
    if presiones:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(range(1, len(presiones) + 1), presiones, marker='o', linestyle='-', color='orange')
        ax.set_xlabel('Medida')
        ax.set_ylabel('Presión')
        ax.set_title('Últimas medidas de presión')
        ax.grid(True)
        ax.set_xticks(range(1, len(presiones) + 1))
        st.pyplot(fig)
    else:
        st.write("No hay medidas de presión disponibles para este vehículo.")

def mostrar_grafica_aceite(id_veh):
    aceites = obtener_ultimas_medidas_aceite(id_veh)
    st.write(f"Aceite obtenido: {aceites}")
    
    if aceites:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(range(1, len(aceites) + 1), aceites, marker='o', linestyle='-', color='r')
        ax.set_xlabel('Medida')
        ax.set_ylabel('Aceite')
        ax.set_title('Últimas medidas de aceite')
        ax.grid(True)
        ax.set_xticks(range(1, len(aceites) + 1))
        st.pyplot(fig)
    else:
        st.write("No hay medidas de aceite disponibles para este vehículo.")


#Dashboard
def dashboard_vehiculo(id_vehiculo):
    # Convertir id_vehiculo a entero, en caso de que sea una cadena
    id_vehiculo = int(id_vehiculo)

    # Obtener los datos del vehículo y del conductor desde la base de datos
    datos_vehiculo = obtener_datos_vehiculo(id_vehiculo)
    if datos_vehiculo:
        id_veh, placa, modelo, color, id_conductor = datos_vehiculo
        datos_conductor = obtener_datos_conductor(id_conductor)
        nombre_conductor = datos_conductor[0] if datos_conductor else "Desconocido"
    else:
        st.error("No se encontraron datos para este vehículo.")
        return

    # Determinar qué conjunto de URLs usar según el id_vehiculo
    if id_vehiculo % 3 == 1:
        urls_sensores = urls_por_vehiculo["vehiculo_1"]
    elif id_vehiculo % 3 == 2:
        urls_sensores = urls_por_vehiculo["vehiculo_2"]
    elif id_vehiculo % 3 == 0:
        urls_sensores = urls_por_vehiculo["vehiculo_3"]
    
    # Obtener los valores de los sensores
    valores_sensores = {}
    for sensor, url in urls_sensores.items():
        valores_sensores[sensor] = obtener_valor_sensor(url, headers)
    
    # Obtener valores específicos
    presion = valores_sensores.get('presion')
    velocidad = valores_sensores.get('velocidad')
    gasolina = valores_sensores.get('gasolina')
    aceite = valores_sensores.get('aceite')
    ubicacion = valores_sensores.get('ubicacion', {})

    # Convertir la ubicación a una cadena de texto si es un diccionario con lat/lon
    if isinstance(ubicacion, dict):
        ubicacion = f"Lat: {ubicacion.get('lat', 'N/A')}, Lon: {ubicacion.get('lon', 'N/A')}"

    # Guardar los datos en la base de datos
    guardar_datos_sensores(id_vehiculo, aceite, gasolina, presion, ubicacion, velocidad)

    # Obtener los valores de estado de vía y accidente
    estado_via = obtener_valor_sensor(url_estado_via, headers)
    accidente = obtener_valor_sensor(url_accidente, headers)
    
    # Inicializar un mensaje de alerta si alguna condición se cumple
    mensaje_alerta = ""
    
    # Verificar las condiciones para activar la alerta
    if presion is not None and (presion < 30 or presion > 40):
        mensaje_alerta += f"- Presión fuera de rango: {presion}\n"
    if velocidad is not None and velocidad > 100:
        mensaje_alerta += f"- Velocidad fuera de rango: {velocidad}\n"
    if gasolina is not None and gasolina < 10:
        mensaje_alerta += f"- Nivel de gasolina bajo: {gasolina}\n"
    if aceite is not None and aceite < 10:
        mensaje_alerta += f"- Nivel de aceite bajo: {aceite}\n"
    
    # Enviar correo de alerta y registrar alerta en la base de datos si alguna condición se cumple
    if mensaje_alerta:
        # Enviar el correo de alerta
        enviar_alerta_correo(mensaje_alerta)  
        # Registrar la alerta en la base de datos con timestamp
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        alerta_registrada = False  # Variable para verificar si se registra alguna alerta
        try:
            # Dividir el mensaje en líneas para obtener cada alerta específica
            for linea in mensaje_alerta.split('\n'):
                if linea:  # Verificar que la línea no esté vacía
                    # Obtener el nombre de la variable y su valor
                    partes_alerta = linea.split(":")
                    if len(partes_alerta) >= 2:
                        nombre_alerta = partes_alerta[0].strip()  # Nombre de la variable que presenta la alerta
                        valor_alerta = partes_alerta[1].strip()   # Valor de la variable que generó la alerta

                        # Insertar en la tabla de alertas con el timestamp
                        cursor.execute('''
                            INSERT INTO alertas (nombre, descripcion, id_veh)
                            VALUES (?, ?, ?)
                        ''', (nombre_alerta, f"Placa: {placa}, Valor: {valor_alerta}", id_veh))
                        alerta_registrada = True  # Marcar como registrada

            conexion.commit()
            if alerta_registrada:
                st.success("Alerta registrada en la base de datos.")
        except Exception as e:
            st.error(f"Error al registrar la alerta: {e}")
        finally:
            conexion.close()

    # Personalizar las descripciones de estado de vía y accidente
    estado_via_texto = "Abierta" if estado_via else "Cerrada"
    accidente_texto = "Sí" if accidente else "No"
    
    # Mostrar el dashboard con la información del vehículo y sensores
    st.title(f"Dashboard del Vehículo ID: {id_vehiculo}")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Información del Vehículo")
        st.write(f"**Placa:** {placa}")
        st.write(f"**Modelo:** {modelo}")
        st.write(f"**Color:** {color}")
        st.write(f"**Conductor:** {nombre_conductor}")

        st.subheader("Estado de Ruta")
        st.write(f"Estado de Vía: {estado_via_texto}")
        st.write(f"Accidente: {accidente_texto}")
        
        # Mostrar los datos de los sensores
        st.subheader("Datos de Sensores")
        st.write(f"Aceite: {aceite}")
        st.write(f"Gasolina: {gasolina}")
        st.write(f"Presión: {presion}")
        st.write(f"Ubicación: {ubicacion}")
        
        # Añadir título de Velocidad y mostrar la velocidad de manera destacada
        st.markdown("<h3 style='margin-top: 20px;'>Velocidad</h3>", unsafe_allow_html=True)
        st.write(f"Velocidad: {velocidad}")

        # Mostrar la gráfica de las últimas medidas de velocidad
        st.subheader("Gráficas de Sensores")
        mostrar_grafica_velocidad(id_vehiculo)
        mostrar_grafica_gasolina(id_vehiculo)
        mostrar_grafica_presion(id_vehiculo)
        mostrar_grafica_aceite(id_vehiculo)

    with col2:
        st.subheader("Mapa")
        
        # Verificar si las coordenadas están disponibles
        latitud = valores_sensores.get('ubicacion', {}).get('lat')
        longitud = valores_sensores.get('ubicacion', {}).get('lon')
        if latitud and longitud:
            # Configuración del mapa en pydeck
            view_state = pdk.ViewState(
                latitude=latitud,
                longitude=longitud,
                zoom=11,
                pitch=50,
            )

            # Capa para mostrar la ubicación como punto en el mapa
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=[{"lat": latitud, "lon": longitud}],
                get_position="[lon, lat]",
                get_color="[200, 30, 0, 160]",
                get_radius=200,
            )

            # Crear el mapa
            mapa = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "Ubicación: {lat}, {lon}"},
            )

            # Mostrar el mapa en Streamlit
            st.pydeck_chart(mapa)
        else:
            st.write("Ubicación no disponible")

      

            
def perfil_page():
    st.title("Mi Perfil")
    usuario = obtener_datos_usuario(st.session_state.id_usuario)
    if usuario:
        nombre, rol, correo = usuario

        # Obtener la URL de la imagen de perfil del usuario desde la base de datos
        img_usr_url = obtener_imagen_usuario(st.session_state.id_usuario)
        # URL de imagen predeterminada si el campo está vacío
        if not img_usr_url:
            img_usr_url = "https://cdn.pixabay.com/photo/2015/10/05/22/37/blank-profile-picture-973460_1280.png"

        # Mostrar la imagen del perfil
        st.image(img_usr_url, width=150, caption="Imagen de Perfil")

        # Botón para abrir el popup de edición de imagen
        if "editar_imagen" not in st.session_state:
            st.session_state.editar_imagen = False

        if st.button("Editar Imagen"):
            st.session_state.editar_imagen = not st.session_state.editar_imagen

        # Mostrar el input de edición si se presiona el botón
        if st.session_state.editar_imagen:
            nueva_url_img = st.text_input("Ingrese la nueva URL de la imagen", key="input_nueva_img")

            # Botón para actualizar la imagen
            if st.button("Actualizar Imagen"):
                if nueva_url_img:
                    actualizar_imagen_usuario(st.session_state.id_usuario, nueva_url_img)
                    st.success("Imagen de perfil actualizada.")
                    st.session_state.editar_imagen = False  # Cerrar el modo de edición
                else:
                    st.warning("Por favor, ingrese una URL válida.")

        st.write(f"**Nombre:** {nombre}")
        st.write(f"**Rol:** {rol}")
        st.write(f"**Correo:** {correo}")
    else:
        st.error("No se pudo cargar la información del perfil.")

# Inicializar el estado de la sesión
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if 'id_usuario' not in st.session_state:
    st.session_state.id_usuario = None

if 'rol' not in st.session_state:
    st.session_state.rol = None

if 'nav_option' not in st.session_state:
    st.session_state.nav_option = "Login"

if 'vehiculo_seleccionado' not in st.session_state:
    st.session_state.vehiculo_seleccionado = None

# Función para la pantalla de login
def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])  # Crear columnas para centrar el contenido

    with col2:  # Contenido centrado en la segunda columna
        st.title("Iniciar Sesión")
        correo = st.text_input("Correo Electrónico", max_chars=30)
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Iniciar Sesión"):
            autenticado, id_usuario, rol = autenticar_usuario(correo, password)
            if autenticado:
                st.session_state.authenticated = True
                st.session_state.id_usuario = id_usuario
                st.session_state.rol = rol
                st.session_state.nav_option = "Home"
                st.success("Inicio de sesión exitoso.")
            else:
                st.error("Correo o contraseña incorrectos")
        
        if st.button("Registrarse", key="register_btn"):
            st.session_state.nav_option = "Registro"

# Función de registro
def registro_page():
    col1, col2, col3 = st.columns([1, 2, 1])  # Crear columnas para centrar el contenido

    with col2:  # Contenido centrado en la segunda columna
        st.title("Registrarse")
        nombre = st.text_input("Nombre Completo", max_chars=30)
        correo = st.text_input("Correo Electrónico", max_chars=30)
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Registrarse"):
            registrar_usuario(nombre, correo, password)
            st.session_state.nav_option = "Login"
        
        if st.button("Volver al Login", key="back_to_login_btn"):
            st.session_state.nav_option = "Login"



# Modificar la navegación en el sidebar
if not st.session_state.authenticated:
    if st.session_state.nav_option == "Login":
        login_page()
    elif st.session_state.nav_option == "Registro":
        registro_page()
else:
    # Sidebar solo si el usuario está autenticado
    st.sidebar.title("Navegación")
    if st.sidebar.button('Home'):
        st.session_state.nav_option = "Home"
    if st.sidebar.button('Mi Perfil'):
        st.session_state.nav_option = "Mi Perfil"
    if st.session_state.rol != "conductor":
        if st.sidebar.button('Crear Conductor'):
            st.session_state.nav_option = "Crear Conductor"
        if st.sidebar.button('Crear Vehículo'):
            st.session_state.nav_option = "Crear Vehículo"
        # Mostrar el botón de Planes solo si el usuario no es admin_premium
        if st.session_state.rol != "admin_premium":
            if st.sidebar.button('Planes'):  # Agregar botón solo para administradores que no sean premium
                st.session_state.nav_option = "Planes"
    if st.sidebar.button('Soporte'):
        st.session_state.nav_option = "Soporte"
    if st.sidebar.button('Alertas'):  # Agregar acceso a la página de alertas
        st.session_state.nav_option = "Alertas"
    if st.sidebar.button('Cerrar Sesión'):
        st.session_state.authenticated = False
        st.session_state.nav_option = "Login"

        
    # Navegar a la pantalla correspondiente según la selección del usuario
    if st.session_state.nav_option == "Home":
        home_page()
    elif st.session_state.nav_option == "Mi Perfil":
        perfil_page()
    elif st.session_state.nav_option == "Crear Conductor":
        crear_conductor_page()
    elif st.session_state.nav_option == "Crear Vehículo":
        crear_vehiculo_page()
    elif st.session_state.nav_option == "Dashboard Vehículo":
        if st.session_state.vehiculo_seleccionado:
            dashboard_vehiculo(st.session_state.vehiculo_seleccionado)
        else:
            st.error("No se ha seleccionado ningún vehículo.")
    elif st.session_state.nav_option == "Soporte":
        soporte_page()
    elif st.session_state.nav_option == "Planes":
        planes_page()
    elif st.session_state.nav_option == "Alertas":
        alertas_page()
    elif st.session_state.nav_option == "Pasarela":
        pasarela_page()
    elif st.session_state.nav_option == "Pago Realizado":
        pago_realizado_page()