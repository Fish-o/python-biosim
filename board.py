import random
import time

import numpy as np

from creature import Creature

random = random.Random()

random.seed(1)


class Board:
    creatures: list[Creature]
    board_width: int
    board_height: int
    steps_per_generation: int
    creature_count: int
    generation: int
    step: int

    logs: list[Creature]

    def __init__(self, board_size: (int, int), steps_per_generation: int, creature_count: int, mut_fac: float):
        print("Main init")
        self.board_width = board_size[0]
        self.board_height = board_size[1]
        self.steps_per_generation = steps_per_generation
        self.creature_count = creature_count
        if self.creature_count % 2 != 0:
            self.creature_count -= 1
        self.init_creatures(mut_fac)
        self.generation = 0
        self.step = 0

    def get_all_free_spots(self):
        taken: list[tuple[int, int]] = []
        for creature in self.creatures:
            taken.append(creature.get_pos())
        available: list[tuple[int, int]] = []
        for x in range(self.board_width):
            for y in range(self.board_height):
                if (x, y) not in taken:
                    available.append((x, y))
        return available

    def get_free_spot_matrix(self) -> np.ndarray:
        matrix = np.empty((self.board_width, self.board_height), np.bool)
        matrix.fill(True)
        for creature in self.creatures:
            pos = creature.get_pos()
            # TODO: off by one error waiting to happen
            matrix.itemset((pos[0], pos[1]), False)
        return matrix

    def init_creatures(self, mut_fac: float):
        self.creatures = []
        free_spots = self.get_all_free_spots()
        random.shuffle(free_spots)
        for _ in range(self.creature_count):
            location = free_spots.pop()
            new_creature = Creature(location, [],
                                    (random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255)),
                                    mut_fac)
            self.creatures.append(new_creature)

    def get_creatures(self):
        return self.creatures

    def get_board_size(self):
        return self.board_width, self.board_height

    def get_steps_per_generation(self):
        return self.steps_per_generation

    def tick(self):
        start_tick = time.perf_counter()
        self.step += 1

        def create_arg(entity: Creature) -> tuple[Creature, "Board"]:
            return entity, self

        args: list[tuple[Creature, "Board"]] = list(map(create_arg, self.creatures))

        before_pool = time.perf_counter()
        result = map(Creature.tick, args)  # pool.map(Creature.tick, args)
        done_pool = time.perf_counter()

        before_free_tiles = time.perf_counter()
        # free_tiles = self.get_all_free_spots()
        free_tiles_matrix = self.get_free_spot_matrix()
        self.creatures = []
        starting_for_loop = time.perf_counter()
        for creature, new_pos in result:
            self.creatures.append(creature)
            if new_pos is None:
                continue
            old_pos = creature.get_pos()
            if free_tiles_matrix.item((new_pos[0], new_pos[1])):
                creature.set_pos(new_pos)
                free_tiles_matrix.itemset((old_pos[0], old_pos[1]), True)
                free_tiles_matrix.itemset((new_pos[0], new_pos[1]), False)

        moved_creatures = time.perf_counter()
        print(f"Tick duration : {moved_creatures - start_tick :0.4f}s")
        print(f"Pool          : {done_pool - beIfore_pool :0.4f}s")
        print(f"Free tiles    : {starting_for_loop - before_free_tiles  :0.4f}s")
        print(f"Moving        : {moved_creatures - done_pool :0.4f}s")
        print("")

    def tick_round(self):
        self.generation += 1
        # Kill half of the creatures from left to right on the screen
        sorted_creatures = sorted(self.creatures, key=lambda sorting_creature: sorting_creature.get_pos()[0],
                                  reverse=True)

        # Kill the creatures the furthest from the middle
        # sorted_creatures = sorted(self.creatures,
        #                           key=lambda sorting_creature: sorting_creature.distance_from_center(self),
        #                           reverse=True)

        # for index, creature in enumerate(sorted_creatures):
        #     creature.color = (index * 5, index * 5, index * 5)
        # self.creatures = sorted_creatures
        # screenn.display(self)
        # time.sleep(5)
        self.creatures = []
        for _ in range(round(self.creature_count / 2)):
            sorted_creatures.pop(0)
        free_spots = self.get_all_free_spots()
        random.shuffle(free_spots)
        for creature in sorted_creatures:
            new_creature = creature.reproduce()
            new_creature.set_pos(free_spots.pop())
            creature.set_pos(free_spots.pop())
            self.creatures.append(creature)
            self.creatures.append(new_creature)

    def get_gen(self):
        return self.generation

    def get_step(self):
        return self.step
