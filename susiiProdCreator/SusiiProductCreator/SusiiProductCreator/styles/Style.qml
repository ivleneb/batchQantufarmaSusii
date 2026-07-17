pragma Singleton
import QtQuick 2.15

QtObject {
    // Colores principales
    property color primaryColor: "#1e56a0"
    property color primaryHover: "#163d7a"
    readonly  property color backgroundColor: "#f0f2f5"
    property color inputBg: "#f8f9fc"
    property color borderColor: "#d1d9e6"
    property color textColor: "#333"
    property color textSecondary: "#64748b"
    property color white: "#ffffff"
    property color errorColor: "#e74c3c"
    property color successColor: "#2ecc71"
    property color warningColor: "#f39c12"
    property color placeHolderTextColor: "#888"

    // Tamaños
    property int radiusSmall: 5
    property int radiusMedium: 8
    property int radiusLarge: 10
    property int radiusRound: 15

    // Fuentes
    property int fontSizeSmall: 12
    property int fontSizeMedium: 14
    property int fontSizeLarge: 18
    property int fontSizeXLarge: 24
}