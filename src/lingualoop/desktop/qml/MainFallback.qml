import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1180
    height: 780
    minimumWidth: 360
    minimumHeight: 560
    visible: true
    title: "LinguaLoop"

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16
            anchors.rightMargin: 8
            Label { text: "LinguaLoop"; font.bold: true }
            Label { text: learningViewModel.providerLabel; color: "#4b5563" }
            Item { Layout.fillWidth: true }
            ToolButton { text: "重置"; onClicked: learningViewModel.resetSession() }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Label {
            Layout.fillWidth: true
            text: learningViewModel.status
            visible: text.length > 0
            wrapMode: Text.WordWrap
            color: "#1f2937"
        }

        TabBar {
            id: tabs
            Layout.fillWidth: true
            TabButton { text: "材料" }
            TabButton { text: "练习" }
            TabButton { text: "复盘" }
        }

        StackLayout {
            currentIndex: tabs.currentIndex
            Layout.fillWidth: true
            Layout.fillHeight: true

            ScrollView {
                objectName: "materialScroll"
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label { text: "学习材料"; font.pixelSize: 24; font.bold: true }
                    Label { text: "输入真实材料，生成适合你的练习。"; Layout.fillWidth: true; wrapMode: Text.WordWrap }
                    TextField { id: titleField; Layout.fillWidth: true; placeholderText: "材料标题"; text: "市场购物" }
                    ComboBox { id: sourceLanguage; Layout.fillWidth: true; model: ["english", "chinese", "japanese", "french", "spanish"] }
                    ComboBox { id: targetLanguage; Layout.fillWidth: true; model: ["english", "chinese", "japanese", "french", "spanish"] }
                    ComboBox { id: nativeLanguage; Layout.fillWidth: true; model: ["chinese", "english", "japanese", "french", "spanish"] }
                    ComboBox { id: level; Layout.fillWidth: true; model: ["A1", "A2", "B1", "B2", "C1", "C2"]; currentIndex: 1 }
                    Label { text: "材料内容" }
                    TextArea {
                        id: materialField
                        Layout.fillWidth: true
                        Layout.preferredHeight: 180
                        placeholderText: "粘贴或输入学习材料"
                        text: "Yesterday I went to the market and bought apples."
                        wrapMode: TextEdit.Wrap
                    }
                    Button {
                        Layout.fillWidth: true
                        text: learningViewModel.busy ? "处理中..." : "分析材料"
                        enabled: !learningViewModel.busy
                        onClicked: learningViewModel.loadMaterial(titleField.text, materialField.text, sourceLanguage.currentText, targetLanguage.currentText, nativeLanguage.currentText, level.currentText)
                    }
                    Label {
                        Layout.fillWidth: true
                        visible: learningViewModel.hasMaterial
                        text: learningViewModel.materialSummary
                        wrapMode: Text.WordWrap
                    }
                    Button {
                        Layout.fillWidth: true
                        text: "开始练习"
                        enabled: learningViewModel.hasMaterial && !learningViewModel.busy
                        onClicked: { learningViewModel.startPractice(); tabs.currentIndex = 1 }
                    }
                }
            }

            ScrollView {
                objectName: "practiceScroll"
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label { text: "练习"; font.pixelSize: 24; font.bold: true }
                    Label { text: "当前任务"; font.bold: true }
                    Label { Layout.fillWidth: true; text: learningViewModel.currentTask; wrapMode: Text.WordWrap }
                    Label { text: "对话记录"; font.bold: true }
                    Repeater {
                        model: learningViewModel.messages
                        delegate: Frame {
                            required property var modelData
                            Layout.fillWidth: true
                            Label {
                                width: parent.width
                                text: (parent.modelData.role === "user" ? "我：" : "AI：") + parent.modelData.content
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                    TextArea {
                        id: messageField
                        Layout.fillWidth: true
                        Layout.preferredHeight: 120
                        placeholderText: "输入你的练习回答"
                        wrapMode: TextEdit.Wrap
                    }
                    Button {
                        Layout.fillWidth: true
                        text: learningViewModel.busy ? "等待 AI 回复..." : "发送"
                        enabled: learningViewModel.hasSession && !learningViewModel.busy
                        onClicked: { learningViewModel.sendMessage(messageField.text); messageField.text = "" }
                    }
                    Button { Layout.fillWidth: true; text: "查看复盘"; onClicked: tabs.currentIndex = 2 }
                }
            }

            ScrollView {
                objectName: "reviewScroll"
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 12

                    Label { text: "复盘"; font.pixelSize: 24; font.bold: true }
                    Label { Layout.fillWidth: true; text: learningViewModel.sessionSummary; wrapMode: Text.WordWrap }
                    Label { text: "反馈"; font.bold: true }
                    Repeater {
                        model: learningViewModel.feedbackItems
                        delegate: Frame {
                            required property var modelData
                            Layout.fillWidth: true
                            Label {
                                width: parent.width
                                text: parent.modelData.original + " -> " + parent.modelData.corrected + "\n" + parent.modelData.explanation
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                    Label { text: "复习项"; font.bold: true }
                    Repeater {
                        model: learningViewModel.reviewItems
                        delegate: Frame {
                            required property var modelData
                            Layout.fillWidth: true
                            Label {
                                width: parent.width
                                text: parent.modelData.prompt + "\n答案：" + parent.modelData.answer
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                    Button { Layout.fillWidth: true; text: "导出会话"; onClicked: exportDialog.open() }
                }
            }
        }
    }

    Dialog {
        id: exportDialog
        title: "导出会话"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok | Dialog.Cancel
        contentItem: TextField {
            id: exportPath
            width: 320
            placeholderText: "导出文件路径"
            text: "lingualoop-session.json"
        }
        onAccepted: learningViewModel.exportSession(exportPath.text)
    }

    Dialog {
        id: errorDialog
        property string errorText: ""
        title: "操作失败"
        modal: true
        anchors.centerIn: parent
        standardButtons: Dialog.Ok
        contentItem: Label { width: 320; text: errorDialog.errorText; wrapMode: Text.WordWrap }
    }

    Connections {
        target: learningViewModel
        function onErrorOccurred(message) { errorDialog.errorText = message; errorDialog.open() }
    }
}
