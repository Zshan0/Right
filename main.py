import pygame
from pygame.locals import *
import sys
import random
import time

pygame.init()
vec = pygame.math.Vector2  # 2 for two dimensional

HEIGHT = 1000
WIDTH = 1000
ACC = 0.5
FRIC = -0.25
FPS = 60

FramePerSec = pygame.time.Clock()

displaysurface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # self.image = pygame.image.load("character.png")
        self.surf = pygame.Surface((30, 30))
        self.surf.fill((255, 255, 0))
        self.rect = self.surf.get_rect()

        self.pos = vec((10, 360))
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.jumping = False
        self.score = 0
        self.flipped = False

    def move(self):
        self.acc = vec(0, 0.5)

        pressed_keys = pygame.key.get_pressed()

        if pressed_keys[K_LEFT]:
            self.acc.x = -ACC * (-1 if self.flipped else 1)
        if pressed_keys[K_RIGHT]:
            self.acc.x = ACC * (-1 if self.flipped else 1)

        self.acc.x += self.vel.x * FRIC
        self.vel += self.acc
        self.pos += self.vel + 0.5 * self.acc

        if self.pos.x > WIDTH:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = WIDTH

        self.rect.midbottom = self.pos

    def jump(self):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if hits and not self.jumping:
            self.jumping = True
            self.vel.y = -15

    def cancel_jump(self):
        if self.jumping:
            if self.vel.y < -3:
                self.vel.y = -3

    def update(self):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if self.vel.y > 0:
            if hits:
                if self.pos.y < hits[0].rect.bottom:
                    if hits[0].point == True:
                        hits[0].point = False
                        self.score += 1
                    self.pos.y = hits[0].rect.top + 1
                    self.vel.y = 0
                    self.jumping = False

    def gonnaFlip(self):
        print("Flipping in 3")
        self.surf.fill((255, 255, 255))

    def flip(self):
        self.flipped = not self.flipped
        if self.flipped:
            self.surf.fill((0, 255, 255))
        else:
            self.surf.fill((255, 255, 0))


class platform(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surf = pygame.Surface((random.randint(50, 100), 12))
        self.surf.fill((0, 255, 0))
        self.rect = self.surf.get_rect(
            center=(random.randint(0, WIDTH - 10), random.randint(0, HEIGHT - 30))
        )
        self.speed = random.randint(-1, 1)

        self.point = True
        self.moving = True

    def move(self):
        if self.moving == True:
            self.rect.move_ip(self.speed, 0)
            if self.speed > 0 and self.rect.left > WIDTH:
                self.rect.right = 0
            if self.speed < 0 and self.rect.right < 0:
                self.rect.left = WIDTH


def check(platform, groupies):
    if pygame.sprite.spritecollideany(platform, groupies):
        return True
    else:
        for entity in groupies:
            if entity == platform:
                continue
            if (abs(platform.rect.top - entity.rect.bottom) < 40) and (
                abs(platform.rect.bottom - entity.rect.top) < 40
            ):
                return True
        C = False


def plat_gen():
    while len(platforms) < 6:
        width = random.randrange(50, 100)
        p = platform()
        C = True

        while C:
            p = platform()
            p.rect.center = (
                random.randrange(0, WIDTH - width),
                random.randrange(-50, 0),
            )
            C = check(p, platforms)
        platforms.add(p)
        all_sprites.add(p)


PT1 = platform()
P1 = Player()

PT1.surf = pygame.Surface((WIDTH, 20))
PT1.surf.fill((255, 0, 0))
PT1.rect = PT1.surf.get_rect(center=(WIDTH / 2, HEIGHT - 10))

all_sprites = pygame.sprite.Group()
all_sprites.add(PT1)
all_sprites.add(P1)

platforms = pygame.sprite.Group()
platforms.add(PT1)

PT1.moving = False
PT1.point = False  ##
flipIn = 300

# GAME STATES
INVERSE = False


def flip_state():
    global INVERSE
    P1.flip()
    INVERSE = not INVERSE


def init_platform(count):
    for _ in range(count):
        pl = platform()
        while check(pl, platforms):
            pl = platform()

        platforms.add(pl)
        all_sprites.add(pl)


def keyboard_events():
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                P1.jump()

            pressed_keys = pygame.key.get_pressed()
            if pressed_keys[K_x]:
                pygame.quit()
                sys.exit()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                P1.cancel_jump()


def end_game():
    for entity in all_sprites:
        entity.kill()
        time.sleep(1)
        displaysurface.fill((255, 0, 0))
        pygame.display.update()
        time.sleep(1)
        pygame.quit()
        sys.exit()


def shift_level_up():
    P1.pos.y += abs(P1.vel.y)
    for plat in platforms:
        plat.rect.y += abs(P1.vel.y)
        if plat.rect.top >= HEIGHT:
            plat.kill()


def main():
    global flipIn
    init_platform(random.randint(4, 5))

    while True:
        flipIn -= 1

        if flipIn == 60:
            P1.gonnaFlip()

        if flipIn == 0:
            flip_state()

        P1.update()
        keyboard_events()

        if P1.rect.top > HEIGHT:
            # player dies.
            end_game()

        if P1.rect.top <= HEIGHT / 3:
            shift_level_up()

        plat_gen()
        displaysurface.fill((0, 0, 0))
        f = pygame.font.SysFont("Verdana", 20)
        g = f.render(str(P1.score), True, (123, 255, 0))
        displaysurface.blit(g, (WIDTH / 2, 10))

        for entity in all_sprites:
            displaysurface.blit(entity.surf, entity.rect)
            entity.move()

        pygame.display.update()
        FramePerSec.tick(FPS)


if __name__ == "__main__":
    main()
