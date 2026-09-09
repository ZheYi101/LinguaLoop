import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Dialogs as Dialogs
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
    property int currentPage: 0
    property bool compact: width < 600
    property bool showContext: width >= 900
    property string selectedImportPath: ""

    pageStack.initialPage: Kirigami.Page {
        title: "学习工作台"
        padding: 0
        actions: [
            Kirigami.Action {
                text: "重置当前状态"
                icon.name: "edit-clear"
                onTriggered: learningViewModel.resetSession()
            }
        ]

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                color: "#f8fafc"
                border.color: "#e5e7eb"
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 18
                    anchors.rightMargin: 18
                    Controls.Label { text: "LinguaLoop"; font.bold: true; font.pixelSize: 18 }
                    Controls.Label { text: learningViewModel.providerLabel; color: "#64748b" }
                    Item { Layout.fillWidth: true }
                    Controls.Label { text: "待复习 " + learningViewModel.dueReviewCount; color: "#0f766e"; font.bold: true }
                }
            }

            Controls.TabBar {
                visible: root.compact
                Layout.fillWidth: true
                currentIndex: root.currentPage
                onCurrentIndexChanged: root.currentPage = currentIndex
                Controls.TabButton { text: "材料" }
                Controls.TabButton { text: "练习" }
                Controls.TabButton { text: "复盘" }
                Controls.TabButton { text: "设置" }
            }

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                Layout.leftMargin: 14
                Layout.rightMargin: 14
                Layout.topMargin: 10
                text: learningViewModel.status
                type: Kirigami.MessageType.Information
                visible: text.length > 0
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.margins: 14
                spacing: 14

                Rectangle {
                    visible: !root.compact
                    Layout.preferredWidth: 178
                    Layout.fillHeight: true
                    radius: 8
                    color: "#111827"
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8
                        NavButton { text: "材料"; checked: root.currentPage === 0; onClicked: root.currentPage = 0 }
                        NavButton { text: "练习"; checked: root.currentPage === 1; onClicked: root.currentPage = 1 }
                        NavButton { text: "复盘 / 复习"; checked: root.currentPage === 2; onClicked: root.currentPage = 2 }
                        NavButton { text: "设置"; checked: root.currentPage === 3; onClicked: root.currentPage = 3 }
                        Item { Layout.fillHeight: true }
                        Controls.Label { text: "本地优先\nSQLite 持久化"; color: "#cbd5e1"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                    }
                }

                StackLayout {
                    currentIndex: root.currentPage
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    MaterialPage {}
                    PracticePage {}
                    ReviewPage {}
                    SettingsPage {}
                }

                ContextPanel {
                    visible: root.showContext
                    Layout.preferredWidth: 310
                    Layout.fillHeight: true
                }
            }
        }
    }

    Dialogs.FileDialog {
        id: fileDialog
        title: "导入学习材料"
        nameFilters: ["Learning materials (*.md *.markdown *.docx)"]
        onAccepted: root.selectedImportPath = selectedFile.toString()
    }

    Controls.Dialog {
        id: exportDialog
        title: "导出会话"
        modal: true
        standardButtons: Controls.Dialog.Ok | Controls.Dialog.Cancel
        contentItem: Controls.TextField { id: exportPath; width: 360; text: "lingualoop-session.json" }
        onAccepted: learningViewModel.exportSession(exportPath.text)
    }

    Controls.Dialog {
        id: errorDialog
        property string errorText: ""
        title: "操作失败"
        modal: true
        standardButtons: Controls.Dialog.Ok
        contentItem: Controls.Label { width: 360; text: errorDialog.errorText; wrapMode: Text.WordWrap }
    }

    Connections {
        target: learningViewModel
        function onErrorOccurred(message) { errorDialog.errorText = message; errorDialog.open() }
    }

    component NavButton: Controls.Button {
        Layout.fillWidth: true
        flat: true
        checkable: true
        font.bold: checked
    }

    component SectionTitle: Controls.Label {
        font.pixelSize: 22
        font.bold: true
        color: "#0f172a"
    }

    component MaterialPage: Controls.ScrollView {
        objectName: "materialScroll"
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 12
            SectionTitle { text: "材料" }
            Controls.Label { text: "导入或粘贴真实材料，先分析成可练习内容。"; color: "#475569"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            RowLayout {
                Layout.fillWidth: true
                Controls.TextField { Layout.fillWidth: true; placeholderText: "选择 .md / .markdown / .docx 文件"; text: root.selectedImportPath; onTextChanged: root.selectedImportPath = text }
                Controls.Button { text: "选择"; onClicked: fileDialog.open() }
                Controls.Button {
                    text: learningViewModel.busy ? "导入中" : "导入并分析"
                    enabled: !learningViewModel.busy && root.selectedImportPath.length > 0
                    onClicked: learningViewModel.importMaterial(root.selectedImportPath, sourceLanguage.currentText, targetLanguage.currentText, nativeLanguage.currentText, level.currentText, track.currentText)
                }
            }
            Controls.TextField { id: titleField; Layout.fillWidth: true; placeholderText: "材料标题"; text: learningViewModel.materialTitle || "市场购物" }
            GridLayout {
                Layout.fillWidth: true
                columns: root.compact ? 1 : 5
                Controls.ComboBox { id: sourceLanguage; Layout.fillWidth: true; model: ["english", "chinese", "japanese", "french", "spanish"]; currentIndex: 0 }
                Controls.ComboBox { id: targetLanguage; Layout.fillWidth: true; model: ["english", "chinese", "japanese", "french", "spanish"]; currentIndex: 0 }
                Controls.ComboBox { id: nativeLanguage; Layout.fillWidth: true; model: ["chinese", "english", "japanese", "french", "spanish"]; currentIndex: 0 }
                Controls.ComboBox { id: level; Layout.fillWidth: true; model: ["A1", "A2", "B1", "B2", "C1", "C2", "unknown"]; currentIndex: 1 }
                Controls.ComboBox { id: track; Layout.fillWidth: true; model: ["article_reading", "live_chat"]; currentIndex: 0 }
            }
            Controls.Label { text: "材料内容"; font.bold: true }
            Controls.TextArea {
                id: materialField
                Layout.fillWidth: true
                Layout.preferredHeight: 170
                placeholderText: "粘贴或输入学习材料"
                text: learningViewModel.materialContent || "Yesterday I went to the market and bought apples."
                wrapMode: TextEdit.Wrap
            }
            RowLayout {
                Layout.fillWidth: true
                Controls.Button {
                    Layout.fillWidth: true
                    text: learningViewModel.busy ? "处理中" : "分析材料"
                    enabled: !learningViewModel.busy
                    onClicked: learningViewModel.loadMaterial(titleField.text, materialField.text, sourceLanguage.currentText, targetLanguage.currentText, nativeLanguage.currentText, level.currentText)
                }
                Controls.Button {
                    Layout.fillWidth: true
                    text: "开始练习"
                    enabled: learningViewModel.hasMaterial && !learningViewModel.busy
                    onClicked: { learningViewModel.startPractice(); root.currentPage = 1 }
                }
            }
            Controls.Label { text: learningViewModel.materialSummary; visible: learningViewModel.hasMaterial; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }

    component PracticePage: Item {
        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            SectionTitle { text: "练习" }
            Controls.Label { text: learningViewModel.currentTask; wrapMode: Text.WordWrap; Layout.fillWidth: true; color: "#334155" }
            Controls.ScrollView {
                objectName: "practiceScroll"
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: availableWidth
                ColumnLayout {
                    width: parent.width
                    spacing: 10
                    Repeater {
                        model: learningViewModel.messages
                        delegate: Kirigami.AbstractCard {
                            required property var modelData
                            Layout.fillWidth: true
                            contentItem: Controls.Label { text: (modelData.role === "user" ? "我：" : "AI：") + modelData.content; wrapMode: Text.WordWrap }
                        }
                    }
                }
            }
            Controls.TextArea { id: messageField; Layout.fillWidth: true; Layout.preferredHeight: 95; placeholderText: "输入你的练习回答"; wrapMode: TextEdit.Wrap }
            Connections { target: learningViewModel; function onMessageSent() { messageField.text = "" } }
            RowLayout {
                Layout.fillWidth: true
                Controls.Button { Layout.fillWidth: true; text: learningViewModel.busy ? "等待回复" : "发送"; enabled: learningViewModel.hasSession && !learningViewModel.busy; onClicked: learningViewModel.sendMessage(messageField.text) }
                Controls.Button { Layout.fillWidth: true; text: "结束并复盘"; enabled: learningViewModel.hasSession && !learningViewModel.busy; onClicked: { learningViewModel.finishPractice(); root.currentPage = 2 } }
            }
        }
    }

    component ReviewPage: Controls.ScrollView {
        objectName: "reviewScroll"
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 12
            SectionTitle { text: "复盘 / 复习" }
            Controls.Label { text: learningViewModel.sessionSummary; wrapMode: Text.WordWrap; Layout.fillWidth: true; color: "#334155" }
            Controls.Label { text: "反馈"; font.bold: true }
            Repeater {
                model: learningViewModel.feedbackItems
                delegate: Kirigami.AbstractCard {
                    required property var modelData
                    Layout.fillWidth: true
                    contentItem: Controls.Label { text: modelData.original + " -> " + modelData.corrected + "\n" + modelData.explanation; wrapMode: Text.WordWrap }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Controls.Label { text: "复习项"; font.bold: true }
                Item { Layout.fillWidth: true }
                Controls.Button { text: "导出 JSON"; onClicked: exportDialog.open() }
            }
            Repeater {
                model: learningViewModel.reviewItems
                delegate: Kirigami.AbstractCard {
                    required property var modelData
                    Layout.fillWidth: true
                    contentItem: ColumnLayout {
                        Controls.Label { text: modelData.context; visible: modelData.context.length > 0; wrapMode: Text.WordWrap; color: "#64748b"; Layout.fillWidth: true }
                        Controls.Label { text: modelData.prompt; wrapMode: Text.WordWrap; Layout.fillWidth: true; font.bold: true }
                        Controls.TextArea { id: reviewAnswer; Layout.fillWidth: true; Layout.preferredHeight: 60; placeholderText: "先尝试回答，再记录结果"; wrapMode: TextEdit.Wrap }
                        Controls.Label { text: "答案：" + modelData.answer; wrapMode: Text.WordWrap; Layout.fillWidth: true; color: "#475569" }
                        RowLayout {
                            Layout.fillWidth: true
                            Controls.Button { text: "Again"; onClicked: learningViewModel.reviewOutcome(modelData.id, "again", reviewAnswer.text) }
                            Controls.Button { text: "Hard"; onClicked: learningViewModel.reviewOutcome(modelData.id, "hard", reviewAnswer.text) }
                            Controls.Button { text: "Good"; onClicked: learningViewModel.reviewOutcome(modelData.id, "good", reviewAnswer.text) }
                            Controls.Button { text: "Easy"; onClicked: learningViewModel.reviewOutcome(modelData.id, "easy", reviewAnswer.text) }
                            Item { Layout.fillWidth: true }
                            Controls.Button { text: "暂停"; onClicked: learningViewModel.updateReviewStatus(modelData.id, "paused") }
                            Controls.Button { text: "忽略"; onClicked: learningViewModel.updateReviewStatus(modelData.id, "ignored") }
                            Controls.Button { text: "归档"; onClicked: learningViewModel.updateReviewStatus(modelData.id, "archived") }
                            Controls.Button { text: "删除"; onClicked: learningViewModel.updateReviewStatus(modelData.id, "deleted") }
                        }
                    }
                }
            }
        }
    }

    component SettingsPage: Controls.ScrollView {
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 12
            SectionTitle { text: "设置" }
            Controls.Label { text: "当前只支持真实 provider 桌面模式。离线 mock 保留给 CLI、测试和显式调试。"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            Controls.Label { text: "数据目录可用 LINGUALOOP_DATA_DIR 覆盖。"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }

    component ContextPanel: Rectangle {
        radius: 8
        color: "#f8fafc"
        border.color: "#e5e7eb"
        Controls.ScrollView {
            anchors.fill: parent
            anchors.margins: 12
            clip: true
            contentWidth: availableWidth
            ColumnLayout {
                width: parent.width
                spacing: 12
                Controls.Label { text: "上下文"; font.bold: true; font.pixelSize: 18 }
                Controls.Label { text: learningViewModel.materialSummary; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Controls.Label { text: "当前任务"; font.bold: true }
                Controls.Label { text: learningViewModel.currentTask; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Controls.Label { text: "待复习 " + learningViewModel.dueReviewCount; font.bold: true; color: "#0f766e" }
                Repeater {
                    model: learningViewModel.reviewItems.slice(0, 3)
                    delegate: Controls.Label { required property var modelData; text: "- " + modelData.prompt; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
            }
        }
    }
}
