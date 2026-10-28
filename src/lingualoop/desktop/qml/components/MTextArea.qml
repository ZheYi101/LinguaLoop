import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import "../design"

TextArea {
    implicitHeight: 120
    wrapMode: TextEdit.Wrap
    selectByMouse: true
    font.family: AppTheme.uiFont
    font.pixelSize: AppTheme.bodyLarge
    color: AppTheme.colorOnSurface
    placeholderTextColor: AppTheme.colorOnSurfaceVariant
    Material.containerStyle: Material.Outlined
    Material.accent: AppTheme.primary
    Accessible.name: placeholderText
}
