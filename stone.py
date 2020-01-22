from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.vector import Vector
from itertools import product
from random import choice, random

GRAVITY = .02
FRICTION = .9
CHISEL_RADIUS = 6e-4
DISLODGE_VELOCITY = 1e-7
MAX_VELOCITY = 1e-6
PEBBLE_RADIUS = 1.7
PEBBLE_COUNT = 1e4
PEBBLE_SEGMENTS = 4
PEBBLE_COLORS = ((0.910, 0.784, 0.725),
                 (0.549, 0.514, 0.502),
                 (0.953, 0.816, 0.667),
                 (0.820, 0.694, 0.592),
                 (0.831, 0.796, 0.761),
                 (0.435, 0.329, 0.282),
                 (0.384, 0.207, 0.125))
POWER_SCALE = 1e-3

def pebble_positions():
    pebble_count = int(PEBBLE_COUNT**.5)
    x_scale, y_scale = .5 / pebble_count, .75 / pebble_count
    x_offset = .25
    for y in range(pebble_count - 10):
        x_offset += (random() - .5) / 40
        for x in range(pebble_count):
            yield x_offset + x_scale * x, .001 + y_scale * y

    # Taper the top a bit to look more natural
    x_length = .5
    for y in range(y, y + 10):
        x_length *= .85
        pebble_count = int(pebble_count * .83)
        new_x_offset = (1 - x_length) / 2 + (x_offset - .25)
        x_scale = x_length / pebble_count
        for x in range(pebble_count):
            yield new_x_offset + x_scale * x, .001 + y_scale * y

class Pebble:
    def __init__(self, index, x, y, circles, x_dim, y_dim):
        self.index = index
        self.x, self.y = x, y
        self.circles = circles
        self.x_dim, self.y_dim = x_dim, y_dim
        self.__velocity = 0.0, 0.0
        self.update = Clock.schedule_interval(self.step, 0)
        self.update.cancel()

    @property
    def velocity(self):
        return self.__velocity

    @velocity.setter
    def velocity(self, velocity_):
        """Start falling if velocity is over a certain threshold, else do nothing."""
        x, y = velocity_
        magnitude = (x**2 + y**2)**.5
        if magnitude < DISLODGE_VELOCITY:
            return
        if magnitude > MAX_VELOCITY:
            x *= MAX_VELOCITY / magnitude
            y *= MAX_VELOCITY / magnitude
        self.__velocity = velocity_
        self.update()

    def step(self, dt):
        """Gravity Physics"""
        x, y = self.x, self.y
        vx, vy = self.__velocity
        vx *= FRICTION
        vy *= FRICTION
        vy -= GRAVITY

        # Bounce off walls
        if not 0 < x < 1:
            vx *= -1
        if y > 1:
            vy *= -1

        self.x, self.y = x + vx, max(0, y + vy)

        self.circles[self.index].circle = (self.x * self.x_dim, self.y * self.y_dim,
                                           PEBBLE_RADIUS, 0, 360, PEBBLE_SEGMENTS)

        if not self.y:
            self.__velocity = 0.0, 0.0
            self.update.cancel()
        else:
            self.__velocity = vx, vy


class Chisel(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.size = self.parent.size if self.parent else Window.size

        self.circles = []
        self.pebbles = []
        with self.canvas:
            for index, (x, y) in enumerate(pebble_positions()):
                Color(*choice(PEBBLE_COLORS))
                self.circles.append(Line(circle=(x * self.width, y * self.height,
                                                 PEBBLE_RADIUS, 0, 360, PEBBLE_SEGMENTS),
                                         width=PEBBLE_RADIUS))
                self.pebbles.append(Pebble(index, x, y, self.circles, self.width, self.height))

        (self.parent if self.parent else Window).bind(size=self.resize)

    def resize(self, *args):
        self.size = self.parent.size if self.parent else Window.size
        for i, pebble in enumerate(self.pebbles):
            self.circles[i].circle = (pebble.x * self.width, pebble.y * self.height,
                                      PEBBLE_RADIUS, 0, 360, PEBBLE_SEGMENTS)

    def poke_power(self, touch_pos, pebble_x, pebble_y):
        """
        Returns the force vector of a poke.
        """
        tx, ty = touch_pos
        dx, dy = pebble_x - tx, pebble_y - ty
        distance = dx**2 + dy**2
        if distance > CHISEL_RADIUS:
            return 0.0, 0.0
        if not distance:
            distance = .0001
        power = POWER_SCALE / distance
        return power * dx, power * dy

    def poke(self, touch):
        """
        Apply a poke to each pebble.
        """
        for pebble in self.pebbles:
            pebble.velocity = self.poke_power(touch.spos, pebble.x, pebble.y)

    def on_touch_down(self, touch):
        self.poke(touch)
        return True

    def on_touch_move(self, touch):
        self.poke(touch)
        return True


if __name__ == '__main__':
    class ChiselApp(App):
        def build(self):
            return Chisel()
    ChiselApp().run()
