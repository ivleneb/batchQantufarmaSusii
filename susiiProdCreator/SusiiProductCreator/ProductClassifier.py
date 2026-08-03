# This Python file uses the following encoding: utf-8
from PySide6.QtCore import QObject, Signal, Slot
import sys
sys.path.append(r'../../')
from lib.QantuClassifier import QantuClassifier
from lib.PropertyLoader import PropertyLoader

"""class ProductClassifier(QObject):
    def __init__(self):
        pass
"""

class ProductClassifier(QObject):
    """Clase para clasificar productos desde QML"""

    # Señal para enviar el resultado de vuelta a QML
    classificationFinished = Signal(str, str)  # (registro, categoria)
    classificationError = Signal(str)         # (mensaje_error)

    def __init__(self):
        super().__init__()
        # self.classifier = QantuClassifier()  # Instancia de tu clasificador

    @Slot(str)
    def classify(self, registro: str):
        """
        Slot que recibe el registro sanitario desde QML
        y retorna la categoría
        """
        print(f"Clasificando registro: {registro}")

        try:
            # Valida que el registro no esté vacío
            if not registro or not registro.strip():
                self.classificationError.emit("El registro sanitario está vacío")
                return

            # ==== AQUÍ USAS TU QANTUCLASSIFIER ====
            code = QantuClassifier.digemidRegCodeFromStr(registro)
            categoria = None
            if code:
                listCodePerCat = PropertyLoader.getRegCodePerCategory()
                for cat, lsCodes in listCodePerCat.items():
                    if code in lsCodes:
                        categoria = cat
                        break

                if not categoria:
                    listCodePerCatDigesa = PropertyLoader.getRegDigesaCodePerCategory()
                    for cat, lsCodes in listCodePerCatDigesa.items():
                        if code in lsCodes:
                            categoria = cat
                            break

            # categoria = self.classifier.get_category(registro)

            # Simulación: clasificación de ejemplo
            # Reemplaza esto con tu QantuClassifier real
            """if "DM" in registro:
                categoria = "Medicamento"
            elif "DE" in registro:
                categoria = "Dispositivo Médico"
            elif "G" in registro:
                categoria = "Genérico"
            else:
                categoria = "No clasificado"
            """
            # Emitir señal con el resultado
            self.classificationFinished.emit(registro, categoria)
            print(f"Categoría: {categoria}")

        except Exception as e:
            error_msg = f"Error clasificando: {str(e)}"
            print(f"X {error_msg}")
            self.classificationError.emit(error_msg)