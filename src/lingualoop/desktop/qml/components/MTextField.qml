import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import "../design"

TextField {
    implicitHeight: 64
    font.family: AppTheme.uiFont
    font.pixelSize: AppTheme.bodyLarge
    color: AppTheme.colorOnSurface
    placeholderTextColor: AppTheme.colorOnSurfaceVariant
    selectByMouse: true
    Material.containerStyle: Material.Outlined
    Material.accent: AppTheme.primary
    Accessible.name: placeholderText
}
