import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs as Dialogs
import QtQuick.Layouts

ApplicationWindow {
    id: root
    width: 1180
    height: 780
    minimumWidth: 360
    minimumHeight: 560
    visible: true
    title: "LinguaLoop"
    property int currentPage: 0
    property bool compact: width < 600
    property bool showContext: width >= 900
    property string selectedImportPath: ""

    header: ToolBar {
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            Label { text: "LinguaLoop"; font.bold: true; font.pixelSize: 18 }
            Label { text: learningViewModel.providerLabel; color: "#64748b" }
            Item { Layout.fillWidth: true }
            Label { text: "待复习 " + learningViewModel.dueReviewCount; color: "#0f766e"; font.bold: true }
            ToolButton { text: "重置"; onClicked: learningViewModel.resetSession() }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        TabBar {
            visible: root.compact
            Layout.fillWidth: true
            currentIndex: root.currentPage
            onCurrentIndexChanged: root.currentPage = currentIndex
            TabButton { text: "材料" }
            TabButton { text: "练习" }
            TabButton { text: "复盘" }
            TabButton { text: "设置" }
        }

        Label { Layout.fillWidth: true; text: learningViewModel.status; wrapMode: Text.WordWrap; color: "#1f2937" }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
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
                    Label { text: "本地优先\nSQLite 持久化"; color: "#cbd5e1"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
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

            ContextPanel { visible: root.showContext; Layout.preferredWidth: 310; Layout.fillHeight: true }
        }
    }

    Dialogs.FileDialog {
        id: fileDialog
        title: "导入学习材料"
        nameFilters: ["Learning materials (*.md *.markdown *.docx)"]
        onAccepted: root.selectedImportPath = selectedFile.toString()
    }

    Dialog {
        id: exportDialog
        title: "导出会话"
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        contentItem: TextField { id: exportPath; width: 360; text: "lingualoop-session.json" }
        onAccepted: learningViewModel.exportSession(exportPath.text)
    }

    Dialog {
        id: errorDialog
        property string errorText: ""
        title: "操作失败"
        modal: true
        standardButtons: Dialog.Ok
        contentItem: Label { width: 360; text: errorDialog.errorText; wrapMode: Text.WordWrap }
    }

    Connections {
        target: learningViewModel
        function onErrorOccurred(message) { errorDialog.errorText = message; errorDialog.open() }
    }

    component NavButton: Button { Layout.fillWidth: true; flat: true; checkable: true; font.bold: checked }
    component SectionTitle: Label { font.pixelSize: 22; font.bold: true; color: "#0f172a" }

    component MaterialPage: ScrollView {
        objectName: "materialScroll"
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 12
            SectionTitle { text: "材料" }
            Label { text: "导入或粘贴真实材料，先分析成可练习内容。"; color: "#475569"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            RowLayout {
                Layout.fillWidth: true
                TextField { Layout.fillWidth: true; placeholderText: "选择 .md / .markdown / .docx 文件"; text: root.selectedImportPath; onTextChanged: root.selectedImportPath = text }
                Button { text: "选择"; onClicked: fileDialog.open() }
                Button {
                    text: learningViewModel.busy ? "导入中" : "导入并分析"
                    enabled: !learningViewModel.busy && root.selectedImportPath.length > 0
                    onClicked: learningViewModel.importMaterial(root.selectedImportPath, sourceLanguage.currentText, targetLanguage.currentText, nativeLanguage.currentText, level.currentText, track.currentText)
                }
            }
            TextField { id: titleField; Layout.fillWidth: true; placeholderText: "材料标题"; text: learningViewModel.materialTitle || "市场购物" }
            GridLayout {
                Layout.fillWidth: true
                columns: root.compact ? 1 : 5
                ComboBox { id: sourceLanguage; Layout.fillWidth: true; model: ["english", "chinese", "japanese", "french", "spanish"]; currentIndex: 0 }
                ComboBox { id: targetLanguage; Layout.fillWidth: true; model: ["english", "chinese", "japanese", "french", "spanish"]; currentIndex: 0 }
                ComboBox { id: nativeLanguage; Layout.fillWidth: true; model: ["chinese", "english", "japanese", "french", "spanish"]; currentIndex: 0 }
                ComboBox { id: level; Layout.fillWidth: true; model: ["A1", "A2", "B1", "B2", "C1", "C2", "unknown"]; currentIndex: 1 }
                ComboBox { id: track; Layout.fillWidth: true; model: ["article_reading", "live_chat"]; currentIndex: 0 }
            }
            Label { text: "材料内容"; font.bold: true }
            TextArea {
                id: materialField
                Layout.fillWidth: true
                Layout.preferredHeight: 170
                placeholderText: "粘贴或输入学习材料"
                text: learningViewModel.materialContent || "Yesterday I went to the market and bought apples."
                wrapMode: TextEdit.Wrap
            }
            RowLayout {
                Layout.fillWidth: true
                Button {
                    Layout.fillWidth: true
                    text: learningViewModel.busy ? "处理中" : "分析材料"
                    enabled: !learningViewModel.busy
                    onClicked: learningViewModel.loadMaterial(titleField.text, materialField.text, sourceLanguage.currentText, targetLanguage.currentText, nativeLanguage.currentText, level.currentText)
                }
                Button {
                    Layout.fillWidth: true
                    text: "开始练习"
                    enabled: learningViewModel.hasMaterial && !learningViewModel.busy
                    onClicked: { learningViewModel.startPractice(); root.currentPage = 1 }
                }
            }
            Label { text: learningViewModel.materialSummary; visible: learningViewModel.hasMaterial; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }

    component PracticePage: Item {
        ColumnLayout {
            anchors.fill: parent
            spacing: 10
            SectionTitle { text: "练习" }
            Label { text: learningViewModel.currentTask; wrapMode: Text.WordWrap; Layout.fillWidth: true; color: "#334155" }
            ScrollView {
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
                        delegate: Frame {
                            required property var modelData
                            Layout.fillWidth: true
                            Label { width: parent.width; text: (modelData.role === "user" ? "我：" : "AI：") + modelData.content; wrapMode: Text.WordWrap }
                        }
                    }
                }
            }
            TextArea { id: messageField; Layout.fillWidth: true; Layout.preferredHeight: 95; placeholderText: "输入你的练习回答"; wrapMode: TextEdit.Wrap }
            Connections { target: learningViewModel; function onMessageSent() { messageField.text = "" } }
            RowLayout {
                Layout.fillWidth: true
                Button { Layout.fillWidth: true; text: learningViewModel.busy ? "等待回复" : "发送"; enabled: learningViewModel.hasSession && !learningViewModel.busy; onClicked: learningViewModel.sendMessage(messageField.text) }
                Button { Layout.fillWidth: true; text: "结束并复盘"; enabled: learningViewModel.hasSession && !learningViewModel.busy; onClicked: { learningViewModel.finishPractice(); root.currentPage = 2 } }
            }
        }
    }

    component ReviewPage: ScrollView {
        objectName: "reviewScroll"
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 12
            SectionTitle { text: "复盘 / 复习" }
            Label { text: learningViewModel.sessionSummary; wrapMode: Text.WordWrap; Layout.fillWidth: true; color: "#334155" }
            Label { text: "反馈"; font.bold: true }
            Repeater {
                model: learningViewModel.feedbackItems
                delegate: Frame {
                    required property var modelData
                    Layout.fillWidth: true
                    Label { width: parent.width; text: modelData.original + " -> " + modelData.corrected + "\n" + modelData.explanation; wrapMode: Text.WordWrap }
                }
            }
            RowLayout {
                Layout.fillWidth: true
                Label { text: "复习项"; font.bold: true }
                Item { Layout.fillWidth: true }
                Button { text: "导出 JSON"; onClicked: exportDialog.open() }
            }
            Repeater {
                model: learningViewModel.reviewItems
                delegate: Frame {
                    required property var modelData
                    Layout.fillWidth: true
                    ColumnLayout {
                        width: parent.width
                        Label { text: modelData.context; visible: modelData.context.length > 0; wrapMode: Text.WordWrap; color: "#64748b"; Layout.fillWidth: true }
                        Label { text: modelData.prompt; wrapMode: Text.WordWrap; Layout.fillWidth: true; font.bold: true }
                        TextArea { id: reviewAnswer; Layout.fillWidth: true; Layout.preferredHeight: 60; placeholderText: "先尝试回答，再记录结果"; wrapMode: TextEdit.Wrap }
                        Label { text: "答案：" + modelData.answer; wrapMode: Text.WordWrap; Layout.fillWidth: true; color: "#475569" }
                        RowLayout {
                            Layout.fillWidth: true
                            Button { text: "Again"; onClicked: learningViewModel.reviewOutcome(modelData.id, "again", reviewAnswer.text) }
                            Button { text: "Hard"; onClicked: learningViewModel.reviewOutcome(modelData.id, "hard", reviewAnswer.text) }
                            Button { text: "Good"; onClicked: learningViewModel.reviewOutcome(modelData.id, "good", reviewAnswer.text) }
                            Button { text: "Easy"; onClicked: learningViewModel.reviewOutcome(modelData.id, "easy", reviewAnswer.text) }
                            Item { Layout.fillWidth: true }
                            Button { text: "暂停"; onClicked: learningViewModel.updateReviewStatus(modelData.id, "paused") }
                            Button { text: "忽略"; onClicked: learningViewModel.updateReviewStatus(modelData.id, "ignored") }
                            Button { text: "归档"; onClicked: learningViewModel.updateReviewStatus(modelData.id, "archived") }
                            Button { text: "删除"; onClicked: learningViewModel.updateReviewStatus(modelData.id, "deleted") }
                        }
                    }
                }
            }
        }
    }

    component SettingsPage: ScrollView {
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: parent.width
            spacing: 12
            SectionTitle { text: "设置" }
            Label { text: "当前只支持真实 provider 桌面模式。离线 mock 保留给 CLI、测试和显式调试。"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
            Label { text: "数据目录可用 LINGUALOOP_DATA_DIR 覆盖。"; wrapMode: Text.WordWrap; Layout.fillWidth: true }
        }
    }

    component ContextPanel: Rectangle {
        radius: 8
        color: "#f8fafc"
        border.color: "#e5e7eb"
        ScrollView {
            anchors.fill: parent
            anchors.margins: 12
            clip: true
            contentWidth: availableWidth
            ColumnLayout {
                width: parent.width
                spacing: 12
                Label { text: "上下文"; font.bold: true; font.pixelSize: 18 }
                Label { text: learningViewModel.materialSummary; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Label { text: "当前任务"; font.bold: true }
                Label { text: learningViewModel.currentTask; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                Label { text: "待复习 " + learningViewModel.dueReviewCount; font.bold: true; color: "#0f766e" }
                Repeater {
                    model: learningViewModel.reviewItems.slice(0, 3)
                    delegate: Label { required property var modelData; text: "- " + modelData.prompt; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                }
            }
        }
    }
}
