from flask import Flask, render_template, request, redirect, url_for, session, flash
import tensorflow as tf
import numpy as np
from PIL import Image
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from estructuras.arbol import ArbolUsuarios
from estructuras.pila_historial import PilaHistorial
from database import obtener_estadisticas_usuario,obtener_estadisticas_confirmacion, obtener_diagnosticos_incorrectos,confirmar_diagnostico,usuario_esta_activo, cambiar_estado_usuario,obtener_todos_registros_admin,crear_tablas, guardar_usuario, obtener_usuarios,guardar_registro, obtener_registros_usuario, eliminar_registro, obtener_estadisticas_admin, obtener_usuarios_admin
app = Flask(__name__)
app.secret_key = "clave_secreta_proyecto_aguacate"
CARPETA_PROYECTO = Path(__file__).resolve().parent
UPLOAD_FOLDER = CARPETA_PROYECTO / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
crear_tablas()
usuarios = ArbolUsuarios()
for cuenta in obtener_usuarios():
    usuarios.insertar(cuenta["id"], cuenta["usuario"], cuenta["contrasena_hash"], cuenta["rol"])
RUTA_MODELO = CARPETA_PROYECTO / "modelo.tflite"
interpreter = tf.lite.Interpreter(model_path=str(RUTA_MODELO))
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
def predict_image(path):
    imagen = Image.open(path).convert("RGB")
    imagen = imagen.resize((224, 224))
    imagen = np.array(imagen, dtype=np.float32)
    imagen = np.expand_dims(imagen, axis=0)
    interpreter.set_tensor(input_details[0]["index"], imagen)
    interpreter.invoke()
    prediccion = interpreter.get_tensor(output_details[0]["index"])[0]
    clases = ["Anthracnose", "Healthy", "Scab"]
    indice = int(np.argmax(prediccion))
    clase = clases[indice]
    confianza = float(prediccion[indice]) * 100
    print("Resultado:", clase)
    print("Confianza:", confianza)
    return clase, confianza
def obtener_informacion_diagnostico(resultado, confianza):
    if confianza >= 80:
        nivel = "Alta"
        mensaje = "El modelo presenta un nivel alto de confianza en este resultado."
    elif confianza >= 60:
        nivel = "Moderada"
        mensaje = "El resultado presenta una confianza moderada. Se recomienda revisar el fruto y realizar una nueva captura si existen dudas."
    else:
        nivel = "Baja"
        mensaje = "El resultado presenta una confianza baja. Se recomienda analizar otra fotografía con mejor iluminación y enfoque."
    if resultado == "Anthracnose":
        recomendacion = "Se recomienda separar los frutos afectados y realizar una revisión de otros frutos cercanos para identificar posibles síntomas similares."
    elif resultado == "Scab":
        recomendacion = "Se recomienda inspeccionar la superficie de otros frutos y mantener un seguimiento ante la aparición de nuevas lesiones."
    else:
        recomendacion = "No se detectaron signos visibles de antracnosis o sarna en la imagen analizada. Se recomienda continuar con la observación del fruto."
    return nivel, mensaje, recomendacion
@app.route("/")
def home():
    if "usuario_id" in session:
        if session.get("rol") == "admin":
            return redirect(url_for("admin"))
        return redirect(url_for("principal"))
    return render_template("login.html")
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        return render_template("registro.html")
    usuario = request.form.get("usuario", "").strip().lower()
    contrasena = request.form.get("contrasena", "")
    confirmar = request.form.get("confirmar", "")
    if len(usuario) < 3:
        return render_template("registro.html", error="El usuario debe tener al menos 3 caracteres.")
    if len(contrasena) < 4:
        return render_template("registro.html", error="La contraseña debe tener al menos 4 caracteres.")
    if contrasena != confirmar:
        return render_template("registro.html", error="Las contraseñas no coinciden.")
    if usuarios.buscar_usuario(usuario) is not None:
        return render_template("registro.html", error="Ese nombre de usuario ya está registrado.")
    contrasena_hash = generate_password_hash(contrasena)
    id_usuario = guardar_usuario(usuario, contrasena_hash)
    if id_usuario is None:
        return render_template("registro.html", error="No se pudo crear la cuenta.")
    usuarios.insertar(id_usuario, usuario, contrasena_hash, "usuario")
    flash("Cuenta creada correctamente. Ya puede iniciar sesión.")
    return redirect(url_for("home"))
@app.route("/login", methods=["POST"])
def login():
    usuario = request.form.get("usuario", "").strip().lower()
    contrasena = request.form.get("contrasena", "")
    usuario_encontrado = usuarios.autenticar(usuario, contrasena)
    if usuario_encontrado is None:
        return render_template("login.html", error="Usuario o contraseña incorrectos.")
    if not usuario_esta_activo(usuario_encontrado.id_usuario):
        return render_template("login.html", error="Esta cuenta ha sido desactivada por el administrador.")
    session["usuario_id"] = usuario_encontrado.id_usuario
    session["usuario"] = usuario_encontrado.usuario
    session["rol"] = usuario_encontrado.rol
    if usuario_encontrado.rol == "admin":
        return redirect(url_for("admin"))
    return redirect(url_for("principal"))
@app.route("/principal")
def principal():
    if "usuario_id" not in session:
        return redirect(url_for("home"))
    if session.get("rol") == "admin":
        return redirect(url_for("admin"))
    return render_template("index.html", usuario=session["usuario"])
