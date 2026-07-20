import pandas as pd
import os
import shutil

csv_file = "dataset/avocado labels 1.csv"
imagenes = "static/entrenamiento"

df = pd.read_csv(csv_file)

for _, fila in df.iterrows():
    nombre = fila["Identification"] + ".jpg"
    clase = fila["Condition"]

    origen = os.path.join(imagenes, nombre)

    destino = os.path.join(imagenes, clase)
    os.makedirs(destino, exist_ok=True)

    if os.path.exists(origen):
        shutil.move(
            origen,
            os.path.join(destino, nombre)
        )
print("Proceso terminado")