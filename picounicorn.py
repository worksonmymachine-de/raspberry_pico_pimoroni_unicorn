# Dummy implementation of the picounicorn API with some optional debug and test features.

# Toggle any print statements for debugging here or use dummy_logging_off / dummy_logging_on
# (don't forget to remove the method calls to dummy* from your code before deploying on Pico)
# Default it is turned off. When enabled it prints out which rbg color at which (LED )coords
# was set and if you did call init or not - or multiple times.
# Button pressed states (A is pressed) can be simulated by dummy_set_button_state(BUTTON_A, True)
# Every single button can be simulated and the dummy_reset_buttons() method can be used to reset
# all buttons to False (e.g. in unit tests)

_init_called = False
_WIDTH = 16
_HEIGHT = 7
_logging_on = False

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
    global _init_called
    if not _init_called:
        _init_called = True
    elif _init_called and _logging():
        print("picounicorn.init() was already called!")


def _ensure_init_called() -> None:
    if not _init_called and _logging():
        print("Call picounicorn.init() first!")


def get_width() -> int:
    _ensure_init_called()
    return _WIDTH


def get_height() -> int:
    _ensure_init_called()
    return _HEIGHT


def set_pixel(x: int, y: int, r: int, b: int, g: int) -> None:
    _ensure_init_called()
    if _logging():
        print(f"picounicorn.set_pixel() called: x={x}, y={y}, rgb={r},{g},{b}")


def set_pixel_value(x: int, y: int, v: int) -> None:
    _ensure_init_called()
    if _logging():
        print(f"picounicorn.set_pixel_value() called: x={x}, y={y}, v={v}")


def is_pressed(button_key: str) -> bool:
    return _buttons.get(button_key)


def _logging() -> bool:
    return _logging_on


def dummy_logging_off():
    global _logging_on
    _logging_on = False


def dummy_logging_on():
    global _logging_on
    _logging_on = True


def dummy_set_button_state(button_key: str, state: bool) -> None:
    if _logging():
        print(f"setting button {button_key} to pressed state {state}")
    _buttons.update({button_key: state})


def dummy_reset_buttons() -> None:
    if _logging():
        print("resetting all buttons to pressed state False")
    for key in _buttons.keys():
        _buttons.update({key: False})
