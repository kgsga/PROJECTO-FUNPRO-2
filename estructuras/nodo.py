class Nodo:
    def __init__(self, id_usuario, usuario, contrasena_hash, rol):
        self.id_usuario = id_usuario
        self.usuario = usuario
        self.contrasena_hash = contrasena_hash
        self.rol = rol
        self.izquierda = None
        self.derecha = None