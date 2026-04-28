#!/usr/bin/env python3
import sys
import subprocess
import json

def run_cmd(cmd):
    """Ejecuta un comando y devuelve el JSON parseado."""
    try:
        output = subprocess.check_output(cmd, shell=True, text=True)
        return json.loads(output)
    except Exception:
        return []

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    target_ws = sys.argv[1]

    active_ws_data = run_cmd("hyprctl activeworkspace -j")
    if not active_ws_data:
        sys.exit(1)

    current_ws = str(active_ws_data.get("id", ""))
    current_ws_name = active_ws_data.get("name", "")
    current_mon = active_ws_data.get("monitor", "")

    if target_ws in (current_ws, current_ws_name):
        sys.exit(0)

    workspaces_data = run_cmd("hyprctl workspaces -j")
    target_mon = None

    for ws in workspaces_data:
        if str(ws.get("id")) == target_ws or ws.get("name") == target_ws:
            target_mon = ws.get("monitor")
            break

    if not target_mon or target_mon == current_mon:
        subprocess.run(f"hyprctl dispatch workspace {target_ws}", shell=True)
        sys.exit(0)

    monitors_data = run_cmd("hyprctl monitors -j")
    target_is_active = False

    for mon in monitors_data:
        if mon.get("name") == target_mon:
            active_on_mon = mon.get("activeWorkspace", {})
            if str(active_on_mon.get("id")) == target_ws or active_on_mon.get("name") == target_ws:
                target_is_active = True
            break

    if target_is_active:
        subprocess.run(f"hyprctl dispatch swapactiveworkspaces {current_mon} {target_mon}", shell=True)
    else:
        batch_cmd = (
            f"dispatch moveworkspacetomonitor {target_ws} {current_mon}; "
            f"dispatch moveworkspacetomonitor {current_ws} {target_mon}; "
            f"dispatch workspace {target_ws}"
        )
        subprocess.run(f"hyprctl --batch \"{batch_cmd}\"", shell=True)

if __name__ == "__main__":
    main()