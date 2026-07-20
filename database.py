import sqlite3
from pathlib import Path
CARPETA_PROYECTO = Path(__file__).resolve().parent
RUTA_BASE_DATOS = CARPETA_PROYECTO / "registros.db"
def conectar():
    conexion = sqlite3.connect(str(RUTA_BASE_DATOS))
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion
def crear_tablas():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL UNIQUE,
        contrasena_hash TEXT NOT NULL
    )
    """)
    cursor.execute("PRAGMA table_info(usuarios)")
    columnas = [columna["name"] for columna in cursor.fetchall()]
    if "rol" not in columnas:    
        cursor.execute("ALTER TABLE usuarios ADD COLUMN rol TEXT NOT NULL DEFAULT 'usuario'")
    if "activo" not in columnas:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        imagen TEXT NOT NULL,
        resultado TEXT NOT NULL,
        fecha TEXT NOT NULL,
        hora TEXT NOT NULL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    )
    """)
    cursor.execute("PRAGMA table_info(historial)")
    columnas_historial = [columna["name"] for columna in cursor.fetchall()]
    if "confirmado" not in columnas_historial:
        cursor.execute("ALTER TABLE historial ADD COLUMN confirmado INTEGER")
    conexion.commit()
    conexion.close()
def guardar_usuario(usuario, contrasena_hash):
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (usuario, contrasena_hash, rol) VALUES (?, ?, ?)", (usuario, contrasena_hash, "usuario"))
        id_usuario = cursor.lastrowid
        conexion.commit()
        return id_usuario
    except sqlite3.IntegrityError:
        return None
    finally:
        conexion.close()
def obtener_usuarios():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT id, usuario, contrasena_hash, rol FROM usuarios")
    usuarios = cursor.fetchall()
    conexion.close()
    return usuarios
def hacer_admin(usuario):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("UPDATE usuarios SET rol = 'admin' WHERE usuario = ?", (usuario,))
    actualizado = cursor.rowcount > 0
    conexion.commit()
    conexion.close()
    return actualizado
def guardar_registro(usuario_id, imagen, resultado, fecha, hora):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO historial (usuario_id, imagen, resultado, fecha, hora) VALUES (?, ?, ?, ?, ?)", (usuario_id, imagen, resultado, fecha, hora))
    id_registro = cursor.lastrowid
    conexion.commit()
    conexion.close()
    return id_registro
def obtener_registros_usuario(usuario_id, resultado="", fecha=""):
    conexion = conectar()
    cursor = conexion.cursor()
    consulta = "SELECT id, imagen, resultado, fecha, hora FROM historial WHERE usuario_id = ?"
    parametros = [usuario_id]
    if resultado:
        consulta += " AND resultado = ?"
        parametros.append(resultado)
    if fecha:
        consulta += " AND fecha = ?"
        parametros.append(fecha)
    consulta += " ORDER BY id ASC"
    cursor.execute(consulta, parametros)
    registros = cursor.fetchall()
    conexion.close()
    return registros
def eliminar_registro(id_registro, usuario_id):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT imagen FROM historial WHERE id = ? AND usuario_id = ?", (id_registro, usuario_id))
    registro = cursor.fetchone()
    if registro is None:
        conexion.close()
        return None
    imagen = registro["imagen"]
    cursor.execute("DELETE FROM historial WHERE id = ? AND usuario_id = ?", (id_registro, usuario_id))
    conexion.commit()
    conexion.close()
    return imagen
def obtener_estadisticas_admin():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'usuario'")
    total_usuarios = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial")
    total_diagnosticos = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE resultado = 'Antracnosis'")
    antracnosis = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE resultado = 'Sarna o roña'")
    sarna = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE resultado = 'Aguacate sano'")
    sanos = cursor.fetchone()["total"]
    conexion.close()
    return {"usuarios": total_usuarios, "diagnosticos": total_diagnosticos, "antracnosis": antracnosis, "sarna": sarna, "sanos": sanos}
