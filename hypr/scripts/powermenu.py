#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk
import subprocess

# --- CONFIGURACIÓN ---
BUTTONS = [
    ("", "systemctl suspend"),
    ("󰈆", "hyprctl dispatch exit"),
    ("", "systemctl reboot"),
    ("󰐥", "systemctl poweroff"),
]

CSS = b"""
window {
    background-color: rgba(0, 0, 0, 0.4);
}
.power-menu {
    background-color: #1a1b26;
    border-radius: 20px;
    border: 2px solid #7aa2f7;
    padding: 20px;
}
.powerMenuButton {
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

.powerMenuButton.active {
    background-color: #7aa2f7;
    color: #1a1b26;
}
"""

# --- LÓGICA GLOBAL ---
buttons = []
using_keyboard = False
win = None
app = None

def run(cmd):
    subprocess.Popen(cmd, shell=True)
    app.quit()

def clear_all():
    for btn in buttons:
        btn.remove_css_class("active")

def set_active(index):
    clear_all()
    if 0 <= index < len(buttons):
        buttons[index].add_css_class("active")

def get_active_index():
    for i, btn in enumerate(buttons):
        if btn.has_css_class("active"):
            return i
    return None

def enable_keyboard_mode(index):
    global using_keyboard
    using_keyboard = True
    set_active(index)

def on_key(controller, keyval, keycode, state):
    current = get_active_index()
    
    if keyval == Gdk.KEY_Right:
        new_idx = (current + 1) % len(buttons) if current is not None else 0
        enable_keyboard_mode(new_idx)
    elif keyval == Gdk.KEY_Left:
        new_idx = (current - 1) % len(buttons) if current is not None else 0
        enable_keyboard_mode(new_idx)
    elif keyval == Gdk.KEY_Return: # La tecla Enter
        if current is not None:
            run(BUTTONS[current][1])
    elif keyval == Gdk.KEY_Escape:
        app.quit()
    return True

# --- CONSTRUCCIÓN DE INTERFAZ ---
def on_activate(application):
    global win, app
    app = application

    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_display(
        Gdk.Display.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

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
    menu.add_css_class("power-menu")
    
    menu.set_homogeneous(True)
    menu.set_size_request(800, 150)

    for i, (icon, cmd) in enumerate(BUTTONS):
        btn = Gtk.Button(label=icon)
        btn.add_css_class("powerMenuButton")
        
        btn.set_focusable(False)
        
        btn.set_hexpand(True)
        btn.set_halign(Gtk.Align.FILL)
        
        btn.connect("clicked", lambda b, c=cmd: run(c))

        btn_click = Gtk.GestureClick()
        btn_click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        btn_click.connect("pressed", lambda ctrl, *a: ctrl.set_state(Gtk.EventSequenceState.CLAIMED))
        btn.add_controller(btn_click)

        motion = Gtk.EventControllerMotion()
        def on_enter(ctrl, x, y, idx=i):
            global using_keyboard
            using_keyboard = False
            set_active(idx)

        motion.connect("enter", on_enter)
        btn.add_controller(motion)

        menu.append(btn)
        buttons.append(btn)

    center_box.append(menu)
    win.set_child(center_box)
    win.present()

app_instance = Gtk.Application(application_id="com.yako.powermenu")
app_instance.connect("activate", on_activate)
app_instance.run(None)
