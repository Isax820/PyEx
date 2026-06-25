import pygame
import threading
import random
import sys
import os

from rpc import *

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import pyex
    PYEX_AVAILABLE = True
except ImportError:
    PYEX_AVAILABLE = False

pygame.init()

WIDTH, HEIGHT = 900, 600
FPS = 60
GRAVITY = 0.6
JUMP_FORCE = -14
GROUND_Y = HEIGHT - 60

WHITE   = (255, 255, 255)
BLACK   = (10, 10, 15)
CYAN    = (0, 220, 255)
MAGENTA = (220, 0, 255)
YELLOW  = (255, 220, 0)
DARK    = (20, 20, 35)
GRAY    = (60, 60, 80)
RED     = (255, 60, 60)
GREEN   = (60, 255, 120)
ORANGE  = (255, 140, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEON RUN")
clock = pygame.time.Clock()

font_big   = pygame.font.SysFont("consolas", 64, bold=True)
font_med   = pygame.font.SysFont("consolas", 32, bold=True)
font_small = pygame.font.SysFont("consolas", 22)

thread_rpc = threading.Thread(target=run_rpc, daemon=True)
thread_rpc.start()

game_context = {
    "score": 0,
    "speed": 5.0,
    "lives": 3,
}

if PYEX_AVAILABLE:
    pyex.boot(screen=screen, clock=clock, game_context=game_context)

def draw_neon_rect(surface, color, rect, width=2, glow=6):
    for i in range(glow, 0, -1):
        alpha = int(80 / i)
        s = pygame.Surface((rect[2] + i*4, rect[3] + i*4), pygame.SRCALPHA)
        r = pygame.Rect(i*2, i*2, rect[2], rect[3])
        pygame.draw.rect(s, (*color, alpha), r, width + i)
        surface.blit(s, (rect[0] - i*2, rect[1] - i*2))
    pygame.draw.rect(surface, color, rect, width)

def draw_neon_text(surface, text, font, color, x, y, glow=4):
    for i in range(glow, 0, -1):
        alpha = int(100 / i)
        rendered = font.render(text, True, (*color, alpha))
        surface.blit(rendered, (x - i, y - i))
        surface.blit(rendered, (x + i, y + i))
    rendered = font.render(text, True, color)
    surface.blit(rendered, (x, y))

class Stars:
    def __init__(self):
        self.stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT - 80),
                       random.uniform(0.3, 1.5), random.uniform(0.5, 2.0)) for _ in range(120)]

    def update(self, speed):
        updated = []
        for x, y, s, brightness in self.stars:
            x -= speed * s * 0.4
            if x < 0:
                x = WIDTH
                y = random.randint(0, HEIGHT - 80)
            updated.append((x, y, s, brightness))
        self.stars = updated

    def draw(self, surface):
        for x, y, s, brightness in self.stars:
            c = max(0, min(255, int(brightness * 180)))
            pygame.draw.circle(surface, (c, c, min(255, c + 40)), (int(x), int(y)), max(1, int(s * 0.8)))

class Player:
    def __init__(self):
        self.w, self.h = 38, 48
        self.x = 120
        self.y = float(GROUND_Y - self.h)
        self.vy = 0
        self.on_ground = True
        self.jumps_left = 2
        self.trail = []
        self.alive = True
        self.invincible = 0
        self.flash = 0

    def jump(self):
        if self.jumps_left > 0:
            self.vy = JUMP_FORCE if self.jumps_left == 2 else JUMP_FORCE * 0.85
            self.jumps_left -= 1
            self.on_ground = False

    def update(self, platforms):
        self.vy += GRAVITY
        self.y += self.vy
        self.on_ground = False

        if self.y + self.h >= GROUND_Y:
            self.y = GROUND_Y - self.h
            self.vy = 0
            self.on_ground = True
            self.jumps_left = 2

        for p in platforms:
            if (self.vy > 0 and
                self.x + self.w > p.x and self.x < p.x + p.w and
                self.y + self.h >= p.y and self.y + self.h <= p.y + 20 + self.vy + 1):
                self.y = p.y - self.h
                self.vy = 0
                self.on_ground = True
                self.jumps_left = 2

        self.trail.append((self.x + self.w // 2, self.y + self.h // 2))
        if len(self.trail) > 12:
            self.trail.pop(0)

        if self.invincible > 0:
            self.invincible -= 1
        if self.flash > 0:
            self.flash -= 1

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def draw(self, surface):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(200 * (i / len(self.trail)))
            r = max(1, int(6 * (i / len(self.trail))))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 220, 255, alpha), (r, r), r)
            surface.blit(s, (tx - r, ty - r))

        if self.invincible > 0 and self.invincible % 6 < 3:
            return

        rect = (int(self.x), int(self.y), self.w, self.h)
        pygame.draw.rect(surface, (0, 40, 60), rect)
        draw_neon_rect(surface, CYAN, rect, width=2, glow=5)

        eye_x = int(self.x + self.w - 12)
        eye_y = int(self.y + 12)
        pygame.draw.circle(surface, CYAN, (eye_x, eye_y), 5)
        pygame.draw.circle(surface, WHITE, (eye_x, eye_y), 2)

        leg_offset = int(abs(self.vy) * 0.3)
        pygame.draw.line(surface, CYAN,
                         (int(self.x + 8), int(self.y + self.h)),
                         (int(self.x + 8), int(self.y + self.h + 8 + leg_offset)), 3)
        pygame.draw.line(surface, CYAN,
                         (int(self.x + 26), int(self.y + self.h)),
                         (int(self.x + 26), int(self.y + self.h + 8 - leg_offset)), 3)

