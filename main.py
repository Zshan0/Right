import pygame
from pygame.locals import *
import sys
import random
import time

pygame.init()
vec = pygame.math.Vector2  # 2 for two dimensional

HEIGHT = 900
WIDTH = 900
PLAYER_HORIZONTAL_VEL = 8
FRIC = -0.25
FPS = 60
GRAVITY = 0.5
VMAX = 4
JUMP_SPEED = 15
PLAYER_HEIGHT = 30
PLATFORM_HEIGHT = 10
JUMP_HEIGHT = JUMP_SPEED**2 / (2 * GRAVITY) - PLATFORM_HEIGHT

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
        self.vel = vec(0, 0)
        self.gravity = vec(0, GRAVITY)
        self.jumping = False
        self.score = 0
        self.flipped = False
        self.collided_platform = None
        self.pos = vec(WIDTH // 2, HEIGHT - 20)

    def move(self):
        # handle collisions
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if len(hits) != 0:
            if self.vel.y < 0:
                # going up, I can only collide from below
                for collided_platform in hits:
                    # set the player to top of the platform ig
                    self.pos.y = collided_platform.rect.bottom + PLAYER_HEIGHT + 1
                    self.vel.y = 0

            elif self.vel.y > 0:
                # going down, I can only collide from above
                for collided_platform in hits:
                    self.pos.y = collided_platform.rect.top + 1
                    self.vel.y = 0
                    self.jumping = False
                    self.collided_platform = collided_platform
            else:
                pass

        pressed_keys = pygame.key.get_pressed()

        self.vel = vec(0, self.vel.y)
        self.vel += self.gravity

        if pressed_keys[K_LEFT]:
            self.vel.x = -PLAYER_HORIZONTAL_VEL
        if pressed_keys[K_RIGHT]:
            self.vel.x = PLAYER_HORIZONTAL_VEL
        self.vel.x *= -1 if self.flipped else 1

        if pressed_keys[K_SPACE] and len(hits) > 0 and not self.jumping:
            # jumping
            self.jumping = True
            self.vel.y = -JUMP_SPEED
            self.collided_platform = None

        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    P1.cancel_jump()

        if self.flipped and self.vel.y < VMAX:
            self.vel.y = -VMAX

        if self.collided_platform:
            self.vel.x += self.collided_platform.vel.x

        self.pos += self.vel
        if self.pos.x > WIDTH:
            self.pos.x = 0
        if self.pos.x < 0:
            self.pos.x = WIDTH

    def cancel_jump(self):
        if self.jumping:
            if self.vel.y < -3:
                self.vel.y = -3

    def gonna_flip(self):
        self.surf.fill((255, 255, 255))

    def flip(self):
        self.flipped = not self.flipped
        if self.flipped:
            self.surf.fill((0, 255, 255))
        else:
            self.surf.fill((255, 255, 0))
        self.gravity = vec(0, GRAVITY * (-1 if self.flipped else 1))

    def update_rect(self):
        self.rect.midbottom = int(self.pos.x), int(self.pos.y)


class Platform(pygame.sprite.Sprite):
    def __init__(self, size=None, position=None, moving=True):
        super().__init__()
        if size is None:
            self.surf = pygame.Surface((random.randint(50, 100), PLATFORM_HEIGHT))
        else:
            self.surf = pygame.Surface(size)

        # color
        self.surf.fill((0, 255, 0))
        self.rect = self.surf.get_rect()
        if position is None:
            self.pos = vec(
                (random.randint(0, WIDTH - 10), random.randint(0, HEIGHT - 30))
            )
        else:
            self.pos = vec(position)
        if moving:
            self.vel = vec(random.choice([1, -1]) * 2, 0)
        else:
            self.vel = vec(0, 0)
        self.moving = moving
        self.point = True

    def move(self):
        self.pos += self.vel
        half_width = self.rect.width / 2
        if self.vel.x > 0 and self.pos.x + half_width > WIDTH:
            self.pos.x = -half_width
        if self.vel.x < 0 and self.pos.x - half_width < 0:
            self.pos.x = WIDTH + half_width
        self.rect.center = int(self.pos.x), int(self.pos.y)


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


P1 = Player()
all_sprites = pygame.sprite.Group()
platforms = pygame.sprite.Group()
top_platforms = []

# GAME STATES
INVERSE = False
flipIn = 300


def flip_state():
    global INVERSE
    P1.flip()
    INVERSE = not INVERSE


def add_platforms():
    """
    Uses top_platforms to decide next layer.
    """
    global top_platforms
    prev_height = top_platforms[0].pos.y

    # No more gen above
    if prev_height < -50:
        return

    new_height = prev_height - random.randint(PLAYER_HEIGHT + 10, int(JUMP_HEIGHT) - 10)

    size = (200, PLATFORM_HEIGHT)
    position = (random.randint(0, WIDTH - 10), new_height)

    pl = Platform(size=size, position=position, moving=True)

    platforms.add(pl)
    all_sprites.add(pl)

    top_platforms = [pl]


def init_platform():
    PT1 = Platform(
        size=(WIDTH - 10, PLATFORM_HEIGHT),
        position=(WIDTH // 2, HEIGHT - 10),
        moving=False,
    )
    platforms.add(PT1)
    all_sprites.add(PT1)
    top_platforms.append(PT1)

    add_platforms()


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
    P1.pos.y += abs(P1.vel.y)
    for plat in platforms:
        plat.pos.y += abs(P1.vel.y)
        if plat.pos.y >= HEIGHT:
            plat.kill()


def main():
    global flipIn
    all_sprites.add(P1)
    init_platform()

    while True:
        flipIn -= 1

        if flipIn == 60:
            P1.gonna_flip()

        if flipIn == 0:
            # flip_state()
            flipIn = 400 + random.randint(-60, 60)

        keyboard_events()
        [entity.move() for entity in all_sprites]

        if P1.rect.top > HEIGHT:
            end_game()

        if P1.rect.top <= HEIGHT / 3:
            shift_level_up()
        add_platforms()

        P1.update_rect()

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
