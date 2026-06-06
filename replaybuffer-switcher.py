import obspython as obs
import websocket
import threading
import json
import queue

_cfg = {
    'user_id': '',
    'source': '',
    'mappings': {},
}
_last_game = None
_pending = queue.Queue()
_stop = threading.Event()
_ws_thread = None
_current_ws = None
_settings_ref = None


def script_description():
    return (
        "<b>replaybuffer switcher</b><br><br>"
        "switches a game capture source to a specific window based on your "
        "discord activity via Lanyard.<br><br>"
        "<b>to add a game:</b><br>launch it, let Discord detect it, set your game capture "
        "source to that window, then click <i>add current game</i>.<br><br>"
        "[!] needs <code>pip install websocket-client</code>"
    )


def script_properties():
    p = obs.obs_properties_create()
    obs.obs_properties_add_text(p, "user_id", "Discord User ID", obs.OBS_TEXT_DEFAULT)

    source_list = obs.obs_properties_add_list(
        p, "source", "Game Capture Source",
        obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING
    )
    sources = obs.obs_enum_sources()
    if sources:
        for src in sources:
            if obs.obs_source_get_id(src) == "game_capture":
                name = obs.obs_source_get_name(src)
                obs.obs_property_list_add_string(source_list, name, name)
        obs.source_list_release(sources)

    obs.obs_properties_add_text(p, "game_mappings", "Game Mappings (one per line)", obs.OBS_TEXT_MULTILINE)
    obs.obs_properties_add_button(p, "add_btn", "Add Current Game", _add_current_game)
    return p


def script_defaults(settings):
    pass


def script_update(settings):
    global _settings_ref
    _settings_ref = settings
    _cfg['user_id'] = obs.obs_data_get_string(settings, "user_id")
    _cfg['source'] = obs.obs_data_get_string(settings, "source")

    mappings = {}
    for line in obs.obs_data_get_string(settings, "game_mappings").splitlines():
        if '=' in line:
            game, _, window = line.partition('=')
            mappings[game.lower().strip()] = window
    _cfg['mappings'] = mappings

    _reconnect()


def script_load(settings):
    obs.timer_add(_drain_pending, 250)


def script_unload():
    obs.timer_remove(_drain_pending)
    _stop.set()
    if _current_ws:
        try:
            _current_ws.close()
        except Exception:
            pass


def _add_current_game(props, prop):
    if not _last_game:
        obs.script_log(obs.LOG_WARNING, "[game-switcher] No game detected yet, is Discord running?")
        return True

    src = obs.obs_get_source_by_name(_cfg['source'])
    if not src:
        obs.script_log(obs.LOG_WARNING, f"[game-switcher] Source not found: '{_cfg['source']}'")
        return True

    src_settings = obs.obs_source_get_settings(src)
    window = obs.obs_data_get_string(src_settings, "window")
    obs.obs_data_release(src_settings)
    obs.obs_source_release(src)

    if not window:
        obs.script_log(obs.LOG_WARNING,
            "[game-switcher] Game Capture has no window selected, "
            "set it to Capture specific window and pick the game first.")
        return True

    entry = f"{_last_game}={window}"
    existing = obs.obs_data_get_string(_settings_ref, "game_mappings")
    obs.obs_data_set_string(_settings_ref, "game_mappings", (existing.rstrip('\n') + '\n' + entry).lstrip('\n'))

    _cfg['mappings'][_last_game.lower().strip()] = window
    obs.script_log(obs.LOG_INFO, f"[game-switcher] Added: {entry}")
    return True


def _drain_pending():
    while not _pending.empty():
        try:
            _apply_window(_pending.get_nowait())
        except queue.Empty:
            break


def _apply_window(window):
    src = obs.obs_get_source_by_name(_cfg['source'])
    if not src:
        obs.script_log(obs.LOG_WARNING, f"[game-switcher] Source not found: '{_cfg['source']}'")
        return
    d = obs.obs_data_create()
    obs.obs_data_set_string(d, "window", window)
    obs.obs_source_update(src, d)
    obs.obs_data_release(d)
    obs.obs_source_release(src)


def _on_game(game):
    global _last_game
    if game == _last_game:
        return
    _last_game = game
    window = _cfg['mappings'].get((game or '').lower().strip(), '')
    obs.script_log(obs.LOG_INFO, f"[game-switcher] {game!r} -> {window!r}")
    _pending.put(window)


def _lanyard_thread(user_id, stop_event):
    global _current_ws

    def on_message(ws, raw):
        try:
            msg = json.loads(raw)
            op = msg.get('op')
            if op == 1:
                interval = msg['d']['heartbeat_interval'] / 1000
                ws.send(json.dumps({'op': 2, 'd': {'subscribe_to_id': user_id}}))
                def heartbeat():
                    while not stop_event.wait(interval):
                        try:
                            ws.send(json.dumps({'op': 3}))
                        except Exception:
                            break
                threading.Thread(target=heartbeat, daemon=True).start()
            elif op == 0 and msg.get('t') in ('INIT_STATE', 'PRESENCE_UPDATE'):
                acts = msg.get('d', {}).get('activities', [])
                _on_game(next((a['name'] for a in acts if a.get('type') == 0), None))
        except Exception as e:
            obs.script_log(obs.LOG_WARNING, f"[game-switcher] Message error: {e}")

    def on_error(ws, error):
        obs.script_log(obs.LOG_WARNING, f"[game-switcher] WS error: {error}")

    while not stop_event.is_set():
        try:
            ws = websocket.WebSocketApp(
                "wss://api.lanyard.rest/socket",
                on_message=on_message,
                on_error=on_error,
            )
            _current_ws = ws
            ws.run_forever()
            _current_ws = None
        except Exception as e:
            obs.script_log(obs.LOG_WARNING, f"[game-switcher] Connection error: {e}")
        if not stop_event.is_set():
            obs.script_log(obs.LOG_INFO, "[game-switcher] Reconnecting in 5s...")
            stop_event.wait(5)


def _reconnect():
    global _stop, _ws_thread
    _stop.set()
    if _current_ws:
        try:
            _current_ws.close()
        except Exception:
            pass
    if _ws_thread and _ws_thread.is_alive():
        _ws_thread.join(timeout=3)
    _stop = threading.Event()
    if _cfg['user_id']:
        _ws_thread = threading.Thread(
            target=_lanyard_thread,
            args=(_cfg['user_id'], _stop),
            daemon=True,
        )
        _ws_thread.start()
