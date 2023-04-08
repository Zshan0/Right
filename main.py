import pygame
from pygame.locals import *
import sys
import random
import time
import logging

pygame.init()
vec = pygame.math.Vector2  # 2 for two dimensional

HEIGHT = 900
WIDTH = 900
PLAYER_HORIZONTAL_VEL = 8
PLAYER_TERMINAL_VEL = 10
FPS = 60
GRAVITY = 0.5
VMAX = 4
JUMP_SPEED = 12
PLAYER_HEIGHT = 30
PLAYER_WIDTH = 30
PLATFORM_HEIGHT = 13
PLATFORM_VEL = 2
MAX_PLATFORM_WIDTH = 100
MIN_CAMERA_SPEED = 0.3
MAX_CAMERA_SPEED = 5
PLAYER_STARTED = False
JUMP_HEIGHT = JUMP_SPEED**2 / (2 * GRAVITY) - PLATFORM_HEIGHT

FramePerSec = pygame.time.Clock()

displaysurface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Right?")


def min_sep_vec(rec1, rec2):
    # Left object is rec1
    if rec1.left > rec2.left:
        rec1, rec2 = rec2, rec1

    x2, x3, x4 = rec1.right, rec2.left, rec2.right

    if x3 <= x2 <= x4:
        x_gap = x2 - x3
    else:
        x_gap = x4 - x3

    if rec1.top > rec2.top:
        rec1, rec2 = rec2, rec1

    y2, y3, y4 = rec1.bottom, rec2.top, rec2.bottom

    if y3 <= y2 <= y4:
        y_gap = y2 - y3
    else:
        y_gap = y4 - y3

    return [x_gap, y_gap]


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        # self.image = pygame.image.load("character.png")
        self.surf = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.surf.fill((255, 255, 0))
        self.rect = self.surf.get_rect()
        self.vel = vec(0, 0)
        self.jumping = False
        self.score = 0
        self.collided_platform = None
        self.pos = vec(WIDTH // 2, HEIGHT - 30)
        self.update_rect()

    def collision(self):
        hits = pygame.sprite.spritecollide(self, platforms, False)

        if len(hits) == 0:
            return
        # TODO move platforms also
        collided_platform = hits[0]

        msv = min_sep_vec(self.rect, collided_platform.rect)

        # normalize the overlap in both directions
        msv[0] /= min(PLAYER_WIDTH, collided_platform.rect.width)
        msv[1] /= min(PLAYER_HEIGHT, collided_platform.rect.height)

        if collided_platform != self.collided_platform:
          logging.debug(msv)
          logging.debug(f"\nvel:{self.vel.x}\npos:{self.pos.x}\n")

        # x < y
        clip = msv[0] < msv[1]
        if clip:
            # logging.debug("clip!")
            if self.pos.x < collided_platform.rect.center[0]:
                self.pos.x = collided_platform.rect.left - PLAYER_WIDTH / 2
            else:
                self.pos.x = collided_platform.rect.right + PLAYER_WIDTH / 2

            # if players and platform move in opposite directions then shift the player by the platforms velocity
            if self.vel.x * collided_platform.vel.x < 0:
                self.pos.x += collided_platform.vel.x
            # logging.debug(f"changed pos:{self.pos.x}\n")

        if self.vel.y < 0:
            # going up
            # if collided_platform != self.collided_platform:
            #   logging.debug("UP")

            #
            if (
                not clip
                and msv[0]
                > PLAYER_HORIZONTAL_VEL
                / min(PLAYER_WIDTH, collided_platform.rect.width)
                and self.pos.y - PLAYER_HEIGHT > collided_platform.rect.top
                and self.pos.y > collided_platform.rect.bottom
            ):
                # print("Jerking to botom of the platform")
                self.vel.y = GRAVITY
                self.pos.y = collided_platform.rect.bottom + PLAYER_HEIGHT
        else:
            # going down
            # if collided_platform != self.collided_platform:
            #   logging.debug("DOWN")

            if clip or self.pos.y> collided_platform.rect.bottom:
                # print("Clipped or too low")
                return

            # if collided_platform != self.collided_platform:
            #     logging.debug("Sending to top of the platform")

            self.pos.y = collided_platform.rect.top + 1
            self.vel.y = 0
            self.jumping = False
            self.collided_platform = collided_platform

    def move(self):
        global PLAYER_STARTED
        if not PLAYER_STARTED and self.pos.y < HEIGHT * 0.5:
            PLAYER_STARTED = True

        self.vel = vec(0, self.vel.y)
        self.vel.y += GRAVITY

        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_LEFT]:
            self.vel.x = -PLAYER_HORIZONTAL_VEL
        if pressed_keys[K_RIGHT]:
            self.vel.x = PLAYER_HORIZONTAL_VEL
        self.vel.x *= -1 if INVERSE else 1

        hits = pygame.sprite.spritecollide(self, platforms, False)
        if pressed_keys[K_SPACE] and len(hits) > 0 and not self.jumping:
            # jumping
            self.jumping = True
            self.vel.y = -JUMP_SPEED
            self.collided_platform = None

        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    P1.cancel_jump()

        if self.collided_platform:
            self.vel.x += self.collided_platform.vel.x

        self.vel.y = min(self.vel.y, PLAYER_TERMINAL_VEL)
        self.pos += self.vel

        if self.pos.x > WIDTH:
            self.pos.x = WIDTH
        if self.pos.x < 0:
            self.pos.x = 0

        self.update_rect()

    def cancel_jump(self):
        if self.jumping:
            if self.vel.y < -10:
                self.vel.y = -10

    def gonna_flip(self):
        self.surf.fill((255, 255, 255))

    def flip(self):
        if not INVERSE:
            self.surf.fill((0, 255, 255))
        else:
            self.surf.fill((255, 255, 0))

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
            self.vel = vec(random.choice([1, -1]) * PLATFORM_VEL, 0)
        else:
            self.vel = vec(0, 0)
        self.moving = moving
        self.point = True

    def move(self):
        self.pos += self.vel
        half_width = self.rect.width / 2
        # Platform bounce back
        if self.vel.x > 0 and self.pos.x + half_width > WIDTH:
            self.vel.x = -1 * self.vel.x
        if self.vel.x < 0 and self.pos.x - half_width < 0:
            self.vel.x = -1 * self.vel.x
        self.rect.midbottom = int(self.pos.x), int(self.pos.y)


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
flipIn = 100
flipDec = 0.2


