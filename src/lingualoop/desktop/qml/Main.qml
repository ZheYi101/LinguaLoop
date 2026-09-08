import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root
    visible: true
    width: 1180
    height: 780
    minimumWidth: 360
    minimumHeight: 560
    title: "LinguaLoop"

    pageStack.initialPage: Kirigami.Page {
        id: page
        title: "学习工作台"
        padding: Kirigami.Units.largeSpacing
        actions: [Kirigami.Action { text: "重置"
 icon.name: "edit-clear"
 onTriggered: learningViewModel.resetSession() }]

        ColumnLayout {
            anchors.fill: parent
            spacing: Kirigami.Units.largeSpacing
            Kirigami.InlineMessage {
                Layout.fillWidth: true
                text: learningViewModel.status
                type: Kirigami.MessageType.Information
                visible: text.length > 0
            }
            Controls.TabBar {
                id: tabs
                Layout.fillWidth: true
                Controls.TabButton { text: "材料" }
                Controls.TabButton { text: "练习" }
                Controls.TabButton { text: "复盘" }
            }
            Controls.StackLayout {
                currentIndex: tabs.currentIndex
                Layout.fillWidth: true
                Layout.fillHeight: true
                Flickable {
                    contentHeight: materialColumn.height
                    clip: true
                    Controls.ScrollBar.vertical: Controls.ScrollBar {}
                    ColumnLayout {
                        id: materialColumn
                        width: parent.width
                        spacing: Kirigami.Units.largeSpacing
                        Controls.Label { text: "学习材料"
 font.bold: true
 font.pixelSize: 24 }
                        Controls.Label { text: "输入真实材料，生成适合你的练习。"
 wrapMode: Text.WordWrap
 Layout.fillWidth: true }
                        Controls.TextField { id: titleField
 Layout.fillWidth: true
 placeholderText: "材料标题"
 text: "市场购物" }
                        Controls.ComboBox { id: sourceLanguage
 Layout.fillWidth: true
 model: ["english", "chinese", "japanese", "french", "spanish"]
 currentIndex: 0 }
                        Controls.ComboBox { id: targetLanguage
 Layout.fillWidth: true
 model: ["english", "chinese", "japanese", "french", "spanish"]
 currentIndex: 0 }
                        Controls.ComboBox { id: nativeLanguage
 Layout.fillWidth: true
 model: ["chinese", "english", "japanese", "french", "spanish"]
 currentIndex: 0 }
                        Controls.ComboBox { id: level
 Layout.fillWidth: true
 model: ["A1", "A2", "B1", "B2", "C1", "C2"]
 currentIndex: 1 }
                        Controls.Label { text: "材料内容" }
                        Controls.TextArea { id: materialField
 Layout.fillWidth: true
 Layout.preferredHeight: 180
 placeholderText: "粘贴或输入学习材料"
 text: "Yesterday I went to the market and bought apples."
 wrapMode: TextEdit.Wrap }
                        Controls.Button {
                            Layout.fillWidth: true
                            text: learningViewModel.busy ? "处理中..." : "分析材料"
                            enabled: !learningViewModel.busy
                            onClicked: learningViewModel.loadMaterial(titleField.text, materialField.text, sourceLanguage.currentText, targetLanguage.currentText, nativeLanguage.currentText, level.currentText)
                        }
                        Controls.Label { text: learningViewModel.materialSummary
 wrapMode: Text.WordWrap
 Layout.fillWidth: true
 visible: learningViewModel.hasMaterial }
                        Controls.Button { Layout.fillWidth: true
 text: "开始练习"
 enabled: learningViewModel.hasMaterial && !learningViewModel.busy
 onClicked: { learningViewModel.startPractice()
 tabs.currentIndex = 1 } }
                    }
                }
                Flickable {
                    contentHeight: practiceColumn.height
                    clip: true
                    Controls.ScrollBar.vertical: Controls.ScrollBar {}
                    ColumnLayout {
                        id: practiceColumn
                        width: parent.width
                        spacing: Kirigami.Units.largeSpacing
                        Controls.Label { text: "练习"
 font.bold: true
 font.pixelSize: 24 }
                        Controls.Label { text: "当前任务"
 font.bold: true }
                        Controls.Label { text: learningViewModel.currentTask
 wrapMode: Text.WordWrap
 Layout.fillWidth: true }
                        Controls.Label { text: "对话记录"
 font.bold: true }
                        Repeater {
                            model: learningViewModel.messages
                            delegate: Kirigami.AbstractCard {
                                Layout.fillWidth: true
                                contentItem: Controls.Label { text: (modelData.role === "user" ? "我：" : "AI：") + modelData.content
 wrapMode: Text.WordWrap }
                            }
                        }
                        Controls.TextArea { id: messageField
 Layout.fillWidth: true
 Layout.preferredHeight: 120
 placeholderText: "输入你的练习回答"
 wrapMode: TextEdit.Wrap }
                        Controls.Button { Layout.fillWidth: true
 text: learningViewModel.busy ? "等待 AI 回复..." : "发送"
 enabled: learningViewModel.hasSession && !learningViewModel.busy
 onClicked: { learningViewModel.sendMessage(messageField.text)
 messageField.text = "" } }
                        Controls.Button { Layout.fillWidth: true
 text: "查看复盘"
 onClicked: tabs.currentIndex = 2 }
                    }
                }
                Flickable {
                    contentHeight: reviewColumn.height
                    clip: true
                    Controls.ScrollBar.vertical: Controls.ScrollBar {}
                    ColumnLayout {
                        id: reviewColumn
                        width: parent.width
                        spacing: Kirigami.Units.largeSpacing
                        Controls.Label { text: "复盘"
 font.bold: true
 font.pixelSize: 24 }
                        Controls.Label { text: learningViewModel.sessionSummary
 wrapMode: Text.WordWrap
 Layout.fillWidth: true }
                        Controls.Label { text: "反馈"
 font.bold: true }
                        Repeater { model: learningViewModel.feedbackItems
 delegate: Kirigami.AbstractCard { Layout.fillWidth: true
 contentItem: Controls.Label { text: modelData.original + " -> " + modelData.corrected + "\n" + modelData.explanation
 wrapMode: Text.WordWrap } } }
                        Controls.Label { text: "复习项"
 font.bold: true }
                        Repeater { model: learningViewModel.reviewItems
 delegate: Kirigami.AbstractCard { Layout.fillWidth: true
 contentItem: Controls.Label { text: modelData.prompt + "\n答案：" + modelData.answer
 wrapMode: Text.WordWrap } } }
                        Controls.Button { Layout.fillWidth: true
 text: "导出会话"
 onClicked: exportDialog.open() }
                    }
                }
            }
        }
        Kirigami.Dialog {
            id: exportDialog
            title: "导出会话"
            standardButtons: Controls.Dialog.Ok | Controls.Dialog.Cancel
            Controls.TextField { id: exportPath
 width: 360
 text: "lingualoop-session.json"
 placeholderText: "导出文件路径" }
            onAccepted: learningViewModel.exportSession(exportPath.text)
        }
        Controls.Dialog {
            id: errorDialog
            property string errorText: ""
            title: "操作失败"
            standardButtons: Controls.Dialog.Ok
            Controls.Label { text: errorDialog.errorText
 wrapMode: Text.WordWrap
 width: 360 }
        }
        Connections { target: learningViewModel
 function onErrorOccurred(message) { errorDialog.errorText = message
 errorDialog.open() } }
    }
}
