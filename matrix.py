import random
from app import App
import uasyncio
import picounicorn

WIDTH, HEIGHT = 16, 7  # pico unicorn constants
START, BODY, GAP = 0, 1, 2  # line parts
line_parts = (START, BODY, GAP)

delays = (  # the lower the value the faster it moves
    (0.2, 0.4), (0.1, 0.2), (0.07, 0.1), (0.05, 0.07), (0.03, 0.05), (0.02, 0.03), (0.01, 0.02), (0.005, 0.01))

_black = (0, 0, 0)  # color combinations - rbg values for start, body and gap
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
compositions = (((1, 1), (4, 15), (1, 3)),  # medium long, short start
                ((1, 3), (7, 25), (2, 4)),  # longer start and lines
                ((1, 2), (4, 15), (0, 0)),  # no gap
                ((1, 1), (3, 10), (1, 2)),  # shorter lines
                ((0, 0), (4, 15), (1, 3)),  # no start
                ((0, 0), (1, 2), (3, 10)),  # rain drops with long gap
                ((0, 0), (1, 1), (10, 30)),  # small rain drops with very long gap
                ((0, 0), (0, 1), (20, 50)),  # very few small rain drops with very long gap
                ((1, 1), (0, 0), (10, 30)),  # small shiny rain drops with very long gap
                ((0, 1), (0, 0), (20, 50)))  # very few shiny small rain drops with very long gap

# directions in which the lines will scroll
downwards, upwards = lambda y: HEIGHT - 1 - y, lambda y: y
directions = (lambda: downwards, lambda: upwards, lambda: random.choice((downwards, upwards)))


def next_index(values: (), current_index: int) -> int:
    return current_index + 1 if current_index + 1 < len(values) else 0


def random_range(limit: (int, int)) -> int:
    return random.randint(limit[0], limit[1])


def random_range_factor(limit: (float, float), factor=1000) -> float:
    return random_range((int(limit[0] * factor), int(limit[1] * factor))) / factor


class Matrix(App):
    def __init__(self, config=(0, 0, 2, 0)):
        print("init")
        self.direction_index, self.color_index, self.delay_index, self.composition_index = config
        self.lines = self._create_lines()
        self.active_trigger = None
        self.trigger_methods = {App.TRIGGER_1: self.cycle_colors, App.TRIGGER_2: self.cycle_scrolling_speeds,
                                App.TRIGGER_3: self.cycle_scrolling_directions, App.TRIGGER_4: self.cycle_line_compositions,
                                App.TRIGGER_EXIT: self.end_tasks}
        self.matrix_cache = [[GAP for _1 in range(HEIGHT)] for _2 in range(WIDTH)]
        self.tasks = self._create_tasks()

    async def trigger(self, trigger: int) -> int():
        print(f"trigger: {trigger}")
        self.active_trigger = trigger
        if trigger in App.mode_triggers:
            await self.trigger_methods.get(trigger)()
            self.active_trigger = App.TRIGGER_RUN
        return self.active_trigger

    async def cycle_colors(self) -> None:
        self.color_index = next_index(colors, self.color_index)
        for x in range(WIDTH):  # instantly applying new color (not waiting for scrolling delay)
            self.update_line(x, self.matrix_cache[x], self.lines[x].dir_supplier, cache=False)

    async def cycle_scrolling_speeds(self) -> None:
        self.delay_index = next_index(delays, self.delay_index)
        for line in self.lines:  # applying new scrolling speed (delay)
            line.current_delay = random_range_factor(delays[self.delay_index])

    async def cycle_scrolling_directions(self) -> None:
        self.direction_index = next_index(directions, self.direction_index)
        for line in self.lines:  # applying new scrolling direction
            line.dir_supplier = directions[self.direction_index]()

    async def cycle_line_compositions(self) -> None:
        self.composition_index = next_index(compositions, self.composition_index)
        for x, line in enumerate(self.lines):  # shortening very long lines to see comp change earlier
            line.dots = line.dots[0: len(line.dots) - 20] if HEIGHT <= len(line.dots) >= 40 else line.dots

    async def end_tasks(self) -> None:
        for task in self.tasks:
            task.cancel()

    def _create_lines(self) -> []:
        print("creating lines")
        return [MatrixLine(x_coord=i, comp_supplier=lambda: compositions[self.composition_index],
                           delay_supplier=lambda: delays[self.delay_index],
                           dir_supplier=directions[self.direction_index](),
                           shift=random_range((HEIGHT, 17)),  # initial shift of line start
                           callback_show=self.update_line,
                           trigger_supplier=lambda: self.active_trigger) for i in range(WIDTH)]

    def _create_tasks(self) -> []:
        return [uasyncio.create_task(line.scroll()) for line in self.lines]

    def update_line(self, x: int, line: [], direction_supplier, cache=True) -> None:
        for y in range(HEIGHT):
            r, g, b = colors[self.color_index][line[y]]
            picounicorn.set_pixel(x, direction_supplier(y), r, g, b)  # shifting up lines to the top of picounicorn
        if cache:
            self.matrix_cache[x] = line


class MatrixLine:
    def __init__(self, x_coord: int, comp_supplier, delay_supplier, dir_supplier, shift: int, callback_show, trigger_supplier) -> None:
        self.x_coord = x_coord
        self.delay_supplier = delay_supplier
        self.current_delay = random_range_factor(self.delay_supplier())
        self.dir_supplier = dir_supplier
        self.comp_supplier = comp_supplier
        self.current_comp_index = 0
        self.dots = [GAP for _ in range(shift)]  # initial shift of line start for diversity at start
        self.callback_show = callback_show
        self.trigger_supplier = trigger_supplier

    def _randomize_scrolling_speed(self) -> None:
        if self.current_comp_index == START:  # randomizing when we just added a start part to the line
            self.current_delay = random_range_factor(self.delay_supplier())

    def _add_dots(self) -> None:
        for _ in range(random_range(self.comp_supplier()[self.current_comp_index])):
            self.dots.append(line_parts[self.current_comp_index])
        self.current_comp_index = next_index(self.comp_supplier(), self.current_comp_index)

    async def scroll(self) -> None:
        while True:
            while self.trigger_supplier() == App.TRIGGER_RUN:
                self.dots.pop(0)  # remove first dot from line for scrolling
                while len(self.dots) < HEIGHT:  # lengthen line if too short for display
                    self._add_dots()
                    self._randomize_scrolling_speed()
                self.callback_show(self.x_coord, self.dots, self.dir_supplier)
                await uasyncio.sleep(self.current_delay)
            await uasyncio.sleep(0)
