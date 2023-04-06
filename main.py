import pygame
from pygame.locals import *
import sys
import random
import time

pygame.init()
vec = pygame.math.Vector2  # 2 for two dimensional

HEIGHT = 900
WIDTH = 900
PLAYER_HORIZONTAL_VEL = 2
FRIC = -0.25
FPS = 60
GRAVITY = 0.5
VMAX = 4

FramePerSec = pygame.time.Clock()

displaysurface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Right?")


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # self.image = pygame.image.load("character.png")
        self.surf = pygame.Surface((30, 30))
        self.surf.fill((255, 255, 0))
        self.rect = self.surf.get_rect()
        self.rect.center = (WIDTH / 2, HEIGHT / 2)

        self.vel = vec(0, 0)
        self.acc = vec(0, GRAVITY)
        self.jumping = False
        self.score = 0
        self.flipped = False
        self.collided_platform = None

    def move(self):
        # handle collisions
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if len(hits) != 0:
            if self.vel.y < 0:
                # going up, I can only collide from below
                for collided_platform in hits:
                    self.rect.top = collided_platform.rect.bottom + 1
                    self.vel.y = 0

            elif self.vel.y > 0:
                # going down, I can only collide from above
                for collided_platform in hits:
                    self.rect.bottom = collided_platform.rect.top + 1
                    self.vel.y = 0
                    self.jumping = False
                    self.collided_platform = collided_platform
            else:
                pass

        
        pressed_keys = pygame.key.get_pressed()

        if pressed_keys[K_LEFT]:
            self.acc.x = -PLAYER_HORIZONTAL_VEL * (-1 if self.flipped else 1)
        if pressed_keys[K_RIGHT]:
            self.acc.x = PLAYER_HORIZONTAL_VEL
        self.acc.x *= (-1 if self.flipped else 1)
        
        if pressed_keys[K_SPACE] and len(hits) > 0 and not self.jumping:
            # jumping
            self.jumping = True
            self.vel.y = -15
            self.collided_platform = None

        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    P1.cancel_jump()

        # print(self.acc)
        self.vel.x = 0
        self.vel += self.acc

        if self.flipped and self.vel.y < VMAX:
            self.vel.y = -VMAX

        if self.collided_platform:
            self.vel.x += self.collided_platform.vel.x

        pos = self.rect.midbottom
        
        print(pos, self.vel)
        pos += self.vel
        print(pos)
        if pos.x > WIDTH:
            pos.x = 0
        if pos.x < 0:
            pos.x = WIDTH

        self.rect.midbottom = pos

    def cancel_jump(self):
        if self.jumping:
            if self.vel.y < -3:
                self.vel.y = -3

    def gonnaFlip(self):
        self.surf.fill((255, 255, 255))

    def flip(self):
        self.flipped = not self.flipped
        if self.flipped:
            self.surf.fill((0, 255, 255))
        else:
            self.surf.fill((255, 255, 0))
        self.acc = vec(0, GRAVITY * (-1 if self.flipped else 1))


class platform(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.surf = pygame.Surface((random.randint(50, 100), 12))
        self.surf.fill((0, 255, 0))
        self.rect = self.surf.get_rect(
            center=(random.randint(0, WIDTH - 10), random.randint(0, HEIGHT - 30))
        )
        self.vel = vec(random.randint(-1, 1), 0)

        self.point = True
        self.moving = True

    def move(self):
        if self.moving == True:
            self.rect.move_ip(self.vel)
            if self.vel.x > 0 and self.rect.left > WIDTH:
                self.rect.right = 0
            if self.vel.x < 0 and self.rect.right < 0:
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
PT1.point = False
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
    P1.rect.bottom += abs(P1.vel.y)
    for plat in platforms:
        plat.rect.y += abs(P1.vel.y)
        if plat.rect.top >= HEIGHT:
            plat.kill()


def main():
    global flipIn
    init_platform(20)

    while True:
        flipIn -= 1

        if flipIn == 60:
            P1.gonnaFlip()

        if flipIn == 0:
            flip_state()
            flipIn = 400 + random.randint(-60, 60)

        keyboard_events()
        [entity.move() for entity in all_sprites]

        if P1.rect.top > HEIGHT:
            end_game()

        if P1.rect.top <= HEIGHT / 3:
            shift_level_up()

        plat_gen()
        displaysurface.fill((0, 0, 0))
        f = pygame.font.SysFont("Verdana", 20)
        g = f.render(str(P1.rect.bottom), True, (123, 255, 0))
        displaysurface.blit(g, (WIDTH / 2, 10))

        for entity in all_sprites:
            displaysurface.blit(entity.surf, entity.rect)

        pygame.display.update()
        FramePerSec.tick(FPS)


if __name__ == "__main__":
    main()