def flip_state():
    global INVERSE
    P1.flip()
    INVERSE = not INVERSE


def add_platforms():
    """
    Uses top_platforms to decide next layer.
    Platform height should be above the previous top platform's height
    Platform width should be uniformly distributed on the length not occupied by the previous top
    platforms and the current top platforms
    """
    count = 2

    global top_platforms
    prev_height = top_platforms[0].pos.y

    # No more gen above
    if prev_height < -50:
        return

    new_height = prev_height - random.randint(PLAYER_HEIGHT + 10, int(JUMP_HEIGHT) - 10)
    new_plats = []

    positions_to_avoid = [
        (top_platform.pos.x, top_platform.rect.right - top_platform.rect.left)
        for top_platform in top_platforms
    ]
    # print(positions_to_avoid)

    for _ in range(count):
        size = (MAX_PLATFORM_WIDTH, PLATFORM_HEIGHT)
        x_pos = positions_to_avoid[0][0]

        def if_x_pos_within_positions_to_avoid(pos):
            for position_to_avoid, width in positions_to_avoid:
                if pos >= position_to_avoid and pos <= position_to_avoid + width:
                    return True
            return False

        while if_x_pos_within_positions_to_avoid(x_pos):
            x_pos = random.randint(0, WIDTH - 10)

        position = (random.randint(0, WIDTH - 10), new_height)
        pl = Platform(size=size, position=position, moving=False)

        positions_to_avoid.append((position[0], pl.rect.right - pl.rect.left))
        platforms.add(pl)
        all_sprites.add(pl)
        new_plats.append(pl)

    top_platforms = new_plats


def init():
    global INVERSE, all_sprites, platforms, top_platforms, P1, PLAYER_STARTED, flipIn
    # reset the game state
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    top_platforms = []
    INVERSE = False
    PLAYER_STARTED = False
    flipIn = 100

    P1 = Player()
    all_sprites.add(P1)
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

            if pressed_keys[K_r]:
                return -1

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                P1.cancel_jump()


def end_game():
    for entity in all_sprites:
        entity.kill()
        # time.sleep(1)
        # displaysurface.fill((255, 0, 0))
        # pygame.display.update()
        # time.sleep(1)
        # pygame.quit()
        # sys.exit()


def shift_level_up(v):
    """
    Takes input the camera speed and moves the camera by that amount in each frame
    """
    P1.pos.y += v
    for plat in platforms:
        plat.pos.y += v
        if plat.pos.y >= HEIGHT:
            plat.kill()


BG1 = (20, 40, 60)
BG2 = (60, 40, 20)


def bg_color():
    global flipIn
    if INVERSE:
        flip = 100 - flipIn
    else:
        flip = flipIn
    return tuple(
        map(lambda x: int(x[0] * flip / 100 + x[1] * (1 - flip / 100)), zip(BG1, BG2))
    )


def game_loop():
    global flipIn, flipDec
    while True:
        flipIn -= flipDec

        if flipIn <= 0:
            # flip_state()
            flipIn = 100
            flipDec = random.randint(2, 3) / 10

        if keyboard_events() == -1:
            return

        # first move and update player
        P1.move()
        [entity.move() for entity in platforms]
        P1.collision()

        if P1.rect.top > HEIGHT:
            end_game()
            return

        if PLAYER_STARTED:
            camera_speed = MIN_CAMERA_SPEED + (MAX_CAMERA_SPEED - MIN_CAMERA_SPEED) * (
                HEIGHT - P1.rect.bottom
            ) / (HEIGHT)
            shift_level_up(camera_speed)

        add_platforms()

        P1.update_rect()

        displaysurface.fill(bg_color())

        f = pygame.font.SysFont("Verdana", 20)
        g = f.render(str(P1.rect.bottom), True, (123, 255, 0))
        displaysurface.blit(g, (WIDTH / 2, 10))

        for entity in all_sprites:
            displaysurface.blit(entity.surf, entity.rect)

        pygame.display.update()
        FramePerSec.tick(FPS)


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    while True:
        init()
        game_loop()


if __name__ == "__main__":
    main()
