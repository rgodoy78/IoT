import colorsys

import tinytuya

SOCKET_TIMEOUT = 3
SOCKET_RETRY_LIMIT = 1


class BulbConnectionError(Exception):
    pass


def _client(bulb):
    device = tinytuya.BulbDevice(
        dev_id=bulb.device_id,
        address=bulb.ip_address,
        local_key=bulb.local_key,
        version=float(bulb.version),
        connection_timeout=SOCKET_TIMEOUT,
    )
    device.set_socketTimeout(SOCKET_TIMEOUT)
    device.set_socketPersistent(False)
    device.set_socketRetryLimit(SOCKET_RETRY_LIMIT)
    return device


def _connection_error(bulb, detail):
    return BulbConnectionError(
        f"No se pudo conectar con ‘{bulb.name}’ en {bulb.ip_address}: {detail}"
    )


def get_status(bulb):
    device = _client(bulb)
    result = device.status()
    if not isinstance(result, dict) or "dps" not in result:
        detail = result.get("Error") if isinstance(result, dict) else "sin respuesta del dispositivo"
        raise _connection_error(bulb, detail)
    return result["dps"]


def _run_command(bulb, action):
    device = _client(bulb)
    result = action(device)
    if isinstance(result, dict) and "Error" in result:
        raise _connection_error(bulb, result["Error"])


def turn_on(bulb):
    _run_command(bulb, lambda device: device.turn_on())


def turn_off(bulb):
    _run_command(bulb, lambda device: device.turn_off())


def set_brightness(bulb, percentage):
    _run_command(bulb, lambda device: device.set_brightness_percentage(percentage))


def set_colortemp(bulb, percentage):
    _run_command(bulb, lambda device: device.set_colourtemp_percentage(percentage))


def set_color(bulb, r, g, b):
    _run_command(bulb, lambda device: device.set_colour(r, g, b))


def _colour_data_to_hex(colour_data):
    if not colour_data or len(colour_data) < 12:
        return "#ffffff"
    try:
        h = int(colour_data[0:4], 16)
        s = int(colour_data[4:8], 16)
        v = int(colour_data[8:12], 16)
    except ValueError:
        return "#ffffff"
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360, min(s, 1000) / 1000, min(v, 1000) / 1000)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def summarize(dps):
    switch = dps.get("20", dps.get("1", False))
    bright_raw = dps.get("22", dps.get("3", 0)) or 0
    temp_raw = dps.get("23", dps.get("4", 0)) or 0
    colour_data = dps.get("24", dps.get("5"))
    return {
        "on": bool(switch),
        "brightness_pct": max(1, min(100, round(bright_raw / 1000 * 100))),
        "colortemp_pct": max(0, min(100, round(temp_raw / 1000 * 100))),
        "color_hex": _colour_data_to_hex(colour_data),
    }
