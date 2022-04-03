# Dummy implementation of the picounicorn API with some optional debug feats.

__init_called = False
__WIDTH = 16
__HEIGHT = 7

# Toggle any print statements for debugging here or use dummy_shut_up / dummy_talk_to_the_hand
# (don't forget to remove the method calls to dummy* from your code before deploying on Pico)
# Default it is turned off. When enabled it prints out which rbg color at which (LED )coords
# was set and if you did call init or not - or multiple times.
__shut_up_dummy = True

BUTTON_A = "A"
BUTTON_B = "B"
BUTTON_X = "X"
BUTTON_Y = "Y"

buttons = {
    BUTTON_A: False,
    BUTTON_B: False,
    BUTTON_X: False,
    BUTTON_Y: False,
}

def init():
    global __init_called
    if not __init_called:
        __init_called = True
    elif __init_called and not __shut_up_dummy:
        print("picounicorn.init() was already called!")


def __ensure_init_called() -> None:
    if not __init_called and not __shut_up_dummy:
        print("Call picounicorn.init() first!")


def get_width() -> int:
    __ensure_init_called()
    return __WIDTH


def get_height() -> int:
    __ensure_init_called()
    return __HEIGHT


def set_pixel(x: int, y: int, r: int, b: int, g: int) -> None:
    __ensure_init_called()
    if not __shut_up_dummy:
        print(f"picounicorn.set_pixel() called: x={x}, y={y}, rgb={r},{g},{b}")


def set_pixel_value(x: int, y: int, v: int) -> None:
    __ensure_init_called()
    if not __shut_up_dummy:
        print(f"picounicorn.set_pixel_value() called: x={x}, y={y}, v={v}")
        
def is_pressed(buttonKey: String) -> bool:
    return buttons.get(buttonKey)

def dummy_shut_up():
    global __shut_up_dummy
    __shut_up_dummy = True


def dummy_talk():
    global __shut_up_dummy
    __shut_up_dummy = False
    
def dummy_set_button_state(buttonKey: String, state: bool) -> None:
    buttons.update({buttonKey: state})
    
def dummy_reset_buttons() -> None:
    {buttons.update({key: False}) for key in buttons.keys()}
