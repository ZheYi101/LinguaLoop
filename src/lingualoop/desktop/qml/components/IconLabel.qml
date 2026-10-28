import QtQuick
import QtQuick.Controls

ToolButton {
    property alias iconSource: control.icon.source
    property alias tint: control.icon.color
    id: control
    width: 32; height: 32
    icon.width: 24; icon.height: 24
    enabled: false
    opacity: 1
    background: Item {}
}
