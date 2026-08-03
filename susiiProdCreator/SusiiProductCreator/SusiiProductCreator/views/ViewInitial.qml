import QtQuick 2.15
import Qt5Compat.GraphicalEffects
import QtQuick.Controls
import QtQuick.Controls.Fusion  // Importar el estilo Fusion
import "../styles" as Styles

Column{

    id: root

    // Propiedades para acceder desde Main.qml
    property alias registroText: basicInput.text
    property alias noRegistroChecked: noRegSan.checked

    // Señal que se emite cuando se hace clic en Continuar
    signal continueClicked()

    anchors{
        left:parent.left
        right:parent.right
        top:parent.top
    }

    Rectangle{
        id: firstTitle
        width: 640
        height: 240
        // position
        color: "transparent"

        Rectangle{
            id: imageContainer
            width: 60
            height: 60
            radius: 10
            color: Styles.Style.primaryColor //"#1e56a0"
            // position
            anchors.top: parent.top
            anchors.topMargin: 30
            anchors.horizontalCenter: parent.horizontalCenter

            Image{
                id: icon
                source: "../../images/shield-check.svg"
                sourceSize.width: 50
                sourceSize.height: 50
                visible: false
                // position
                anchors.centerIn: parent

            }
            ColorOverlay {
                anchors.fill: icon
                source: icon
                color: "white"  // Convertir la imagen a blanco
            }
        }

        Rectangle{
            id: textContainer
            // position
            anchors.top: imageContainer.bottom
            anchors.topMargin: 30
            anchors.horizontalCenter: parent.horizontalCenter

            Text{
                id: text1
                // text
                text: "Verificación de Registro Sanitario"
                font.pixelSize: 24
                // position
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Text{
                id: text2
                // text
                text: "Ingrese numero de registro sanitario del producto"
                font.weight: Font.Light
                font.pixelSize: 15
                //position
                anchors.top:  text1.bottom
                anchors.horizontalCenter: parent.horizontalCenter
            }
        }
    }

    Rectangle{
        id: form1
        // Position
        anchors.horizontalCenter: parent.horizontalCenter
        height: 200
        width: 300
        border.color: Styles.Style.borderColor //"#d1d9e6"
        radius: 8

        Rectangle{
            id: regSanContainer
            // position
            height: 55
            width: 250
            anchors.top: parent.top
            anchors.margins: 10
            anchors.horizontalCenter: parent.horizontalCenter

            Column{

                anchors.fill: parent

                Rectangle{
                    width: 250
                    height: 20

                    Text{
                        text: "Registro Sanitario"
                    }
                }

                Rectangle {
                    id: textInputContainer
                    width: 250
                    height: 35
                    color: Styles.Style.inputBg // "#f8f9fc"
                    border.color: Styles.Style.borderColor // "#d1d9e6"
                    border.width: 1
                    radius: 5

                    TextInput {
                        id: basicInput
                        anchors.fill: parent
                        anchors.margins: 10
                        font.pixelSize: 14
                        selectByMouse: true

                        property string placeholderText: "DE-15446 o G4565454N"
                        Text {
                            text: parent.placeholderText
                            color: Styles.Style.placeHolderTextColor //"#888"
                            font.pixelSize: 14
                            visible: !parent.text && !parent.activeFocus
                            anchors.fill: parent
                        }

                    }
                }

                // Mensaje de error
                Text {
                    id: errorMessage
                    anchors.topMargin: 10
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: ""
                    color: Styles.Style.errorColor
                    font.pixelSize: 12
                    visible: false
                    //wrapMode: Text.WordWrap
                    width: 250
                    horizontalAlignment: Text.AlignHCenter
                }
            }
        }

        Rectangle{
            id: cbContainer
            // Position
            anchors.top: regSanContainer.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: 20
            width: 250
            height: 35

            Row{

                CheckBox {
                    id: noRegSan
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text{
                    text: "No tiene registro sanitario"
                    color: Styles.Style.textSecondary //"#64748b"
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }

        Rectangle {
            id: lineSeparator
            width: 250
            height: 1
            color:  Styles.Style.borderColor //"#d1d9e6"
            anchors.top: cbContainer.bottom
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Rectangle{
            id: btnContainer
            anchors.top: lineSeparator.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            width: 250
            height: 40
            anchors.topMargin: 20

            Button{
                id: btnContinue
                text: "Continuar"
                anchors.fill: parent
                background: Rectangle {
                    color: Styles.Style.primaryColor //"#1e56a0"
                    radius: 10
                    implicitWidth: 150
                    implicitHeight: 40

                    border.width: 0

                    // Animaciones
                    Behavior on color {
                        ColorAnimation { duration: 200 }
                    }

                    Behavior on scale {
                        NumberAnimation { duration: 200 }
                    }

                    scale: btnContinue.hovered ? 1.05 : 1.0  // hover:scale-105

                }

                contentItem: Text {
                    text: parent.text
                    color: "white"
                    font.pixelSize: 14
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                onClicked: {
                    var registro = basicInput.text.trim()
                    var checkboxMarcado = noRegSan.checked


                    // Validar: campo no vacío O checkbox marcado
                    if (registro !== "" || checkboxMarcado) {
                        errorMessage.visible = false
                        console.log("Validación correcta")
                        // Emitir señal para que Main.qml sepa que hay que cambiar de vista
                        root.continueClicked()
                    } else {
                        console.log("Error: Debe ingresar un registro o marcar 'No tiene registro sanitario'")
                        // Opcional: mostrar mensaje de error
                        errorMessage.text = "Ingresar un registro sanitario o marcar checkbox"
                        errorMessage.visible = true
                    }
                }
            }
        }
    }

}