from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from main import Board


class Display:
    screen_width: int
    screen_height: int
    tile_size: int

    def __init__(self, screen_size: (int, int), tile_size: int = 1):
        self.screen_width = screen_size[0]
        self.screen_height = screen_size[1]
        self.tile_size = tile_size
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width * tile_size, self.screen_height * tile_size))
        self.font = pygame.font.SysFont(None, 24)

    def display(self, board: "Board", paused: int = False):
        self.screen.fill((255, 255, 255))
        creatures = board.get_creatures()
        for creature in creatures:
            location = creature.get_pos()
            pygame.draw.rect(
                surface=self.screen,
                rect=(location[0] * self.tile_size, location[1] * self.tile_size, self.tile_size, self.tile_size),
                color=creature.color
            )
        gen_count = self.font.render(f"gen: {board.get_gen()}", True, (0, 0, 0))
        self.screen.blit(gen_count, (2, 2))

        if paused:
            paused_text = self.font.render(f"paused", True, (255, 0, 0))
            self.screen.blit(paused_text, (2, (self.screen_height - 10) * self.tile_size))

        pygame.display.flip()

    def destroy(self):
        pygame.quit()
