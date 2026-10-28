import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs as Dialogs
import "../design"
import "../components"

Item {
    id: page
    signal navigate(int page)
    property bool editing: false
    property bool showSource: false
    property bool showStructure: false
    property bool normalized: true
    property bool optionsExpanded: false
    property bool showFullSummary: false
    ColumnLayout {
        anchors.fill: parent
        spacing: AppTheme.sectionGap
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                Layout.fillWidth: true
                MLabel { text: "材料"; role: "headline" }
                MLabel { visible: page.width > 500; text: "把沉浸中的故事，变成下一次想聊的话题。"; role: "supporting" }
            }
            MButton { text: "导入"; objectName: "importButton"; enabled: !learningViewModel.busy; onClicked: fileDialog.open() }
            MButton { text: "粘贴"; variant: "tonal"; onClicked: page.editing = !page.editing }
        }
        ScrollView {
            id: materialScroll
            objectName: "materialScroll"
            Layout.fillWidth: true; Layout.fillHeight: true
            clip: true
            contentWidth: availableWidth
            ColumnLayout {
                width: materialScroll.availableWidth
                spacing: AppTheme.sectionGap
                MCard {
                    visible: learningViewModel.materials.length === 0 && !page.editing
                    MLabel { text: "从你喜欢的一段内容开始"; role: "title" }
                    MLabel { text: "小说、文章、字幕或已有转写。导入后，AI 会先整理内容和可聊的方向。"; role: "supporting" }
                    MButton { text: "粘贴一段内容"; variant: "tonal"; onClicked: page.editing = true }
                }
                MCard {
                    visible: page.editing
                    MLabel { text: "粘贴内容"; role: "title" }
                    MTextField { id: titleField; objectName: "materialTitleInput"; Layout.fillWidth: true; placeholderText: "材料标题" }
                    MTextArea { id: materialField; objectName: "materialTextInput"; Layout.fillWidth: true; Layout.preferredHeight: 160; placeholderText: "本次已看过的内容" }
                    MLabel { text: "先保存原文，再分段整理。分析失败时，已完成的部分仍会保留。"; role: "supporting" }
                    MButton {
                        text: learningViewModel.busy ? "正在整理…" : "保存并整理"
                        objectName: "saveMaterialButton"
                        enabled: !learningViewModel.busy && titleField.text.trim().length > 0 && materialField.text.trim().length > 0
                        onClicked: learningViewModel.loadMaterial(titleField.text, materialField.text,
                            learningViewModel.preferences.targetLanguage, learningViewModel.preferences.targetLanguage,
                            learningViewModel.preferences.nativeLanguage, learningViewModel.preferences.difficulty)
                    }
                }
                Flow {
                    Layout.fillWidth: true; spacing: AppTheme.gapSmall
                    Repeater {
                        model: learningViewModel.materials
                        MChip {
                            required property var modelData
                            text: modelData.title
                            checked: learningViewModel.selectedMaterialId === modelData.id
                            enabled: !learningViewModel.busy
                            onClicked: learningViewModel.selectMaterial(modelData.id)
                            Accessible.name: "选择材料 " + modelData.title
                        }
                    }
                }
                MCard {
                    visible: learningViewModel.hasMaterial
                    MLabel { text: learningViewModel.materialTitle; role: "title" }
                    MLabel { objectName: "materialSummaryText"; text: learningViewModel.analysisSummary; maximumLineCount: page.showFullSummary ? 2147483647 : 7; elide: Text.ElideRight }
                    MButton { objectName: "expandMaterialSummaryButton"; visible: learningViewModel.analysisSummary.length > 400; text: page.showFullSummary ? "收起概要" : "展开概要"; variant: "text"; onClicked: page.showFullSummary = !page.showFullSummary }
                    MLabel { text: learningViewModel.materialPreparation + (learningViewModel.busy && learningViewModel.materialPrepared ? " · " + learningViewModel.status : ""); role: "supporting"; objectName: "materialPreparationLabel" }
                    Flow {
                        Layout.fillWidth: true; spacing: AppTheme.gapSmall
                        MButton { text: page.showStructure ? "收起内容结构" : "大纲与人物"; variant: "text"; visible: learningViewModel.analysisOutline.length > 0 || learningViewModel.analysisCharacters.length > 0; onClicked: page.showStructure = !page.showStructure }
                        MButton { text: learningViewModel.materialPrepared ? "检查整理" : "继续整理"; variant: "text"; enabled: !learningViewModel.busy; onClicked: learningViewModel.reanalyze() }
                        MButton { text: page.showSource ? "收起原文" : "查看原文"; variant: "text"; onClicked: page.showSource = !page.showSource }
                    }
                    ColumnLayout {
                        visible: page.showStructure; Layout.fillWidth: true; spacing: 12
                        Repeater { model: learningViewModel.analysisOutline; MLabel { required property string modelData; text: "· " + modelData; role: "supporting" } }
                        Repeater { model: learningViewModel.analysisCharacters; MLabel { required property var modelData; text: modelData.name + "：" + modelData.description; role: "supporting" } }
                    }
                }
                MCard {
                    visible: learningViewModel.hasMaterial
                    color: AppTheme.surfaceContainer
                    MLabel { text: learningViewModel.customTopic.trim().length > 0 ? "自定义：" + learningViewModel.customTopic : learningViewModel.selectedTopicTitle; role: "label" }
                    MTextField {
                        objectName: "customTopicInput"
                        visible: page.optionsExpanded
                        Layout.fillWidth: true; placeholderText: "自己想聊的话题（AI 会先整理参考）"
                        text: learningViewModel.customTopic
                        onTextEdited: learningViewModel.customTopic = text
                    }
                    ButtonGroup { id: modeGroup }
                    Flow {
                        visible: page.optionsExpanded
                        Layout.fillWidth: true; spacing: AppTheme.gapSmall
                        MChip { text: "自然讨论"; ButtonGroup.group: modeGroup; checked: learningViewModel.practiceMode === "discussion"; onClicked: learningViewModel.practiceMode = "discussion" }
                        MChip { text: "语境 roleplay"; ButtonGroup.group: modeGroup; checked: learningViewModel.practiceMode === "roleplay"; onClicked: learningViewModel.practiceMode = "roleplay" }
                    }
                    MTextField { visible: page.optionsExpanded && learningViewModel.practiceMode === "roleplay"; Layout.fillWidth: true; placeholderText: "描述你和 AI 各自的角色"; text: learningViewModel.roleDescription; onTextEdited: learningViewModel.roleDescription = text }
                    Flow {
                        Layout.fillWidth: true; spacing: 8
                        MButton {
                        text: learningViewModel.sessionActive ? "继续当前对话" : learningViewModel.customTopic.trim().length > 0 ? "整理话题并开始" : "开始对话"
                        objectName: "startDiscussionButton"
                        enabled: !learningViewModel.busy && (learningViewModel.sessionActive || learningViewModel.materialPrepared && (learningViewModel.topics.length > 0 || learningViewModel.customTopic.trim().length > 0))
                        onClicked: { if (learningViewModel.sessionActive) page.navigate(1); else learningViewModel.startPractice() }
                        }
                        MButton { text: page.optionsExpanded ? "收起选项" : "自定义话题与模式"; objectName: "discussionOptionsButton"; variant: "text"; onClicked: page.optionsExpanded = !page.optionsExpanded }
                    }
                }
                RowLayout {
                    visible: learningViewModel.topics.length > 0
                    Layout.fillWidth: true
                    MLabel { text: "话题 · " + learningViewModel.topics.length; role: "title"; Layout.fillWidth: false }
                    MTextField { visible: learningViewModel.topics.length > 6; objectName: "topicSearchInput"; Layout.fillWidth: true; placeholderText: "查找话题"; text: learningViewModel.topicSearch; onTextEdited: learningViewModel.topicSearch = text }
                }
                Flow {
                    Layout.fillWidth: true; spacing: AppTheme.gapSmall
                    Repeater {
                        model: learningViewModel.topicCategories
                        MChip { required property string modelData; required property int index; objectName: "topicCategory" + index; text: modelData; checked: learningViewModel.topicFilter === modelData; onClicked: learningViewModel.topicFilter = modelData }
                    }
                }
                GridLayout {
                    Layout.fillWidth: true
                    columns: page.width >= 820 ? 2 : 1
                    columnSpacing: 16; rowSpacing: 16
                    Repeater {
                        model: learningViewModel.filteredTopics
                        MCard {
                            id: topicCard
                            required property var modelData
                            required property int index
                            property bool expanded: false
                            Layout.fillWidth: true; Layout.alignment: Qt.AlignTop
                            outlined: true
                            border.color: learningViewModel.selectedTopicId === modelData.id ? AppTheme.primary : AppTheme.outlineVariant
                            color: learningViewModel.selectedTopicId === modelData.id ? AppTheme.primaryContainer : AppTheme.surfaceContainerLow
                            MLabel { text: topicCard.modelData.category_label || "讨论"; role: "label"; color: AppTheme.primary }
                            MLabel { text: topicCard.modelData.title; role: "title" }
                            MLabel { text: topicCard.modelData.opening_question; font.family: AppTheme.japaneseFont }
                            RowLayout {
                                Layout.fillWidth: true
                                MButton { objectName: "selectTopic" + topicCard.index; text: learningViewModel.selectedTopicId === topicCard.modelData.id ? "已选择" : "选这个"; variant: learningViewModel.selectedTopicId === topicCard.modelData.id ? "filled" : "outlined"; enabled: !learningViewModel.busy; onClicked: learningViewModel.selectTopic(topicCard.modelData.id) }
                                MButton { objectName: "topicReference" + topicCard.index; text: topicCard.expanded ? "收起" : "参考"; variant: "text"; onClicked: topicCard.expanded = !topicCard.expanded }
                            }
                            ColumnLayout {
                                visible: topicCard.expanded; Layout.fillWidth: true
                                MLabel { text: "材料依据：" + topicCard.modelData.source_excerpt; role: "supporting" }
                                Repeater {
                                    model: topicCard.modelData.answer_branches || []
                                    ColumnLayout {
                                        required property var modelData
                                        Layout.fillWidth: true
                                        MLabel { text: "可能的讨论方向：" + modelData.user_intent; role: "label" }
                                        MLabel { text: (modelData.response_points || []).join("\n"); role: "supporting" }
                                        MLabel { text: modelData.suggested_reply || ""; font.family: AppTheme.japaneseFont }
                                    }
                                }
                            }
                        }
                    }
                }
                MCard {
                    visible: page.showSource && learningViewModel.hasMaterial
                    Switch { text: "显示清洗结果"; checked: page.normalized; onToggled: page.normalized = checked }
                    MLabel { text: page.normalized ? learningViewModel.materialNormalizedContent : learningViewModel.materialRawContent; font.family: AppTheme.japaneseFont }
                }
                Item { Layout.preferredHeight: 16 }
            }
        }
    }
    Dialogs.FileDialog {
        id: fileDialog
        objectName: "materialFileDialog"
        title: "导入看过的内容"
        nameFilters: ["沉浸材料 (*.txt *.srt *.vtt *.md *.markdown *.docx *.epub *.xlsx *.mp4 *.mkv *.webm *.mov *.avi)"]
        onAccepted: learningViewModel.importMaterial(selectedFile.toString(), "",
            learningViewModel.preferences.targetLanguage, learningViewModel.preferences.targetLanguage,
            learningViewModel.preferences.nativeLanguage, learningViewModel.preferences.difficulty, "live_chat")
    }
}
