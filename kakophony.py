from ast import Call
from cProfile import label
from pickle import TRUE
from subprocess import CalledProcessError, check_output
import sys

# For locating the headsetcontrol bin.
from shutil import which

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QAction, QMessageBox
from PySide2.QtCore import QTimer
import PySide2.Qt

# Headsetcontrol binary location.
BIN_HEADSETCONTROL = None
PARAM_BATTERY = "-b"
PARAM_QUIET = "--short-output"
PARAM_CAPABILITIES = "-?"
PARAM_LED = "-l"
PARAM_SIDETONE = "-s"
PARAM_SIDETONE_OFF = 0
PARAM_SIDETONE_VERYQUIET = 8
PARAM_SIDETONE_QUIET = 16
PARAM_SIDETONE_NORMAL = 32
PARAM_SIDETONE_LOUD = 64
PARAM_SIDETONE_VERYLOUD = 100

TRAY_ROOT = None
TRAY_BATTERY = None

# KDE battery icons.
ICONS_BATTERYLEVEL_KDE = [
    "battery-000", "battery-010", "battery-020", "battery-030", 
    "battery-040", "battery-050", "battery-060", "battery-070", 
    "battery-080", "battery-090", "battery-100"]
ICONS_BATTERYCHARGE_KDE = "battery-full-charging"
ICONS_NOBATTERY_KDE = "battery-missing"

# GNOME battery icon names.
ICONS_BATTERYLEVEL_GNOME = [
    "battery-level-0", "battery-level-10", "battery-level-20",
    "battery-level-30", "battery-level-40", "battery-level-50",
    "battery-level-60", "battery-level-70", "battery-level-80",
    "battery-level-90", "battery-level-100"
]
ICONS_BATTERYCHARGE_GNOME = "battery-full-charging"
ICONS_NOBATTERY_GNOME = "battery-missing"

def get_capabilities():
    try:
        output = check_output([BIN_HEADSETCONTROL, PARAM_QUIET, PARAM_CAPABILITIES])
        return output
    except CalledProcessError as e:
        print(e)
        return "-"

def get_battery_level():
    try:
        output = check_output([BIN_HEADSETCONTROL, PARAM_QUIET, PARAM_BATTERY])
        try:
            batlevel = int(output)
            if 0 <= batlevel <= 100:
                return batlevel
            elif batlevel == -1:
                return -1
            else:
                return -2
        except ValueError as e:
            return -2
    except CalledProcessError as e:
        return -2

def update_battery_level():

    batlevel = get_battery_level()
    if batlevel == -1:
        TRAY_BATTERY.setIcon(
            QIcon.fromTheme(ICONS_BATTERYCHARGE_KDE, QIcon.fromTheme(ICONS_BATTERYCHARGE_GNOME, QIcon.fromTheme("battery")))
        )
        TRAY_BATTERY.setText("Battery: charging")
        TRAY_ROOT.setToolTip("Battery: charging")
        
    elif batlevel == -2:
        TRAY_BATTERY.setIcon(
            QIcon.fromTheme(ICONS_NOBATTERY_KDE, QIcon.fromTheme(ICONS_NOBATTERY_GNOME, QIcon.fromTheme("battery")))
        )
        TRAY_BATTERY.setText("Battery: error")
        TRAY_ROOT.setToolTip("Battery: error")
    else:
        TRAY_BATTERY.setIcon(
            QIcon.fromTheme(ICONS_BATTERYLEVEL_KDE[batlevel // 10], QIcon.fromTheme(ICONS_BATTERYCHARGE_GNOME[batlevel // 10], QIcon.fromTheme("battery")))
        )
        TRAY_BATTERY.setText("Battery: " + str(batlevel) + "%")
        TRAY_ROOT.setToolTip("Battery: " + str(batlevel) + "%")

def set_led(state):
    try:
        check_output([BIN_HEADSETCONTROL, PARAM_LED, str(state)])
    except CalledProcessError as e:
        print(e)

def set_sidetone(level):
    try:
        check_output([BIN_HEADSETCONTROL, PARAM_SIDETONE, str(level)])
    except CalledProcessError as e:
        print(e)

def update():
    capabilities = get_capabilities()
    if b"b" in capabilities:
        update_battery_level()
    else:
        TRAY_ROOT.setToolTip("Unknown battery level")


if __name__ == '__main__':

    BIN_HEADSETCONTROL = which("headsetcontrol")
    capabilities = get_capabilities()

    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    # Tray icon root.
    icon = QIcon().fromTheme("audio-headset", QIcon("icon.svg"))
    TRAY_ROOT = QSystemTrayIcon(icon, app)
    menu = QMenu()

    # Battery status button.
    TRAY_BATTERY = QAction()
    menu.addAction(TRAY_BATTERY)

    # Status / control sections separator.
    menu.addSeparator()

    # Add actions according to headsets' capabilities.
    if b"s" in capabilities:
        action_sidetoneOff = QAction("Off")
        action_sidetoneOff.triggered.connect(lambda: set_sidetone(PARAM_SIDETONE_OFF))
        action_sidetoneVeryQuiet = QAction("Very quiet")
        action_sidetoneVeryQuiet.triggered.connect(lambda: set_sidetone(PARAM_SIDETONE_VERYQUIET))
        action_sidetoneLow = QAction("Quiet")
        action_sidetoneLow.triggered.connect(lambda: set_sidetone(PARAM_SIDETONE_QUIET))
        action_sidetoneNormal = QAction("Normal")
        action_sidetoneNormal.triggered.connect(lambda: set_sidetone(PARAM_SIDETONE_NORMAL))
        action_sidetoneLoud = QAction("Loud")
        action_sidetoneLoud.triggered.connect(lambda: set_sidetone(PARAM_SIDETONE_LOUD))
        action_sidetoneVeryLoud = QAction("Very loud")
        action_sidetoneVeryLoud.triggered.connect(lambda: set_sidetone(PARAM_SIDETONE_VERYLOUD))
        submenu_sidetone = QMenu("Sidetone")
        submenu_sidetone.addActions([action_sidetoneOff, action_sidetoneVeryQuiet, action_sidetoneLow, action_sidetoneNormal, action_sidetoneLoud, action_sidetoneVeryLoud])
        menu.addMenu(submenu_sidetone)
    if b"l" in capabilities:
        action_ledOn = QAction("On")
        action_ledOn.triggered.connect(lambda: set_led(1))
        action_ledOff = QAction("Off")
        action_ledOff.triggered.connect(lambda: set_led(0))
        submenu_led = QMenu("LED")
        submenu_led.addActions([action_ledOn, action_ledOff])
        menu.addMenu(submenu_led)


    # Exit button.
    action_exit = QAction("Exit")
    action_exit.triggered.connect(app.exit)
    action_exit.setIcon(QIcon.fromTheme("application-exit"))
    menu.addAction(action_exit)

    # Init tray menu.
    TRAY_ROOT.setContextMenu(menu)
    TRAY_ROOT.show()

    # Initial update.
    update()

    # Bind an updater to periodically refresh battery status.
    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(2000)

    sys.exit(app.exec_())