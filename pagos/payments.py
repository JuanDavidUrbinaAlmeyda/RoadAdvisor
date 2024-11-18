import paypalrestsdk

# Configuración de PayPal con tus credenciales de Sandbox
paypalrestsdk.configure({
    "mode": "sandbox",  # Cambiar a "live" para producción
    "client_id": "AU3W5KH4y4AGqZyNTIBkbznowK2biP4ZZ-0_hX2q2zGvAL-3DiSAfRnTi8xe8aiYxOJzzmWpNK2MLbQJ",  # Reemplaza con tu Client ID de sandbox
    "client_secret": "EHdckQdaKdXZ25EZEcxkolptxOpjdmHtO1COKU_KGEYDb8sM-mfABeVbCkmUy6RtBrUtT28qi_ETazMN"  # Reemplaza con tu Secret de sandbox
})

def crear_pago_paypal():
    # Crear un nuevo pago
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": "http://localhost:3000/payment/execute",  # Cambiar por una URL válida en tu aplicación
            "cancel_url": "http://localhost:3000/"  # Cambiar por una URL válida en tu aplicación
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "Plan Premium",
                    "sku": "001",
                    "price": "30.00",
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": "30.00",
                "currency": "USD"
            },
            "description": "Pago de prueba con PayPal."
        }]
    })

    # Crear el pago
    if payment.create():
        print("Pago creado con éxito")
        for link in payment.links:
            if link.rel == "approval_url":
                # Redirigir al usuario a esta URL para aprobar el pago
                return link.href  # Devuelve la URL de aprobación
    else:
        print("Error al crear el pago:", payment.error)  # Maneja los errores si el pago falla
        return None
