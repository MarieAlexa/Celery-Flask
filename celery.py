from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from celery import Celery
import redis

app = Flask(__name__)
app.secret_key = "llaveultrasecreta"

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tu_correo@gmail.com'
app.config['MAIL_PASSWORD'] = 'tu_contraseña'
app.config['MAIL_DEFAULT_SENDER'] = 'tu_correo@gmail.com'

mail = Mail(app)


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend='redis://localhost:6379/0',
        broker='redis://localhost:6379/0'
    )
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)
client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

@celery.task
def send_async_email(subject, recipients, body):
    try:
        msg = Message(subject=subject, recipients=recipients, body=body)
        with app.app_context():
            mail.send(msg)
        print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"Error al enviar el correo: {str(e)}")

        @app.route("/nueva", methods=["GET", "POST"])
        def nueva_receta():
            if request.method == "POST":
                nombre = request.form["nombre"]
                ingredientes = request.form["ingredientes"]
                pasos = request.form["pasos"]

                if not nombre or not ingredientes or not pasos:
                    flash("Todos los campos son obligatorios.", "error")
                    return redirect(url_for('nueva_receta'))

                receta_id = client.incr("receta:id")
                key = f"receta:{receta_id}"
                receta = {
                    "nombre": nombre,
                    "ingredientes": ingredientes,
                    "pasos": pasos
                }
                client.hset(key, mapping=receta)


                subject = "Nueva Receta Agregada"
                recipients = ["destinatario@example.com"]
                body = f"Se ha agregado una nueva receta:\n\nNombre: {nombre}\nIngredientes: {ingredientes}\nPasos: {pasos}"
                send_async_email.delay(subject, recipients, body)

                flash("Receta agregada exitosamente y correo enviado!", "success")
                return redirect(url_for('home'))
            return render_template("nueva.html")