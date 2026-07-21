class NodoHistorial:
    def __init__(self, id_registro, imagen, resultado, fecha, hora):
        self.id_registro = id_registro
        self.imagen = imagen
        self.resultado = resultado
        self.fecha = fecha
        self.hora = hora
        self.siguiente = None