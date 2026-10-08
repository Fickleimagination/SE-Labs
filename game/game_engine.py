import pygame
import random
from .hole import Hole

# Game Engine

DARK_BROWN = (60, 40, 20)
MOLE_BROWN = (140, 95, 55)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

class GameEngine:
    def __init__(self, width, height, rows=3, cols=3):
        self.width = width
        self.height = height

        self.holes = []
        spacing_x = width // (cols + 1)
        spacing_y = (height - 80) // (rows + 1)
        for r in range(rows):
            for c in range(cols):
                cx = spacing_x * (c + 1)
                cy = 80 + spacing_y * (r + 1)
                self.holes.append(Hole(cx, cy))

        self.spawn_chance = 0.02   # per-hole, per-frame chance to pop up
        self.mole_up_frames = 45   # how long a mole stays up if not whacked

        self.round_seconds = 30
        self.time_left_frames = self.round_seconds * 60

        self.score = 0
        self.misses = 0
        self.font = pygame.font.SysFont("Arial", 28)
        self.big_font = pygame.font.SysFont("Arial", 48)
        self.game_over = False

    def handle_event(self, event):
        if self.game_over:
            # Game-over screen just waits for any key/click; nothing
            # else to do here until Task 3 adds a replay option.
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_click(event.pos)

    def _handle_click(self, pos):
        candidates = [hole for hole in self.holes if hole.rect().collidepoint(pos)]

        if not candidates:
            self.misses += 1
            return

        click_x, click_y = pos
        closest_hole = min(
            candidates,
            key=lambda h: (h.center_x - click_x) ** 2 + (h.center_y - click_y) ** 2,
        )

        if closest_hole.whack():
            self.score += 1
        else:
            self.misses += 1

    def handle_input(self):
        pass

    def update(self):
        if self.game_over:
            return

        self.time_left_frames -= 1
        if self.time_left_frames <= 0:
            self.game_over = True
            return

        for hole in self.holes:
            hole.update()
            if not hole.active and random.random() < self.spawn_chance:
                hole.pop_up(self.mole_up_frames)

    def render(self, screen):
        for hole in self.holes:
            pygame.draw.circle(screen, DARK_BROWN, (hole.center_x, hole.center_y), 40)
            if hole.active:
                pygame.draw.circle(screen, MOLE_BROWN, (hole.center_x, hole.center_y), 32)

        score_text = self.font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        seconds_left = max(0, self.time_left_frames // 60)
        timer_text = self.font.render(f"Time: {seconds_left}s", True, BLACK)
        screen.blit(timer_text, (self.width - 140, 10))

        if self.game_over:
            self._render_game_over(screen)

    def _render_game_over(self, screen):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title_text = self.big_font.render("Game Over", True, WHITE)
        title_rect = title_text.get_rect(center=(self.width // 2, self.height // 2 - 40))
        screen.blit(title_text, title_rect)

        score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(self.width // 2, self.height // 2 + 10))
        screen.blit(score_text, score_rect)

        hint_text = self.font.render("Press any key to continue", True, WHITE)
        hint_rect = hint_text.get_rect(center=(self.width // 2, self.height // 2 + 50))
        screen.blit(hint_text, hint_rect)