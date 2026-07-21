from estructuras.nodo_historial import NodoHistorial
class PilaHistorial:
    def __init__(self):
        self.tope = None
    def esta_vacia(self):
        return self.tope is None
    def apilar(self, id_registro, imagen, resultado, fecha, hora):
        nuevo = NodoHistorial(id_registro, imagen, resultado, fecha, hora)
        nuevo.siguiente = self.tope
        self.tope = nuevo
    def desapilar(self):
        if self.esta_vacia():
            return None
        eliminado = self.tope
        self.tope = self.tope.siguiente
        eliminado.siguiente = None
        return eliminado
    def obtener_historial(self):
        historial = []
        actual = self.tope
        while actual is not None:
            historial.append({
                "id_registro": actual.id_registro,
                "imagen": actual.imagen,
                "resultado": actual.resultado,
                "fecha": actual.fecha,
                "hora": actual.hora
            })
            actual = actual.siguiente
        return historial