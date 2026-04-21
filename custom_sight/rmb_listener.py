import threading
import logging

from pynput import mouse


def start_rmb_listener(overlay):
    lock  = threading.Lock()
    state = {"pressed": False, "timer": None, "hidden": False}

    def hide_task():
        with lock:
            if state["pressed"] and overlay.rmb_hide_enabled:
                try:
                    overlay.visibility_signal.emit(False)
                except Exception as e:
                    logging.error(f"hide_task: {e}")
                state["hidden"] = True
            state["timer"] = None

    def on_click(x, y, btn, pressed):
        if btn != mouse.Button.right:
            return
        with lock:
            if pressed:
                state["pressed"] = True
                if not overlay.rmb_hide_enabled:
                    if state["timer"]:
                        state["timer"].cancel()
                        state["timer"] = None
                    state["hidden"] = False
                    overlay.visibility_signal.emit(True)
                    return
                if state["timer"]:
                    state["timer"].cancel()
                t = threading.Timer(overlay.rmb_threshold, hide_task)
                t.daemon = True
                t.start()
                state["timer"] = t
            else:
                state["pressed"] = False
                if state["timer"]:
                    state["timer"].cancel()
                    state["timer"] = None
                if state["hidden"]:
                    overlay.visibility_signal.emit(True)
                state["hidden"] = False

    listener = mouse.Listener(on_click=on_click)
    listener.daemon = True
    listener.start()
    return listener
