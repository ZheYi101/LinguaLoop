import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import "../design"

ToolButton {
    property string symbol: "info"
    property string label: ""
    implicitWidth: AppTheme.touchTarget
    implicitHeight: AppTheme.touchTarget
    icon.source: Qt.resolvedUrl("../assets/" + symbol + ".svg")
    icon.width: 24
    icon.height: 24
    icon.color: AppTheme.colorOnSurface
    Accessible.name: label
    ToolTip.visible: hovered
    ToolTip.text: label
    Material.roundedScale: Material.FullScale
}
