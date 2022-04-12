import uasyncio
import random
import picounicorn

# triggers:
TRIGGER_STOP = 0
TRIGGER_RUN = 1
TRIGGER_TOGGLE_A = 2
TRIGGER_TOGGLE_B = 3
TRIGGER_TOGGLE_C = 4

ACTIVE_TRIGGER = TRIGGER_RUN

# pico unicorn constants
WIDTH = 16
HEIGHT = 7

LENGTH_PREFIX = (HEIGHT, 17)  # shifting up beginning of matrix line to the top or above

# the lower the value the faster it moves
delays = (
    (0.2, 0.4), (0.1, 0.2), (0.07, 0.1), (0.05, 0.07), (0.03, 0.05), (0.02, 0.03), (0.01, 0.02), (0.005, 0.01))

# color combinations - rbg values for start, body and gap
_black = (0, 0, 0)
colors = (
    ((0, 120, 0), (0, 40, 0), _black),  # green
    ((180, 0, 0), (70, 0, 0), _black),  # red
    ((0, 0, 120), (0, 0, 50), _black),  # blue
    ((80, 80, 80), (30, 30, 30), _black),  # white
    ((0, 255, 0), (0, 90, 0), _black),  # bright_green
    ((255, 0, 0), (90, 0, 0), _black),  # bright_red
    ((0, 0, 255), (0, 0, 90), _black),  # bright_blue
    ((255, 255, 255), (100, 100, 100), _black),  # bright_white
    ((0, 60, 0), (0, 20, 0), _black),  # dark_green
    ((90, 0, 0), (25, 0, 0), _black),  # dark_red
    ((0, 0, 60), (0, 0, 25), _black),  # dark_blue
    ((50, 50, 50), (20, 20, 20), _black),  # dark_white
)

# lengths in dots of starting (bright) part, following dots and dots inbetween
compositions = (((1, 1), (4, 15), (1, 3)),
                ((1, 2), (7, 25), (2, 4)),
                ((1, 1), (3, 10), (1, 2)),
                ((1, 2), (4, 15), (0, 0)))


def next_index_and_value(values: [], current_index: int) -> (int, tuple):
    return (current_index + 1, values[current_index + 1]) if current_index + 1 < len(values) else (0, values[0])


def random_range(limit: (int, int)) -> int:
    return random.randint(limit[0], limit[1])


def random_range_factor(limit: (float, float), factor=1000) -> float:
    return random_range((int(limit[0] * factor), int(limit[1] * factor))) / factor


def create_matrix_cache() -> []:
    cache = []
    for _ in range(WIDTH):
        cache.append([[2, 2, 2, 2, 2, 2]])
    return cache


def init_picounicorn() -> None:
    picounicorn.init()
    for x in range(picounicorn.get_width()):
        for y in range(picounicorn.get_height()):
            picounicorn.set_pixel_value(x, y, 0)


class Matrix:
    def __init__(self):
        self.current_color_index, self.current_delay_index, self.current_composition_index = 0, 0, 0
        self.color = colors[self.current_color_index]
        self.delay = delays[self.current_delay_index]
        self.comp = compositions[self.current_composition_index]
        self.lines = self._create_lines()
        self.mode_trigger_methods = {TRIGGER_TOGGLE_A: self.cycle_colors,
                                     TRIGGER_TOGGLE_B: self.cycle_scrolling_speeds,
                                     TRIGGER_TOGGLE_C: self.cycle_line_compositions}
        self.matrix_cache = create_matrix_cache()
        self.start_loops()

    async def cycle_colors(self):
        self.current_color_index, self.color = next_index_and_value(colors, self.current_color_index)
        self.update_display()

    async def cycle_scrolling_speeds(self):
        self.current_delay_index, self.delay = next_index_and_value(delays, self.current_delay_index)
        self.update_scrolling_speeds()

    async def cycle_line_compositions(self):
        self.current_composition_index, self.comp = next_index_and_value(compositions,
                                                                         self.current_composition_index)

    def _create_lines(self) -> []:
        return [MatrixLine(i, lambda: self.comp, lambda: self.delay,
                           random_range(LENGTH_PREFIX), self.update_line) for i in range(WIDTH)]

    async def handle_toggle_triggers(self):
        global ACTIVE_TRIGGER
        while True:
            if TRIGGER_TOGGLE_A <= ACTIVE_TRIGGER <= TRIGGER_TOGGLE_C:
                await self.mode_trigger_methods.get(ACTIVE_TRIGGER)()
                ACTIVE_TRIGGER = TRIGGER_RUN
            await uasyncio.sleep(0)

    def start_loops(self):
        uasyncio.create_task(self.handle_toggle_triggers())
        for line in self.lines:
            uasyncio.create_task(line.scroll())

    def update_line(self, x: int, line: [], cache=True):
        for y, part in enumerate(line):
            r, g, b = colors[self.current_color_index][part]
            picounicorn.set_pixel(x, HEIGHT - 1 - y, r, g, b)  # shifting up lines to the top of picounicorn
        if cache:
            self.matrix_cache[x] = line

    def update_display(self):
        for x in range(WIDTH):
            self.update_line(x, self.matrix_cache[x], cache=False)

    def update_scrolling_speeds(self):
        for line in self.lines:
            line.current_delay = random_range_factor(delays[self.current_delay_index])


class MatrixLine:
    def __init__(self, x_coord: int, comp_supplier, delay_supplier, shift: int, callback_update_line) -> None:
        self.x_coord = x_coord
        self.delay_supplier = delay_supplier
        self.current_delay = random_range_factor(self.delay_supplier())
        self.comp_supplier = comp_supplier
        self.current_comp_index = 0
        self.current_comp = self.comp_supplier()[self.current_comp_index]
        self.dots = [2 for _ in
                     range(shift)]  # initial shifting of line start to already have some variety in the beginning
        self.callback_update_line = callback_update_line

    def _get_visible_dots(self) -> []:
        while len(self.dots) < HEIGHT:
            self._add_dots()
        visible_dots = self.dots[0:HEIGHT]
        self.dots = self.dots[1:]  # remove lowest dot from line
        return visible_dots

    def _add_dots(self) -> None:
        for _ in range(random_range(self.comp_supplier()[self.current_comp_index])):
            self.dots.append(self.current_comp_index)
        self.current_comp_index, self.current_comp = next_index_and_value(self.comp_supplier(), self.current_comp_index)
        if self.current_comp_index == 0:
            self._randomize_scrolling_speed()

    def _randomize_scrolling_speed(self) -> None:
        self.current_delay = random_range_factor(self.delay_supplier())

    async def scroll(self) -> None:
        while True:
            while ACTIVE_TRIGGER == TRIGGER_RUN:
                self.callback_update_line(self.x_coord, self._get_visible_dots())
                await uasyncio.sleep(self.current_delay)
            await uasyncio.sleep(0)


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
    Matrix()
    uasyncio.create_task(handle_buttons())
    loop.run_forever()
