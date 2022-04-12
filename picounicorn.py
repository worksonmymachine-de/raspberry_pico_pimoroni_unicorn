# Dummy implementation of the picounicorn API with some optional debug and test features.

# Toggle any print statements for debugging here or use dummy_logging_off / dummy_logging_on
# (don't forget to remove the method calls to dummy* from your code before deploying on Pico)
# Default it is turned off. When enabled it prints out which rbg color at which (LED )coords
# was set and if you did call init or not - or multiple times.
# Button pressed states (A is pressed) can be simulated by dummy_set_button_state(BUTTON_A, True)
# Every single button can be simulated and the dummy_reset_buttons() method can be used to reset
# all buttons to False (e.g. in unit tests)

_WIDTH = 16
_HEIGHT = 7
_init_called = False
_logging_on = False

_x_range = (0, 6)
_y_range = (0, 15)
_rgb_range = (0, 255)

BUTTON_A = "A"
BUTTON_B = "B"
BUTTON_X = "X"
BUTTON_Y = "Y"

_buttons = {
    BUTTON_A: False,
    BUTTON_B: False,
    BUTTON_X: False,
    BUTTON_Y: False,
}


def init():
    if _logging():
        global _init_called
        if _init_called:
            _log("picounicorn.init() was already called!")
        else:
            _init_called = True
            _log("picounicorn.init() called")


def get_width() -> int:
    if _logging():
        _ensure_init_called()
    return _WIDTH


def get_height() -> int:
    if _logging():
        _ensure_init_called()
    return _HEIGHT


def set_pixel(x: int, y: int, r: int, b: int, g: int) -> None:
    if _logging():
        _ensure_init_called()
        coords_valid = _coords_valid(x, y)
        rgb_values_valid = _rgb_values_valid(r, g, b)
        if coords_valid and rgb_values_valid:
            _log(f"picounicorn.set_pixel() called: coords={x},{y} rgb={r},{g},{b}")
        elif not coords_valid:
            _log(f"ERROR: coordinates {x},{y} invalid - should be in range x:{_x_range} and y:{_y_range}")
        elif not rgb_values_valid:
            _log(f"ERROR: rgb values {r},{g},{b} invalid - should be in range {_rgb_range}")


def set_pixel_value(x: int, y: int, v: int) -> None:
    if _logging():
        _ensure_init_called()
        coords_valid = _coords_valid(x, y)
        rgb_value_valid = _rgb_value_valid(v)
        if coords_valid and rgb_value_valid:
            _log(f"picounicorn.set_pixel_value() called: coords={x},{y} v={v}")
        elif not coords_valid:
            _log(f"ERROR: coordinates {x},{y} invalid - should be in range x:{_x_range} and y:{_y_range}")
        elif not rgb_value_valid:
            _log(f"ERROR: rgb value {v} invalid - should be in range {_rgb_range}")


def is_pressed(button_key: str) -> bool:
    return _buttons.get(button_key)


def _logging() -> bool:
    return _logging_on


def _ensure_init_called() -> None:
    if not _init_called:
        _log("ERROR: Call picounicorn.init() first!")


def _coords_valid(x: int, y: int) -> bool:
    return x in _x_range and y in _y_range


def _rgb_values_valid(r: int, g: int, b: int) -> bool:
    return _rgb_value_valid(r) and _rgb_value_valid(g) and _rgb_value_valid(b)


def _rgb_value_valid(v: int) -> bool:
    return v in _rgb_range


def _log(msg: str) -> None:
    print(msg)


def dummy_logging_off():
    global _logging_on
    _logging_on = False


def dummy_logging_on():
    global _logging_on
    _logging_on = True


def dummy_set_button_state(button_key: str, state: bool) -> None:
    if _logging():
        _log(f"setting button {button_key} to pressed state {state}")
    _buttons.update({button_key: state})


def dummy_reset_buttons() -> None:
    if _logging():
        _log("resetting all buttons to pressed state False")
    for key in _buttons.keys():
        _buttons.update({key: False})
