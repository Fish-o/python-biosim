import colorsys
import math
import random
from typing import Union, TYPE_CHECKING

from brain import Brain, Rotation, Connection

if TYPE_CHECKING:
    from main import Board

random = random.Random()

random.seed(1)


def will_get_out_of_bound(new_pos: tuple[int, int], screensize: tuple[int, int]) -> bool:
    if new_pos[0] < 0 or new_pos[0] >= screensize[0]:
        return True
    elif new_pos[1] < 0 or new_pos[1] >= screensize[1]:
        return True
    return False


class Creature:
    brain: Brain
    x: int
    y: int
    age: int
    color: tuple[int, int, int]
    rotation: int
    osc_period: int
    queued_move: Union[tuple[int, float], None]

    def __init__(self, location: tuple[int, int], connections: list[Connection], color: tuple[int, int, int],
                 mutation_factor: float = None):
        self.x = location[0]
        self.y = location[1]
        self.color = color
        self.age = 0
        self.osc_period = 20
        self.queued_move = None
        self.brain = Brain(self, connections, mutation_factor)
        self.rotation = random.choice([0, 1, 2, 3])

    def get_pos(self):
        return self.x, self.y

    def set_pos(self, pos: tuple[int, int]):
        self.x = pos[0]
        self.y = pos[1]

    def get_age(self):
        return self.age

    def get_rotation(self):
        return self.rotation

    # TODO: test if this function doesnt return 1 when in the bottom right corner
    # I named it get_distance_border_forward, but you can pass an optional parameter to set a custom rotation
    def get_distance_border_forward(self, board: "Board", rotation: Union[int, None] = None,
                                    disable_division: Union[bool, None] = None) -> Union[int, float]:
        board_size = board.get_board_size()
        rot: int = rotation or self.rotation
        if rot == Rotation.Left.value:
            if disable_division:
                return self.x
            return self.x / board.board_width
        elif rot == Rotation.Right.value:
            if disable_division:
                return board_size[0] - self.x
            return board_size[0] - self.x / board.board_width
        elif rot == Rotation.Up.value:
            if disable_division:
                return self.y
            return self.y / board.board_width
        elif rot == Rotation.Down.value:
            if disable_division:
                return board_size[1] - self.y
            return board_size[1] - self.y / board.board_width
        else:
            raise Exception("Rotation invalid")

    def get_distance_creature_forward(self, board: "Board") -> float:
        creatures = board.get_creatures()
        furthest = self.get_distance_border_forward(board, None, True)
        rot: int = self.rotation

        for creature in creatures:
            distance_tuple = self.get_distance_between_creature(creature)
            if distance_tuple == (0, 0):
                continue
            elif (rot == Rotation.Down.value or rot == Rotation.Up.value) and distance_tuple[1] == 0:
                furthest = min(furthest, abs(distance_tuple[0])) / board.board_height
            elif (rot == Rotation.Left.value or rot == Rotation.Right.value) and distance_tuple[0] == 0:
                furthest = min(furthest, abs(distance_tuple[0])) / board.board_width
        return furthest

    def get_distance_between_creature(self, creature: "Creature") -> (int, int):
        creature_loc = creature.get_pos()
        return self.x - creature_loc[0], self.y - creature_loc[1]

    def get_straight_distance_between_creature(self, creature: "Creature") -> float:
        creature_loc = creature.get_pos()
        distance_x = self.x - creature_loc[0]
        distance_y = self.y - creature_loc[1]
        return math.sqrt(distance_x ** 2 + distance_y ** 2)  # Pythagoras comes in handy once again

    def get_pop_density(self, board: "Board", radius: int, circular: bool) -> float:
        count = 0
        for creature in board.creatures:
            if circular and self.get_straight_distance_between_creature(creature) <= radius:
                count += 1
            elif not circular and max(*self.get_distance_between_creature(creature)) <= radius:
                count += 1

        if not circular:
            return count / ((radius * 2) ** 2)
        else:
            return count / (math.pi * (radius ** 2))

    def get_osc(self):
        phase = (self.age % self.osc_period) / self.osc_period  # 0.0..1.0
        #                              ^ o operator gets the remainder
        factor = -math.cos(phase * 2.0 * math.pi)
        assert ((factor >= -1.0) and (factor <= 1.0))
        factor += 1.0  # convert to 0.0..2.0
        factor /= 2.0  # convert to 0.0..1.0
        sensor_val = min(1.0, max(0.0, factor))  # floating point math is weird so this makes sure its 0.0..1.0
        return sensor_val

    def set_osc(self, value):
        new_period_0_1 = (math.tanh(value) + 1.0) / 2.0
        new_period = 1 + round(1.5 + math.exp(7.0 * new_period_0_1))
        assert ((new_period >= 2) and (new_period <= 2048))
        self.osc_period = new_period

    def move(self, direction: int, strength: float):
        if self.queued_move is None or self.queued_move[1] < strength:
            self.queued_move = (direction, strength)

    def distance_from_center(self, board: "Board"):
        x_distance = self.x - (board.board_width / 2)
        y_distance = self.y - (board.board_height / 2)
        return round(math.sqrt((x_distance ** 2) + (y_distance ** 2)))

    def get_new_pos(self, direction: int):
        new_x = self.x
        new_y = self.y
        if direction == Rotation.Up.value:
            new_y -= 1
        elif direction == Rotation.Down.value:
            new_y += 1
        elif direction == Rotation.Left.value:
            new_x -= 1
        elif direction == Rotation.Right.value:
            new_x += 1
        return new_x, new_y

    @staticmethod
    def tick(args: tuple["Creature", "Board"]) -> tuple["Creature", Union[None, tuple[int, int]]]:
        creature = args[0]
        board = args[1]
        creature.queued_move = None
        creature.brain.think(board)
        if not creature.queued_move:
            return creature, None
        new_pos = creature.get_new_pos(creature.queued_move[0])
        if will_get_out_of_bound(new_pos, board.get_board_size()):
            return creature, None
        elif new_pos == creature.get_pos():
            return creature, None
        return creature, new_pos

    def reproduce(self):
        def cloned_connections(connections: list[Connection]):
            res = []
            for conn in connections:
                res.append(
                    Connection.create_connection(cloned(conn.inputs), cloned(conn.weights), conn.bias, conn.output)
                )
            return res

        def cloned(li1: list[any]):
            li_copy = li1[:]
            return li_copy

        def cloned_tup(tup: tuple[int, int, int]):
            return tup[0], tup[1], tup[2]

        new_creature = Creature((self.get_pos()[0], self.get_pos()[1]),
                                cloned_connections(self.brain.get_connections()),
                                cloned_tup(self.color),
                                self.brain.get_mutation_factor())
        return new_creature

    def mutate_color(self, strength: int = 5):
        if random.random() < 0.95:
            return

        h, s, v = colorsys.rgb_to_hsv(self.color[0] / float(256), self.color[1] / float(256),
                                      self.color[2] / float(256))
        h += ((random.random() - 0.5) * 0.05)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)

        def clamp(color: int):
            return max(0, min(255, color))

        self.color = (
            clamp(round(r * 255)),
            clamp(round(g * 255)),
            clamp(round(b * 255)),
        )
        # self.color = (
        #     clamp(color[0] + random.randrange(-strength, strength), 0, 255),
        #     clamp(color[1] + random.randrange(-strength, strength), 0, 255),
        #     clamp(color[2] + random.randrange(-strength, strength), 0, 255)
        # )
