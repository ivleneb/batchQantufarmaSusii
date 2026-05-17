import os

class BatchUtils:
    @staticmethod
    def crear_carpeta_si_no_existe(ruta):
        """Crea una carpeta si no existe"""
        if not os.path.exists(ruta):
            os.makedirs(ruta)
            print(f"Carpeta creada: {ruta}")
        else:
            print(f"La carpeta ya existe: {ruta}")
