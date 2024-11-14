import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def enviar_alerta_correo(content):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # Usa 587 para starttls
    correo_emisor = 'juanchitourbinaalmeyda@gmail.com'
    contrasena = 'wjxx kobf ghgi bkfw'  # Considera usar una contraseña de aplicación
    destinatario = 'jurbina148@unab.edu.co'  # Correo del destinatario fijo

    # Crea el mensaje
    mensaje = MIMEMultipart()
    mensaje['From'] = correo_emisor
    mensaje['To'] = destinatario
    mensaje['Subject'] = 'Alerta de sensores en RoadAdvisor'
    mensaje.attach(MIMEText(content, 'plain'))

    try:
        # Conecta al servidor SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()  # Inicia la conexión TLS
        server.login(correo_emisor, contrasena)  # Inicia sesión
        server.sendmail(correo_emisor, destinatario, mensaje.as_string())  # Envía el correo
        print("Correo de alerta enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar el correo de alerta: {e}")
    finally:
        server.quit()  # Cierra la conexión
