import QtQuick
import QtQuick.Window
import Qt5Compat.GraphicalEffects
import QtQuick.Controls
import QtQuick.Controls.Fusion  // Importar el estilo Fusion
import "./views" as Views
import "./styles" as Styles


Window {
    width: 640
    height: 480
    visible: true
    title: qsTr("Sistema de Registro de Productos")

    property int currentView: 0
    property string registroActual: ""
    property string categoriaActual: ""

    Rectangle{
        id: main
        color: Styles.Style.backgroundColor
        // position
        anchors.fill: parent

        Views.ViewInitial{
            id: viewInitial
            visible: currentView===0

            onContinueClicked: {
                // Obtener el registro
                var registro = viewInitial.registroText.trim()
                var sinRegistro = viewInitial.noRegistroChecked

                if (sinRegistro) {
                    // Si no tiene registro, ir directamente a resultados
                    registroActual = ""
                    categoriaActual = "Sin registro sanitario"
                    console.log("Sin reg san")
                } else if (registro !== "") {
                    // ✅ Enviar a Python para clasificar
                    console.log(" Enviando a Python para clasificar:", registro)
                    registroActual = registro
                    categoriaActual = "Clasificando..."

                    // Llamar al método en Python
                    ProductClassifier.classify(registro)
                }

                currentView = 1
            }

        }

        // ========== VISTA DE DETALLE ==========
        Views.ViewProductDetail {
            id: viewProductDetail
            anchors.fill: parent
            visible: currentView === 1

            registro: registroActual
            categoria: categoriaActual

            onVolverClicked: {
                currentView = 0  // Volver a resultados
            }
        }

        Connections {
            target: ProductClassifier

            function onClassificationFinished(registro, categoria) {
                // Actualizar cuando Python termine
                console.log("Clasificación recibida:", categoria)
                categoriaActual = categoria
                // La vista ya se actualiza automáticamente por el binding
            }

            function onClassificationError(error) {
                console.error("Error en clasificación:", error)
                categoriaActual = "Error: " + error
            }
        }
    }
}