@app.route("/upload", methods=["POST"])
def upload():
    if "usuario_id" not in session:
        return redirect(url_for("home"))
    archivo = request.files.get("imagen")
    if archivo is None or archivo.filename == "":
        return render_template("index.html", usuario=session["usuario"], error="Seleccione una imagen.")
    nombre_original = secure_filename(archivo.filename)
    nombre_guardado = str(uuid4()) + "_" + nombre_original
    ruta = UPLOAD_FOLDER / nombre_guardado
    archivo.save(str(ruta))
    resultado, confianza = predict_image(ruta)
    nivel, mensaje_confianza, recomendacion = obtener_informacion_diagnostico(resultado, confianza)
    resultados_espanol = {
        "Anthracnose": "Antracnosis",
        "Healthy": "Aguacate sano",
        "Scab": "Sarna o roña"
    }
    ahora = datetime.now()
    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M:%S")
    id_registro = guardar_registro(session["usuario_id"], nombre_guardado, resultados_espanol[resultado], fecha, hora)
    imagen_url = url_for("static", filename="uploads/" + nombre_guardado)
    return render_template("index.html", usuario=session["usuario"], resultado=resultado, confianza=round(confianza, 2), nivel=nivel, mensaje_confianza=mensaje_confianza, recomendacion=recomendacion, imagen=imagen_url, id_registro=id_registro)
@app.route("/registros")
def registros():
    if "usuario_id" not in session:
        return redirect(url_for("home"))
    filtro_resultado = request.args.get("resultado", "")
    filtro_fecha = request.args.get("fecha", "")
    fecha_busqueda = ""
    if filtro_fecha:
        try:
            fecha_busqueda = datetime.strptime(filtro_fecha, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            fecha_busqueda = ""
    pila = PilaHistorial()
    registros_usuario = obtener_registros_usuario(session["usuario_id"], filtro_resultado, fecha_busqueda)
    for registro in registros_usuario:
        pila.apilar(registro["id"], registro["imagen"], registro["resultado"], registro["fecha"], registro["hora"])
    historial = pila.obtener_historial()
    return render_template("historial.html", usuario=session["usuario"], historial=historial, filtro_resultado=filtro_resultado, filtro_fecha=filtro_fecha)
@app.route("/eliminar-registro/<int:id_registro>", methods=["POST"])
def eliminar_historial(id_registro):
    if "usuario_id" not in session:
        return redirect(url_for("home"))
    nombre_imagen = eliminar_registro(id_registro, session["usuario_id"])
    if nombre_imagen is not None:
        ruta_imagen = UPLOAD_FOLDER / nombre_imagen
        if ruta_imagen.exists():
            ruta_imagen.unlink()
    return redirect(url_for("registros"))
@app.route("/admin")
def admin():
    if "usuario_id" not in session:
        return redirect(url_for("home"))
    if session.get("rol") != "admin":
        return redirect(url_for("principal"))
    estadisticas = obtener_estadisticas_admin()
    confirmaciones = obtener_estadisticas_confirmacion()
    lista_usuarios = obtener_usuarios_admin()
    return render_template("admin.html", usuario=session["usuario"], estadisticas=estadisticas, confirmaciones=confirmaciones, lista_usuarios=lista_usuarios)
@app.route("/admin/reportados")
def admin_reportados():
    if "usuario_id" not in session:
        return redirect(url_for("home"))
    if session.get("rol") != "admin":
        return redirect(url_for("principal"))
    diagnosticos = obtener_diagnosticos_incorrectos()
    return render_template("admin_reportados.html", usuario=session["usuario"], diagnosticos=diagnosticos)
@app.route("/admin/diagnosticos")
def admin_diagnosticos():
    if "usuario_id" not in session:
        return redirect(url_for("home"))
    if session.get("rol") != "admin":
        return redirect(url_for("principal"))
    filtro_usuario = request.args.get("usuario", "")
    filtro_resultado = request.args.get("resultado", "")
    filtro_fecha = request.args.get("fecha", "")
    diagnosticos = obtener_todos_registros_admin(filtro_usuario, filtro_resultado, filtro_fecha)
    lista_usuarios = obtener_usuarios_admin()
    return render_template("admin_diagnosticos.html", usuario=session["usuario"], diagnosticos=diagnosticos, lista_usuarios=lista_usuarios, filtro_usuario=filtro_usuario, filtro_resultado=filtro_resultado, filtro_fecha=filtro_fecha)
@app.route("/admin/cambiar-estado/<int:id_usuario>", methods=["POST"])
def admin_cambiar_estado(id_usuario):
    if "usuario_id" not in session:
        return redirect(url_for("home"))
    if session.get("rol") != "admin":
        return redirect(url_for("principal"))
    cambiar_estado_usuario(id_usuario)
    return redirect(url_for("admin"))
@app.route("/confirmar-diagnostico/<int:id_registro>/<respuesta>", methods=["POST"])
def registrar_confirmacion(id_registro, respuesta):
    if "usuario_id" not in session:
        return redirect(url_for("home"))
    if respuesta not in ["si", "no"]:
        return redirect(url_for("principal"))
    valor = 1 if respuesta == "si" else 0
    confirmar_diagnostico(id_registro, session["usuario_id"], valor)
    flash("Gracias por confirmar el resultado del diagnóstico.")
    return redirect(url_for("principal"))
@app.route("/mis-estadisticas")
def mis_estadisticas():
    if "usuario_id" not in session:
        return redirect(url_for("home"))
    if session.get("rol") == "admin":
        return redirect(url_for("admin"))
    estadisticas = obtener_estadisticas_usuario(session["usuario_id"])
    return render_template("estadisticas_usuario.html", usuario=session["usuario"], estadisticas=estadisticas)
@app.route("/enfermedades")
def enfermedades():
    if "usuario_id" not in session:
        return redirect(url_for("home"))
    return render_template("enfermedades.html", usuario=session["usuario"])
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
if __name__ == "__main__":
    app.run(debug=True)