from subprocess import CalledProcessError, check_output
import sys

# For locating the headsetcontrol bin.
from shutil import which

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QAction, QMessageBox
from PySide2.QtCore import QTimer

# Headsetcontrol binary location.
BIN_HEADSETCONTROL = None
PARAM_BATTERY = "-b"
PARAM_QUIET = "--short-output"
PARAM_CAPABILITIES = "-?"

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

def update():
    if b"b" in get_capabilities():
        update_battery_level()
    else:
        TRAY_ROOT.setToolTip("Unknown battery level")


if __name__ == '__main__':

    BIN_HEADSETCONTROL = which("headsetcontrol")

    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    TRAY_ROOT = QSystemTrayIcon(QIcon("icon.svg"), app)
    menu = QMenu()

    TRAY_BATTERY = QAction()
    menu.addAction(TRAY_BATTERY)

    action_exit = QAction("Exit")
    action_exit.triggered.connect(app.exit)
    menu.addAction(action_exit)

    TRAY_ROOT.setContextMenu(menu)
    TRAY_ROOT.show()

    # Initial update.
    update()

    # Bind an updater to periodically refresh battery status.
    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(2000)

    sys.exit(app.exec_())