def obtener_usuarios_admin():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    SELECT usuarios.id, usuarios.usuario, usuarios.rol, usuarios.activo, COUNT(historial.id) AS diagnosticos
    FROM usuarios
    LEFT JOIN historial ON usuarios.id = historial.usuario_id
    GROUP BY usuarios.id
    ORDER BY usuarios.usuario
    """)
    datos = cursor.fetchall()
    conexion.close()
    return datos
def obtener_todos_registros_admin(usuario="", resultado="", fecha=""):
    conexion = conectar()
    cursor = conexion.cursor()
    consulta = """
    SELECT historial.id, usuarios.usuario, historial.imagen, historial.resultado, historial.fecha, historial.hora
    FROM historial
    INNER JOIN usuarios ON historial.usuario_id = usuarios.id
    WHERE 1=1
    """
    parametros = []
    if usuario:
        consulta += " AND usuarios.usuario = ?"
        parametros.append(usuario)
    if resultado:
        consulta += " AND historial.resultado = ?"
        parametros.append(resultado)
    if fecha:
        consulta += " AND historial.fecha = ?"
        parametros.append(fecha)
    consulta += " ORDER BY historial.id DESC"
    cursor.execute(consulta, parametros)
    registros = cursor.fetchall()
    conexion.close()
    return registros
def usuario_esta_activo(id_usuario):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT activo FROM usuarios WHERE id = ?", (id_usuario,))
    usuario = cursor.fetchone()
    conexion.close()
    if usuario is None:
        return False
    return usuario["activo"] == 1
def cambiar_estado_usuario(id_usuario):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT activo, rol FROM usuarios WHERE id = ?", (id_usuario,))
    usuario = cursor.fetchone()
    if usuario is None or usuario["rol"] == "admin":
        conexion.close()
        return False
    nuevo_estado = 0 if usuario["activo"] == 1 else 1
    cursor.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (nuevo_estado, id_usuario))
    conexion.commit()
    conexion.close()
    return True
def confirmar_diagnostico(id_registro, usuario_id, confirmado):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("UPDATE historial SET confirmado = ? WHERE id = ? AND usuario_id = ?", (confirmado, id_registro, usuario_id))
    actualizado = cursor.rowcount > 0
    conexion.commit()
    conexion.close()
    return actualizado
def obtener_estadisticas_confirmacion():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE confirmado = 1")
    correctos = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE confirmado = 0")
    incorrectos = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE confirmado IS NULL")
    pendientes = cursor.fetchone()["total"]
    conexion.close()
    return {"correctos": correctos, "incorrectos": incorrectos, "pendientes": pendientes}
def obtener_diagnosticos_incorrectos():
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    SELECT historial.id, usuarios.usuario, historial.imagen, historial.resultado, historial.fecha, historial.hora
    FROM historial
    INNER JOIN usuarios ON historial.usuario_id = usuarios.id
    WHERE historial.confirmado = 0
    ORDER BY historial.id DESC
    """)
    registros = cursor.fetchall()
    conexion.close()
    return registros
def obtener_estadisticas_usuario(usuario_id):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE usuario_id = ?", (usuario_id,))
    total = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE usuario_id = ? AND resultado = 'Antracnosis'", (usuario_id,))
    antracnosis = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE usuario_id = ? AND resultado = 'Sarna o roña'", (usuario_id,))
    sarna = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE usuario_id = ? AND resultado = 'Aguacate sano'", (usuario_id,))
    sanos = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE usuario_id = ? AND confirmado = 1", (usuario_id,))
    correctos = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE usuario_id = ? AND confirmado = 0", (usuario_id,))
    incorrectos = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM historial WHERE usuario_id = ? AND confirmado IS NULL", (usuario_id,))
    pendientes = cursor.fetchone()["total"]
    conexion.close()
    return {"total": total, "antracnosis": antracnosis, "sarna": sarna, "sanos": sanos, "correctos": correctos, "incorrectos": incorrectos, "pendientes": pendientes}