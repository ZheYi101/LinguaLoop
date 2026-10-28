import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../design"

ColumnLayout {
    id: root
    property string label: ""
    property string preferenceKey: ""
    property var choices: []
    property var values: []
    Layout.fillWidth: true
    MLabel { text: root.label; role: "label" }
    ComboBox {
        Layout.fillWidth: true
        implicitHeight: 48
        model: root.choices
        Accessible.name: root.label
        currentIndex: Math.max(0, root.values.indexOf(learningViewModel.preferences[root.preferenceKey]))
        onActivated: learningViewModel.preferences.setValue(root.preferenceKey, root.values[currentIndex])
    }
}
