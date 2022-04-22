import picounicorn
import uasyncio
import matrix


class App:
    """"
    base class for apps for communication between Appster and App
    """

    # triggers - used for program control in async environment
    TRIGGER_EXIT, TRIGGER_PAUSE, TRIGGER_RUN, TRIGGER_1, TRIGGER_2, TRIGGER_3, TRIGGER_4 = -1, 0, 1, 2, 3, 4, 5
    mode_triggers = (TRIGGER_EXIT, TRIGGER_1, TRIGGER_2, TRIGGER_3, TRIGGER_4)
    ACTIVE_TRIGGER = TRIGGER_RUN

    async def trigger(self, trigger: int) -> int():
        pass


class UnicornAppManager:

    def __init__(self, apps: [], current_app_index=0):
        self.apps = apps
        self.current_app_index = current_app_index
        self.current_app = None

    async def start(self):
        UnicornAppManager.init_unicorn()
        self.current_app = self.apps[self.current_app_index]()
        await self.current_app.trigger(App.TRIGGER_RUN)
        loop = uasyncio.get_event_loop()
        uasyncio.create_task(self.handle_buttons())
        loop.run_forever()

    async def next_app(self) -> None:
        self.current_app = self.apps[next_index(self.apps, self.current_app_index)]()
        await uasyncio.sleep(1)

    async def handle_buttons(self) -> None:
        while True:
            if picounicorn.is_pressed(picounicorn.BUTTON_A) and picounicorn.is_pressed(picounicorn.BUTTON_X):
                await self.current_app.trigger(App.TRIGGER_EXIT)
                self.reset_display()
                await self.next_app()
                await self.current_app.trigger(App.TRIGGER_RUN)
            if picounicorn.is_pressed(picounicorn.BUTTON_A) and picounicorn.is_pressed(picounicorn.BUTTON_B):
                await self.set_trigger(App.TRIGGER_PAUSE)
                self.reset_display()
            while picounicorn.is_pressed(picounicorn.BUTTON_A):
                await self.set_trigger(App.TRIGGER_1)
            while picounicorn.is_pressed(picounicorn.BUTTON_B):
                await self.set_trigger(App.TRIGGER_2)
            while picounicorn.is_pressed(picounicorn.BUTTON_X):
                await self.set_trigger(App.TRIGGER_3)
            while picounicorn.is_pressed(picounicorn.BUTTON_Y):
                await self.set_trigger(App.TRIGGER_4)
            await uasyncio.sleep(0.1)

    async def set_trigger(self, trigger: int) -> None:
        await self.current_app.trigger(trigger)
        await uasyncio.sleep(0.3)

    @staticmethod
    def init_unicorn() -> None:
        picounicorn.init()
        UnicornAppManager.reset_display()

    @staticmethod
    def reset_display() -> None:
        for x in range(picounicorn.get_width()):
            for y in range(picounicorn.get_height()):
                picounicorn.set_pixel_value(x, y, 0)


def next_index(values: (), current_index: int) -> int:
    return current_index + 1 if current_index + 1 < len(values) else 0


if __name__ == "__main__":
    available_apps = [matrix.Matrix]
    uam = UnicornAppManager(available_apps)
    uasyncio.run(uam.start())
