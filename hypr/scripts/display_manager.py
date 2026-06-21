#!/usr/bin/env python3
from time import sleep

import gi
import subprocess
import os
import sys

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

STATE_FILE = os.path.expanduser("~/.config/hypr/.last_display_state")
INTERNAL = "DP-1"
EXTERNAL = "HDMI-A-1"

# Identificadores basados en la salida de wpctl status
AUDIO_MONITOR = "Ryzen HD Audio Controller"
AUDIO_TV = "Renoir/Cezanne HDMI/DP Audio Controller"

def run_system_cmd(cmd):
    subprocess.Popen(cmd, shell=True)

def cambiar_audio(nombre_sink):
    try:
        # Leemos el estado actual de PipeWire
        output = subprocess.check_output("wpctl status", shell=True).decode()
        in_sinks = False
        sink_id = None
        
        for line in output.split('\n'):
            if "Sinks:" in line:
                in_sinks = True
                continue
            # Salimos del bucle si llegamos a otra categoría
            if in_sinks and ("Sources:" in line or "Filters:" in line):
                break 
            
            # Buscamos la línea que coincide con el nombre de tu dispositivo
            if in_sinks and nombre_sink in line:
                # Limpiamos caracteres visuales ('*', '│') y espacios
                line_clean = line.replace('*', '').replace('│', '').strip()
                # El ID es el número que está antes del punto
                sink_id = line_clean.split('.')[0].strip()
                break
        
        if sink_id:
            # wpctl set-default define la salida principal. 
            # WirePlumber se encarga de migrar el audio de las apps activas automáticamente.
            run_system_cmd(f"wpctl set-default {sink_id}")
            
    except Exception as e:
        print(f"Error cambiando audio: {e}")

def guardar_estado(perfil):
    with open(STATE_FILE, "w") as f:
        f.write(perfil)

def perfil_monitor():
    run_system_cmd(f"hyprctl keyword monitor '{INTERNAL},1920x1080@60,0x0,1'")
    run_system_cmd(f"hyprctl keyword monitor '{EXTERNAL},disabled'")
    sleep(0.5)
    cambiar_audio(AUDIO_MONITOR)
    guardar_estado("monitor")

def perfil_tv():
    run_system_cmd(f"hyprctl keyword monitor '{INTERNAL},disabled'")
    run_system_cmd(f"hyprctl keyword monitor '{EXTERNAL},1920x1080@60,0x0,1'")
    sleep(3)
    cambiar_audio(AUDIO_TV)
    guardar_estado("tv")

def perfil_duplicar():
    run_system_cmd(f"hyprctl keyword monitor '{INTERNAL},1920x1080@60,0x0,1'")
    run_system_cmd(f"hyprctl keyword monitor '{EXTERNAL},1920x1080@60,0x0,1,mirror,{INTERNAL}'")
    sleep(0.5)
    cambiar_audio(AUDIO_TV)
    guardar_estado("duplicar")

def perfil_extender():
    run_system_cmd(f"hyprctl keyword monitor '{INTERNAL},1920x1080@60,0x0,1'")
    run_system_cmd(f"hyprctl keyword monitor '{EXTERNAL},1920x1080@60,auto-up,1'")
    
    run_system_cmd(f"hyprctl keyword workspace 1,monitor:{INTERNAL}")
    run_system_cmd(f"hyprctl keyword workspace 2,monitor:{EXTERNAL}")
    run_system_cmd(f"hyprctl dispatch focusmonitor {INTERNAL}")
    run_system_cmd(f"hyprctl dispatch workspace 1")
    
    sleep(0.5)
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
        
        try:
            import json
            output = subprocess.check_output("hyprctl monitors -j", shell=True, text=True)
            monitors = json.loads(output)
            active = [m for m in monitors if not m.get("disabled", False)]
            if active:
                monitor_name = active[0]["name"]
                run_system_cmd(f"hyprctl dispatch focusmonitor {monitor_name}")
                run_system_cmd("hyprctl dispatch workspace 1")
        except Exception as e:
            print(f"Error al forzar workspace 1: {e}")
    else:
        app_instance = Gtk.Application(application_id="com.yako.displaymanager")
        app_instance.connect("activate", on_activate)
        app_instance.run(None)