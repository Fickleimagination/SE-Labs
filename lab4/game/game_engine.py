import pygame
import random
import sys
from .hole import Hole

# Game Engine

DARK_BROWN = (60, 40, 20)
MOLE_BROWN = (140, 95, 55)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

DIFFICULTIES = {
    "easy":   {"spawn_chance": 0.012, "mole_up_frames": 60},
    "medium": {"spawn_chance": 0.02,  "mole_up_frames": 45},
    "hard":   {"spawn_chance": 0.035, "mole_up_frames": 30},
}

class GameEngine:
    def __init__(self, width, height, rows=3, cols=3):
        self.width = width
        self.height = height
        self.rows = rows
        self.cols = cols

        self.font = pygame.font.SysFont("Arial", 28)
        self.big_font = pygame.font.SysFont("Arial", 48)

        self.state = "playing"  # "playing" -> "game_over" -> "difficulty_select" -> "playing"
        self._start_round("medium")

    def _build_holes(self):
        self.holes = []
        spacing_x = self.width // (self.cols + 1)
        spacing_y = (self.height - 80) // (self.rows + 1)
        for r in range(self.rows):
            for c in range(self.cols):
                cx = spacing_x * (c + 1)
                cy = 80 + spacing_y * (r + 1)
                self.holes.append(Hole(cx, cy))

    def _start_round(self, difficulty):
        settings = DIFFICULTIES[difficulty]
        self.difficulty = difficulty
        self.spawn_chance = settings["spawn_chance"]
        self.mole_up_frames = settings["mole_up_frames"]

        self._build_holes()
        self.round_seconds = 30
        self.time_left_frames = self.round_seconds * 60
        self.score = 0
        self.misses = 0
        self.state = "playing"

    @property
    def game_over(self):
        # Kept for any external code/tests that still check this flag.
        return self.state != "playing"

    def handle_event(self, event):
        if self.state == "playing":
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(event.pos)

        elif self.state == "game_over":
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.state = "difficulty_select"

        elif self.state == "difficulty_select":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    self._start_round("easy")
                elif event.key == pygame.K_m:
                    self._start_round("medium")
                elif event.key == pygame.K_h:
                    self._start_round("hard")
                elif event.key == pygame.K_x:
                    pygame.quit()
                    sys.exit()

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
        if self.state != "playing":
            return

        self.time_left_frames -= 1
        if self.time_left_frames <= 0:
            self.state = "game_over"
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

        if self.state == "game_over":
            self._render_game_over(screen)
        elif self.state == "difficulty_select":
            self._render_difficulty_select(screen)

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

    def _render_difficulty_select(self, screen):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        title_text = self.big_font.render("Play Again?", True, WHITE)
        title_rect = title_text.get_rect(center=(self.width // 2, self.height // 2 - 80))
        screen.blit(title_text, title_rect)

        options = [
            "[E] Easy",
            "[M] Medium",
            "[H] Hard",
            "[X] Exit",
        ]
        for i, option in enumerate(options):
            opt_text = self.font.render(option, True, WHITE)
            opt_rect = opt_text.get_rect(center=(self.width // 2, self.height // 2 - 20 + i * 36))
            screen.blit(opt_text, opt_rect)