pragma Singleton
import QtQuick

QtObject {
    readonly property bool dark: learningViewModel.preferences.themeMode === "dark" || (learningViewModel.preferences.themeMode === "system" && learningViewModel.systemDark)
    readonly property bool reducedMotion: learningViewModel.preferences.reducedMotion
    readonly property int duration: reducedMotion ? 0 : 200
    readonly property color primary: dark ? "#D0BCFF" : "#6750A4"
    readonly property color colorOnPrimary: dark ? "#381E72" : "#FFFFFF"
    readonly property color primaryContainer: dark ? "#4F378B" : "#EADDFF"
    readonly property color colorOnPrimaryContainer: dark ? "#EADDFF" : "#21005D"
    readonly property color secondaryContainer: dark ? "#4A4458" : "#E8DEF8"
    readonly property color colorOnSecondaryContainer: dark ? "#E8DEF8" : "#1D192B"
    readonly property color surface: dark ? "#141218" : "#FEF7FF"
    readonly property color surfaceContainerLow: dark ? "#1D1B20" : "#F7F2FA"
    readonly property color surfaceContainer: dark ? "#211F26" : "#F3EDF7"
    readonly property color surfaceContainerHigh: dark ? "#2B2930" : "#ECE6F0"
    readonly property color colorOnSurface: dark ? "#E6E0E9" : "#1D1B20"
    readonly property color colorOnSurfaceVariant: dark ? "#CAC4D0" : "#49454F"
    readonly property color outline: dark ? "#938F99" : "#79747E"
    readonly property color outlineVariant: dark ? "#49454F" : "#CAC4D0"
    readonly property color error: dark ? "#F2B8B5" : "#B3261E"
    readonly property color errorContainer: dark ? "#8C1D18" : "#F9DEDC"
    readonly property color colorOnErrorContainer: dark ? "#F9DEDC" : "#410E0B"
    readonly property color scrim: "#66000000"
    readonly property int space: 4
    readonly property int gapSmall: 8
    readonly property int gapMedium: 12
    readonly property int gapLarge: 16
    readonly property int sectionGap: 20
    readonly property int pageMargin: 24
    readonly property int compactPageMargin: 16
    readonly property int railWidth: 80
    readonly property int contextWidth: 320
    readonly property int topBarHeight: 64
    readonly property int navigationBarHeight: 80
    readonly property int touchTarget: 48
    readonly property int compactBreakpoint: 600
    readonly property int expandedBreakpoint: 1200
    readonly property real bodyLineHeight: 1.35
    readonly property int cardRadius: 12
    readonly property int panelRadius: 16
    readonly property int dialogRadius: 28
    readonly property int bodyLarge: 16
    readonly property int bodyMedium: 14
    readonly property int labelLarge: 14
    readonly property int titleLarge: 22
    readonly property int headlineMedium: 28
    readonly property string uiFont: Qt.platform.os === "windows" ? "Microsoft YaHei UI" : Qt.platform.os === "osx" ? "PingFang SC" : "Noto Sans CJK SC"
    readonly property string japaneseFont: Qt.platform.os === "windows" ? "Yu Gothic UI" : uiFont
}