class Obstacle:
    def __init__(self, speed):
        kind = random.choice(["spike", "tall", "wide", "spike"])
        self.kind = kind
        if kind == "spike":
            self.w, self.h = 30, 40
            self.color = MAGENTA
        elif kind == "tall":
            self.w, self.h = 24, 80
            self.color = RED
        else:
            self.w, self.h = 60, 28
            self.color = ORANGE
        self.x = float(WIDTH + 20)
        self.y = GROUND_Y - self.h
        self.speed = speed

    def update(self):
        self.x -= self.speed

    def get_rect(self):
        margin = 6
        return pygame.Rect(int(self.x) + margin, int(self.y) + margin,
                           self.w - margin*2, self.h - margin*2)

    def draw(self, surface):
        rect = (int(self.x), int(self.y), self.w, self.h)
        pygame.draw.rect(surface, (30, 0, 20), rect)
        if self.kind == "spike":
            pts = [
                (int(self.x), int(self.y + self.h)),
                (int(self.x + self.w // 2), int(self.y)),
                (int(self.x + self.w), int(self.y + self.h))
            ]
            pygame.draw.polygon(surface, (40, 0, 30), pts)
            pygame.draw.polygon(surface, self.color, pts, 2)
            for i in range(4, 0, -1):
                s = pygame.Surface((self.w + i*4, self.h + i*4), pygame.SRCALPHA)
                shifted = [(x - int(self.x) + i*2, y - int(self.y) + i*2) for x, y in pts]
                pygame.draw.polygon(s, (*self.color, 50//i), shifted, 2 + i)
                surface.blit(s, (int(self.x) - i*2, int(self.y) - i*2))
        else:
            draw_neon_rect(surface, self.color, rect, width=2, glow=5)

class Platform:
    def __init__(self, speed):
        self.w = random.randint(90, 180)
        self.h = 16
        self.x = float(WIDTH + 20)
        self.y = random.randint(HEIGHT - 220, HEIGHT - 120)
        self.speed = speed
        self.color = GREEN

    def update(self):
        self.x -= self.speed

    def draw(self, surface):
        rect = (int(self.x), int(self.y), self.w, self.h)
        pygame.draw.rect(surface, (0, 30, 15), rect)
        draw_neon_rect(surface, self.color, rect, width=2, glow=4)

class Coin:
    def __init__(self, speed):
        self.x = float(WIDTH + 20)
        self.y = float(random.randint(GROUND_Y - 200, GROUND_Y - 50))
        self.speed = speed
        self.r = 10
        self.angle = 0
        self.collected = False

    def update(self):
        self.x -= self.speed
        self.angle += 4

    def get_rect(self):
        return pygame.Rect(int(self.x) - self.r, int(self.y) - self.r, self.r*2, self.r*2)

    def draw(self, surface):
        squish = abs(pygame.math.Vector2(1, 0).rotate(self.angle).x)
        w = max(4, int(self.r * 2 * squish))
        rect = pygame.Rect(int(self.x) - w//2, int(self.y) - self.r, w, self.r*2)
        pygame.draw.ellipse(surface, (60, 50, 0), rect)
        for i in range(4, 0, -1):
            s = pygame.Surface((w + i*4, self.r*2 + i*4), pygame.SRCALPHA)
            inner = pygame.Rect(i*2, i*2, w, self.r*2)
            pygame.draw.ellipse(s, (*YELLOW, 50//i), inner, 2)
            surface.blit(s, (rect.x - i*2, rect.y - i*2))
        pygame.draw.ellipse(surface, YELLOW, rect, 2)

class Game:
    def __init__(self):
        self.reset()
        self.high_score = 0

    def reset(self):
        self.player     = Player()
        self.obstacles  = []
        self.platforms  = []
        self.coins      = []
        self.stars      = Stars()
        self.score      = 0
        self.distance   = 0
        self.speed      = 5.0
        self.frame      = 0
        self.spawn_timer= 0
        self.coin_timer = 0
        self.plat_timer = 0
        self.lives      = 3
        self.running    = True
        self.game_over  = False
        self.particles  = []

    def spawn_obstacle(self):  self.obstacles.append(Obstacle(self.speed))
    def spawn_platform(self):  self.platforms.append(Platform(self.speed))
    def spawn_coin(self):      self.coins.append(Coin(self.speed))

    def add_particles(self, x, y, color, n=12):
        for _ in range(n):
            angle = random.uniform(0, 360)
            spd   = random.uniform(2, 6)
            v     = pygame.math.Vector2(spd, 0).rotate(angle)
            life  = random.randint(20, 40)
            self.particles.append([float(x), float(y), v.x, v.y, life, life, color])

    def update_particles(self):
        alive = []
        for p in self.particles:
            p[0] += p[2]; p[1] += p[3]; p[3] += 0.2; p[4] -= 1
            if p[4] > 0:
                alive.append(p)
        self.particles = alive

    def draw_particles(self, surface):
        for p in self.particles:
            alpha = int(255 * (p[4] / p[5]))
            r = max(1, int(4 * (p[4] / p[5])))
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p[6], alpha), (r, r), r)
            surface.blit(s, (int(p[0]) - r, int(p[1]) - r))

    def draw_ground(self, surface):
        pygame.draw.rect(surface, DARK, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        for i in range(5, 0, -1):
            s = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
            s.fill((*CYAN, 40 // i))
            surface.blit(s, (0, GROUND_Y - i))
        pygame.draw.line(surface, CYAN, (0, GROUND_Y), (WIDTH, GROUND_Y), 2)
        grid_spacing = 60
        offset = int(self.distance * self.speed * 0.5) % grid_spacing
        for gx in range(-grid_spacing, WIDTH + grid_spacing, grid_spacing):
            s = pygame.Surface((1, HEIGHT - GROUND_Y), pygame.SRCALPHA)
            s.fill((*CYAN, 20))
            surface.blit(s, (gx - offset, GROUND_Y))

    def draw_hud(self, surface):
        draw_neon_text(surface, f"SCORE  {int(self.score):06d}", font_med, CYAN, 20, 16, glow=3)
        draw_neon_text(surface, f"BEST   {int(self.high_score):06d}", font_small, GRAY, 20, 56)
        draw_neon_text(surface, f"SPEED  x{self.speed:.1f}", font_small, YELLOW, WIDTH - 220, 16)
        for i in range(self.lives):
            cx, cy = WIDTH - 30 - i * 32, 56
            pygame.draw.circle(surface, (40, 0, 20), (cx, cy), 10)
            pygame.draw.circle(surface, MAGENTA, (cx, cy), 10, 2)
            for j in range(3, 0, -1):
                s = pygame.Surface((24, 24), pygame.SRCALPHA)
                pygame.draw.circle(s, (*MAGENTA, 40//j), (12, 12), 10)
                surface.blit(s, (cx - 12, cy - 12))

    def screen_title(self, surface):
        surface.fill(BLACK)
        self.stars.draw(surface)
        for text, font, color, y, glow in [
            ("NEON RUN",          font_big,   CYAN,    150, 8),
            ("PLATFORMER INFINI", font_med,   MAGENTA, 230, 4),
            ("SPACE / Z  =  JUMP  (double jump allowed)", font_small, YELLOW, 330, 0),
            ("Collect coins  •  Avoid obstacles",          font_small, WHITE,  365, 0),
        ]:
            draw_neon_text(surface, text, font, color, WIDTH//2 - font.size(text)[0]//2, y, glow=glow)
        if int(self.frame / 20) % 2:
            t = "PRESS ENTER TO START"
            draw_neon_text(surface, t, font_med, GREEN, WIDTH//2 - font_med.size(t)[0]//2, 450, glow=4)

    def screen_game_over(self, surface):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        for text, font, color, y, glow in [
            ("GAME OVER",                  font_big, RED,    160, 8),
            (f"SCORE : {int(self.score):06d}", font_med, YELLOW, 270, 4),
            (f"BEST : {int(self.high_score):06d}", font_med, CYAN, 320, 3),
        ]:
            draw_neon_text(surface, text, font, color, WIDTH//2 - font.size(text)[0]//2, y, glow=glow)
        if int(self.frame / 20) % 2:
            t = "ENTER = PLAY AGAIN"
            draw_neon_text(surface, t, font_med, GREEN, WIDTH//2 - font_med.size(t)[0]//2, 420, glow=4)

    def _draw_scene(self):
        screen.fill(BLACK)
        self.stars.draw(screen)
        self.draw_ground(screen)
        for obj in self.platforms + self.coins + self.obstacles:
            obj.draw(screen)
        self.player.draw(screen)
        self.draw_particles(screen)
        self.draw_hud(screen)
        if PYEX_AVAILABLE:
            pyex.draw(screen)

    def run(self):
        state = "title"

        while True:
            dt = clock.tick(FPS) / 1000.0
            self.frame += 1
            events = pygame.event.get()

            if PYEX_AVAILABLE:
                game_context["score"] = self.score
                game_context["speed"] = self.speed
                game_context["lives"] = self.lives
                pyex.update(events, dt)
                self.speed = game_context.get("speed", self.speed)

            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if state == "title" and event.key == pygame.K_RETURN:
                        self.reset(); state = "play"
                    elif state == "play" and event.key in (pygame.K_SPACE, pygame.K_z, pygame.K_UP, pygame.K_w):
                        self.player.jump()
                    elif state == "over" and event.key == pygame.K_RETURN:
                        self.reset(); state = "play"

            if state == "title":
                self.stars.update(2)
                screen.fill(BLACK)
                self.stars.draw(screen)
                self.screen_title(screen)
                if PYEX_AVAILABLE:
                    pyex.draw(screen)
                pygame.display.flip()
                continue

            if state == "play":
                game_context["speed"] = 5.0 + self.score * 0.003
                self.speed = game_context["speed"]
                self.distance += self.speed
                self.score    += self.speed * 0.05
                self.stars.update(self.speed)

                self.spawn_timer += 1
                if self.spawn_timer >= max(30, int(80 - self.speed * 4)):
                    self.spawn_obstacle(); self.spawn_timer = 0

                self.plat_timer += 1
                if self.plat_timer >= random.randint(90, 160):
                    self.spawn_platform(); self.plat_timer = 0

                self.coin_timer += 1
                if self.coin_timer >= random.randint(60, 120):
                    self.spawn_coin(); self.coin_timer = 0

                for obj in self.obstacles + self.platforms + self.coins:
                    obj.speed = self.speed
                    obj.update()

                self.obstacles = [o for o in self.obstacles if o.x + o.w > -10]
                self.platforms = [p for p in self.platforms if p.x + p.w > -10]
                self.coins     = [c for c in self.coins if c.x + c.r > -10 and not c.collected]

                self.player.update(self.platforms)
                pr = self.player.get_rect()

                if self.player.invincible == 0:
                    for obs in self.obstacles:
                        if pr.colliderect(obs.get_rect()):
                            self.lives -= 1
                            self.player.invincible = 90
                            self.add_particles(pr.centerx, pr.centery, RED, 20)
                            self.obstacles.remove(obs)
                            if self.lives <= 0:
                                self.high_score = max(self.high_score, self.score)
                                state = "over"
                            break

                for coin in self.coins:
                    if not coin.collected and pr.colliderect(coin.get_rect()):
                        coin.collected = True
                        self.score += 50
                        self.add_particles(coin.x, coin.y, YELLOW, 14)

                self.update_particles()
                self._draw_scene()
                pygame.display.flip()

            elif state == "over":
                self.update_particles()
                self._draw_scene()
                self.screen_game_over(screen)
                if PYEX_AVAILABLE:
                    pyex.draw(screen)
                pygame.display.flip()

if __name__ == "__main__":
    Game().run()