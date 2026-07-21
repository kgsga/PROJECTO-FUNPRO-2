from werkzeug.security import check_password_hash
from estructuras.nodo import Nodo
class ArbolUsuarios:
    def __init__(self):
        self.raiz = None
    def insertar(self, id_usuario, usuario, contrasena_hash, rol):
        nuevo = Nodo(id_usuario, usuario, contrasena_hash, rol)
        if self.raiz is None:
            self.raiz = nuevo
            return True
        return self._insertar(self.raiz, nuevo)
    def _insertar(self, actual, nuevo):
        if nuevo.usuario == actual.usuario:
            return False
        if nuevo.usuario < actual.usuario:
            if actual.izquierda is None:
                actual.izquierda = nuevo
                return True
            return self._insertar(actual.izquierda, nuevo)
        if actual.derecha is None:
            actual.derecha = nuevo
            return True
        return self._insertar(actual.derecha, nuevo)
    def buscar_usuario(self, usuario):
        return self._buscar_usuario(self.raiz, usuario)
    def _buscar_usuario(self, nodo, usuario):
        if nodo is None:
            return None
        if usuario == nodo.usuario:
            return nodo
        if usuario < nodo.usuario:
            return self._buscar_usuario(nodo.izquierda, usuario)
        return self._buscar_usuario(nodo.derecha, usuario)
    def autenticar(self, usuario, contrasena):
        nodo = self.buscar_usuario(usuario)
        if nodo is None:
            return None
        if check_password_hash(nodo.contrasena_hash, contrasena):
            return nodo
        return None