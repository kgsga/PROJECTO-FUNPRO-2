from database import hacer_admin
usuario = input("Nombre del usuario que será administrador: ").strip().lower()
if hacer_admin(usuario):
    print("El usuario ahora es administrador.")
else:
    print("No se encontró ese usuario.")