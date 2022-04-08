import uasyncio
import random

import picounicorn

# triggers:
TRIGGER_STOP = 0
TRIGGER_RUN = 1
TRIGGER_TOGGLE_A = 2
TRIGGER_TOGGLE_B = 3
TRIGGER_TOGGLE_C = 4

# pico unicorn constants
WIDTH = 16
HEIGHT = 7

# current interrupt
ACTIVE_TRIGGER = TRIGGER_RUN


def _next_index_and_value(values: [], current_index: int) -> (int, tuple):
    return (current_index + 1, values[current_index + 1]) if current_index + 1 < len(values) else (0, values[0])


def _random_length(limit: (int, int)) -> int:
    return random.randint(limit[0], limit[1])


def init_picounicorn() -> None:
    picounicorn.init()
    for x in range(picounicorn.get_width()):
        for y in range(picounicorn.get_height()):
            picounicorn.set_pixel(x, y, 0, 0, 0)


class Matrix:
    LENGTH_PREFIX = (7, 17)  # shifting up beginning of matrix line to the top or above

    # the lower the value the faster it moves
    delays = (0.256, 0.128, 0.098, 0.064, 0.032, 0.020, 0.010)

    # color combinations - rbg values for start, body and gap
    black = (0, 0, 0)
    colors = (
        ((0, 120, 0), (0, 40, 0), black), # green
        ((180, 0, 0), (70, 0, 0), black), # red
        ((0, 0, 120), (0, 0, 50), black), # blue
        ((80, 80, 80), (30, 30, 30), black), # white
        ((0, 255, 0), (0, 90, 0), black), # bright_green
        ((255, 0, 0), (90, 0, 0), black), # bright_red
        ((0, 0, 255), (0, 0, 90), black), # bright_blue
        ((255, 255, 255), (100, 100, 100), black), # bright_white
        ((0, 60, 0), (0, 20, 0), black), # dark_green
        ((90, 0, 0), (25, 0, 0), black), # dark_red
        ((0, 0, 60), (0, 0, 25), black), # dark_blue
        ((50, 50, 50), (20, 20, 20), black), # dark_white
    )

    # lengths in dots of starting (bright) part, following dots and dots inbetween
    compositions = (((1, 1), (4, 15), (1, 3)),
                    ((1, 2), (7, 25), (2, 4)),
                    ((1, 1), (3, 10), (1, 2)),
                    ((1, 2), (4, 15), (0, 0)))

    def __init__(self):
        self.current_color_index, self.current_delay_index, self.current_composition_index = 0, 1, 0
        self.color = self.colors[self.current_color_index]
        self.delay = self.delays[self.current_delay_index]
        self.current_comp = self.compositions[self.current_composition_index]
        self.lines = self._init_lines()
        self.mode_trigger_methods = {TRIGGER_TOGGLE_A: self.switch_mode_a,
                                     TRIGGER_TOGGLE_B: self.switch_mode_b,
                                     TRIGGER_TOGGLE_C: self.switch_mode_c}

    async def switch_mode_a(self):
        self.current_color_index, self.color = _next_index_and_value(self.colors, self.current_color_index)

    async def switch_mode_b(self):
        self.current_delay_index, self.delay = _next_index_and_value(self.delays, self.current_delay_index)

    async def switch_mode_c(self):
        self.current_composition_index, self.current_comp = _next_index_and_value(self.compositions, self.current_composition_index)

    def _init_lines(self) -> []:
        lines = [_MatrixLine(lambda: self.current_comp, _random_length(self.LENGTH_PREFIX)) for _ in range(WIDTH)]
        return lines

    async def loop(self):
        global ACTIVE_TRIGGER
        while True:
            while ACTIVE_TRIGGER == TRIGGER_RUN:
                self._update_display()
                await uasyncio.sleep(self.delay)
            if TRIGGER_TOGGLE_A <= ACTIVE_TRIGGER <= TRIGGER_TOGGLE_C:
                await self.mode_trigger_methods.get(ACTIVE_TRIGGER)()
                ACTIVE_TRIGGER = TRIGGER_RUN
            await uasyncio.sleep(0)

    def _update_display(self):
        for x in range(WIDTH):
            for y, part in enumerate(self.lines[x].get_visible_dots()):
                r, g, b = self.colors[self.current_color_index][part]
                picounicorn.set_pixel(x, HEIGHT - 1 - y, r, g, b)


class _MatrixLine:
    def __init__(self, comp_supplier, shift: int) -> None:
        self.comp_supplier = comp_supplier
        self.current_comp_index = 0
        self.current_comp = self.comp_supplier()[self.current_comp_index]
        self.dots = [2 for _ in range(shift)] # initial shifting of line start to already have some variety in the beginning

    def get_visible_dots(self) -> []:
        while len(self.dots) < HEIGHT:
            self._add_dots()
        visible_dots = self.dots[0:HEIGHT]
        self.dots = self.dots[1:] # remove lowest dot from line
        return visible_dots

    def _add_dots(self) -> None:
        for _ in range(_random_length(self.comp_supplier()[self.current_comp_index])):
            self.dots.append(self.current_comp_index)
        self.current_comp_index, self.current_comp = _next_index_and_value(self.comp_supplier(), self.current_comp_index)


async def toggle_mode(trigger: int) -> None:
    global ACTIVE_TRIGGER
    ACTIVE_TRIGGER = trigger
    await uasyncio.sleep(0.3)


async def handle_buttons():
    while True:
        if picounicorn.is_pressed(picounicorn.BUTTON_A):
            await toggle_mode(TRIGGER_STOP) if ACTIVE_TRIGGER != TRIGGER_STOP else await toggle_mode(TRIGGER_RUN)
        if picounicorn.is_pressed(picounicorn.BUTTON_B):
            await toggle_mode(TRIGGER_TOGGLE_A)
        if picounicorn.is_pressed(picounicorn.BUTTON_X):
            await toggle_mode(TRIGGER_TOGGLE_B)
        if picounicorn.is_pressed(picounicorn.BUTTON_Y):
            await toggle_mode(TRIGGER_TOGGLE_C)
        await uasyncio.sleep(0.1)


if __name__ == "__main__":
    init_picounicorn()
    loop = uasyncio.get_event_loop()
    uasyncio.create_task(handle_buttons())
    uasyncio.create_task(Matrix().loop())
    loop.run_forever()

