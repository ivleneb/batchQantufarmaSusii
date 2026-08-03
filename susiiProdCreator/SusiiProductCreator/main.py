# This Python file uses the following encoding: utf-8
import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from ProductClassifier import ProductClassifier


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.addImportPath(Path(__file__).parent)

    classifier = ProductClassifier()

    # Exponer el clasificador a QML como contexto global
    engine.rootContext().setContextProperty("ProductClassifier", classifier)

    engine.loadFromModule("SusiiProductCreator", "Main")
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())
