#!/usr/bin/env python3
import gi
import subprocess
import os
import sys

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

STATE_FILE = os.path.expanduser("~/.config/hypr/.last_display_state")
INTERNAL = "VGA-1"
EXTERNAL = "HDMI-A-1"
AUDIO_MONITOR = "alsa_output.pci-0000_00_1f.3.analog-stereo"
AUDIO_TV = "alsa_output.pci-0000_01_00.1.hdmi-stereo"

def run_system_cmd(cmd):
    subprocess.Popen(cmd, shell=True)

def cambiar_audio(nuevo_sink):
    run_system_cmd(f"pactl set-default-sink {nuevo_sink}")
    try:
        inputs = subprocess.check_output("pactl list short sink-inputs | awk '{print $1}'", shell=True).decode().split()
        for i in inputs:
            run_system_cmd(f"pactl move-sink-input {i} {nuevo_sink}")
    except:
        pass

def guardar_estado(perfil):
    with open(STATE_FILE, "w") as f:
        f.write(perfil)

def perfil_monitor():
    run_system_cmd(f"hyprctl keyword monitor '{INTERNAL},1920x1080@60,0x0,1'")
    run_system_cmd(f"hyprctl keyword monitor '{EXTERNAL},disabled'")
    cambiar_audio(AUDIO_MONITOR)
    guardar_estado("monitor")

def perfil_tv():
    run_system_cmd(f"hyprctl keyword monitor '{INTERNAL},disabled'")
    run_system_cmd(f"hyprctl keyword monitor '{EXTERNAL},1920x1080@60,0x0,1'")
    cambiar_audio(AUDIO_TV)
    guardar_estado("tv")

def perfil_duplicar():
    run_system_cmd(f"hyprctl keyword monitor '{INTERNAL},1920x1080@60,0x0,1'")
    run_system_cmd(f"hyprctl keyword monitor '{EXTERNAL},1920x1080@60,0x0,1,mirror,{INTERNAL}'")
    cambiar_audio(AUDIO_TV)
    guardar_estado("duplicar")

def perfil_extender():
    run_system_cmd(f"hyprctl keyword monitor '{INTERNAL},1280x1024@60,0x0,1'")
    run_system_cmd(f"hyprctl keyword monitor '{EXTERNAL},1920x1080@60,auto-up,1'")
    
    run_system_cmd(f"hyprctl keyword workspace 1,monitor:{INTERNAL}")
    run_system_cmd(f"hyprctl keyword workspace 2,monitor:{EXTERNAL}")
    run_system_cmd(f"hyprctl dispatch focusmonitor {INTERNAL}")
    run_system_cmd(f"hyprctl dispatch workspace 1")
    
    cambiar_audio(AUDIO_MONITOR)
    guardar_estado("extender")

BUTTONS = [
    ("󰍹 ", perfil_monitor),
    (" ", perfil_tv),
    ("󰍺 ", perfil_duplicar),
    ("󰍹   ", perfil_extender),
]

CSS = """
window {
    background-color: rgba(0, 0, 0, 0.4);
}
.display-manager {
    background-color: #1a1b26;
    border-radius: 20px;
    border: 2px solid #7aa2f7;
    padding: 20px;
}
.displayManagerButton {
    font-family: "JetBrainsMono Nerd Font Bold";
    font-size: 45px;
    margin: 0px; 
    padding: 20px;
    border-radius: 15px;
    background-color: #1a1b26;
    color: #c0caf5;
    border: none;
    min-height: 140px; 
}
.displayManagerButton.active {
    background-color: #7aa2f7;
    color: #1a1b26;
}
"""

buttons = []
win = None
app = None

def run_action(action):
    if callable(action):
        action()
    else:
        run_system_cmd(action)
    app.quit()

def set_active(index):
    for btn in buttons:
        btn.remove_css_class("active")
    if 0 <= index < len(buttons):
        buttons[index].add_css_class("active")

def get_active_index():
    for i, btn in enumerate(buttons):
        if btn.has_css_class("active"):
            return i
    return None

def on_key(controller, keyval, keycode, state):
    current = get_active_index()
    if keyval == Gdk.KEY_Right:
        set_active((current + 1) % len(buttons) if current is not None else 0)
    elif keyval == Gdk.KEY_Left:
        set_active((current - 1) % len(buttons) if current is not None else 0)
    elif keyval == Gdk.KEY_Return:
        if current is not None:
            run_action(BUTTONS[current][1])
    elif keyval in [Gdk.KEY_Escape, Gdk.KEY_q]:
        app.quit()
    return True

def on_activate(application):
    global win, app
    app = application

    provider = Gtk.CssProvider()
    provider.load_from_data(CSS.encode('utf-8'))
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    win = Gtk.ApplicationWindow(application=application)
    win.set_decorated(False)
    win.fullscreen()

    overlay_click = Gtk.GestureClick()
    overlay_click.connect("pressed", lambda *a: application.quit())
    win.add_controller(overlay_click)

    key_ctrl = Gtk.EventControllerKey()
    key_ctrl.connect("key-pressed", on_key)
    win.add_controller(key_ctrl)

    center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    center_box.set_halign(Gtk.Align.CENTER)
    center_box.set_valign(Gtk.Align.CENTER)

    menu = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
    menu.add_css_class("display-manager")
    menu.set_homogeneous(True)
    menu.set_size_request(800, 150)

    for i, (icon, action) in enumerate(BUTTONS):
        btn = Gtk.Button(label=icon)
        btn.add_css_class("displayManagerButton")
        btn.set_focusable(False)
        btn.connect("clicked", lambda b, a=action: run_action(a))

        btn_click = Gtk.GestureClick()
        btn_click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        btn_click.connect("pressed", lambda ctrl, *a: ctrl.set_state(Gtk.EventSequenceState.CLAIMED))
        btn.add_controller(btn_click)

        motion = Gtk.EventControllerMotion()
        motion.connect("enter", lambda ctrl, x, y, idx=i: set_active(idx))
        btn.add_controller(motion)

        menu.append(btn)
        buttons.append(btn)

    center_box.append(menu)
    win.set_child(center_box)
    win.present()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--load":
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                estado = f.read().strip().lower()
            perfiles = {"monitor": perfil_monitor, "tv": perfil_tv, "duplicar": perfil_duplicar, "extender": perfil_extender}
            perfiles.get(estado, perfil_monitor)()
        else:
            perfil_monitor()
    else:
        app_instance = Gtk.Application(application_id="com.yako.displaymanager")
        app_instance.connect("activate", on_activate)
        app_instance.run(None)
