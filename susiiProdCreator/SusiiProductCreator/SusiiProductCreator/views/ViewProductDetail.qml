// views/ViewProductDetail.qml
import QtQuick
import QtQuick.Controls
import "../styles" as Styles

Rectangle {
    id: root
    color: Styles.Style.backgroundColor

    // Propiedades que recibe desde Main.qml
    property string registro: ""
    property string categoria: ""

    // Señales
    signal volverClicked()

    Column {
        anchors.centerIn: parent
        spacing: 20
        width: 400

        // Título
        Text {
            text: "Detalle del Producto"
            font.pixelSize: 22
            font.bold: true
            color: Styles.Style.primaryColor
            anchors.horizontalCenter: parent.horizontalCenter
        }

        // Mostrar registro
        Rectangle {
            width: parent.width
            height: 50
            color: Styles.Style.inputBg
            radius: 8
            border.color: Styles.Style.borderColor
            border.width: 1

            Row {
                anchors.centerIn: parent
                spacing: 10

                Text {
                    text: "Registro:"
                    font.bold: true
                    font.pixelSize: 14
                }

                Text {
                    text: registro
                    font.pixelSize: 14
                    color: Styles.Style.primaryColor
                }
            }
        }

        // Mostrar categoría
        Rectangle {
            width: parent.width
            height: 50
            color: Styles.Style.primaryColor
            radius: 8

            Text {
                text: categoria
                anchors.centerIn: parent
                color: Styles.Style.white
                font.pixelSize: 16
                font.bold: true
            }
        }

        // Separador
        Rectangle {
            width: parent.width
            height: 1
            color: Styles.Style.borderColor
        }

        // Aquí irán más campos de detalle
        Text {
            text: "Detalles adicionales (próximamente)"
            font.pixelSize: 14
            color: Styles.Style.textSecondary
            anchors.horizontalCenter: parent.horizontalCenter
        }

        // Botón volver
        Button {
            text: "Volver"
            anchors.horizontalCenter: parent.horizontalCenter
            width: 150
            height: 40

            background: Rectangle {
                color: Styles.Style.primaryColor
                radius: 10
                implicitWidth: 150
                implicitHeight: 40
            }

            contentItem: Text {
                text: parent.text
                color: Styles.Style.white
                font.pixelSize: 14
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            onClicked: root.volverClicked()
        }

        Rectangle{
            id: generalInfo
            width: parent.width
            height: 240
            color: "blue" //Styles.Style.backgroundColor
        }

        Rectangle{
            id: farmaInfo
            width: parent.width
            height: 240
            color: "red" //Styles.Style.backgroundColor
        }


    }
}