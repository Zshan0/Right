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
PLATFORM_HEIGHT = 15
PLATFORM_VEL = 2
MAX_PLATFORM_WIDTH = 100
MIN_CAMERA_SPEED = 0.3
MAX_CAMERA_SPEED = 5
PLAYER_STARTED = False
PHASE_MAX_LAYERS = 10
MOVE_BY = 3
phase_layers = PHASE_MAX_LAYERS + 1
JUMP_HEIGHT = JUMP_SPEED**2 / (2 * GRAVITY) - PLATFORM_HEIGHT
PLATFORM_HEALTH = 50
DAMAGE_THRESHOLD = PLATFORM_HEALTH / 2
DIFFICULTY = 0
H_INVERSE = False
V_INVERSE = False
PT1 = None
LIVES = 5
hInvert = 100
hInvertDec = 0.2
vInvert = 100
vInvertDec = 0.2

COLOR_NORMAL = (255, 255, 0)
COLOR_FLIP = (0, 255, 255)
WHITE = (255, 255, 255)
COLOR_NEW = (255, 0, 0)
FramePerSec = pygame.time.Clock()

displaysurface = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.SCALED, vsync=1)
pygame.display.set_caption("Right?")


def left(s):
    return s.pos.x - s.width / 2


def right(s):
    return s.pos.x + s.width / 2


def top(s):
    return s.pos.y - s.height


def bottom(s):
    return s.pos.y


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
        self.surf.fill(COLOR_NORMAL)
        self.rect = self.surf.get_rect()
        self.vel = vec(0, 0)
        self.jumping = False
        self.score = 0
        self.collided_platform = None
        self.pos = vec(WIDTH // 2, HEIGHT - 30)
        self.update_rect()
        self.flash = True

    def collision(self):
        P1.collided_platform = None
        hits = pygame.sprite.spritecollide(self, platforms, False)

        if len(hits) == 0:
            return
        # TODO move platforms also
        collided_platform = hits[0]

        msv = min_sep_vec(self.rect, collided_platform.rect)

        # normalize the overlap in both directions
        msv[0] /= min(PLAYER_WIDTH, collided_platform.rect.width)
        msv[1] /= min(PLAYER_HEIGHT, collided_platform.rect.height)

        # if collided_platform != self.collided_platform:
        #   logging.debug(msv)
        #   logging.debug(f"\nvel:{self.vel.x}\npos:{self.pos.x}\n")

        # x < y
        clip = msv[0] < msv[1]
        if clip:
            # logging.debug("clip!")
            if self.pos.x < collided_platform.pos.x:
                self.pos.x = left(collided_platform) - PLAYER_WIDTH / 2
            else:
                self.pos.x = right(collided_platform) + PLAYER_WIDTH / 2

            # if players and platform move in opposite directions then shift the player by the platforms velocity
            if self.vel.x * collided_platform.vel.x < 0:
                self.pos.x += collided_platform.vel.x
            # logging.debug(f"changed pos:{self.pos.x}\n")

        if self.vel.y < 0:
            # going up
            if (
                not clip
                and msv[0]
                > PLAYER_HORIZONTAL_VEL / min(PLAYER_WIDTH, collided_platform.width)
                and self.pos.y - PLAYER_HEIGHT > top(collided_platform)
                and self.pos.y > bottom(collided_platform)
            ):
                self.vel.y = GRAVITY
                self.pos.y = bottom(collided_platform) + PLAYER_HEIGHT
        else:
            # going down
            if clip or self.pos.y > bottom(collided_platform):
                # print("Clipped or too low")
                return

            self.pos.y = top(collided_platform) + 1
            self.vel.y = 0
            self.jumping = False
            self.collided_platform = collided_platform

            # decrease the health of the platform every time it is in contact
            collided_platform.health -= 0

            if collided_platform.health <= 0:
                collided_platform.kill()
            if (
                not collided_platform.half_broken
                and collided_platform.health <= DAMAGE_THRESHOLD
            ):
                collided_platform.change_color()

            

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
        self.vel.x *= -1 if H_INVERSE else 1

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
        if not self.flash:
            self.surf.fill((255, 255, 255))
        else:
            if H_INVERSE:
                self.surf.fill(COLOR_FLIP)
            else:
                self.surf.fill(COLOR_NORMAL)
        self.flash = not self.flash

    def flip(self):
        if not H_INVERSE:
            self.surf.fill(COLOR_FLIP)
        else:
            self.surf.fill(COLOR_NORMAL)

    def update_rect(self):
        self.rect.midbottom = int(self.pos.x), int(self.pos.y)


class Platform(pygame.sprite.Sprite):
    def __init__(self, size=None, position=None, moving=True):
        super().__init__()
        if size is None:
            self.surf = pygame.Surface((MAX_PLATFORM_WIDTH, PLATFORM_HEIGHT))
        else:
            self.surf = pygame.Surface(size)

        self.height = self.surf.get_height()
        self.width = self.surf.get_width()
        self.health = PLATFORM_HEALTH
        self.half_broken = False

        # color
        self.surf.fill((0, 255, 0))
        self.rect = self.surf.get_rect()
        self.width = self.surf.get_width()
        self.height = self.surf.get_height()
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

    def change_color(self):
        self.surf.fill((255, 0, 0))
        self.half_broken = True

    def move(self):
        self.pos += self.vel
        half_width = self.width / 2
        # Platform bounce back
        if self.vel.x > 0 and self.pos.x + half_width > WIDTH:
            self.vel.x = -1 * self.vel.x
        if self.vel.x < 0 and self.pos.x - half_width < 0:
            self.vel.x = -1 * self.vel.x
        self.update_rect()

    def update_rect(self):
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


def flip_state():
    global H_INVERSE
    P1.flip()
    H_INVERSE = not H_INVERSE


def gonna_flip():
    P1.gonna_flip()


def add_stack(staggered=False):
    global top_platforms
    center = (random.random() * 0.33 + 0.33) * WIDTH
    prev_plat = top_platforms[-1]

    offsets = [0, 1, -1]
    for idx in range(PHASE_MAX_LAYERS):
        for offset in offsets:
            new_height = prev_plat.pos.y - JUMP_HEIGHT * min(0.9 + DIFFICULTY / 10, 1)
            if staggered and idx % 2 == 0:
                stagger = MAX_PLATFORM_WIDTH * 0.75 * 0.5
            else:
                stagger = 0

            position = (
                center + offset * (MAX_PLATFORM_WIDTH * 2 * 0.75) + stagger,
                new_height,
            )
            pl = Platform(
                size=(MAX_PLATFORM_WIDTH * 0.75, PLATFORM_HEIGHT),
                position=position,
                moving=False,
            )
            platforms.add(pl)
            all_sprites.add(pl)
        prev_plat = pl

    top_platforms = [pl]

    return PHASE_MAX_LAYERS * len(offsets)


def add_random_platform():
    global top_platforms
    new_layer = False
    if len(top_platforms) >= 2 or random.random() < 0.5:
        new_layer = True
        prev_platform = random.choice(top_platforms)
        prev_height = prev_platform.pos.y
        new_height = prev_height - JUMP_HEIGHT * min(1, 0.75 + DIFFICULTY / 10)
        min_horizontal_dist = MAX_PLATFORM_WIDTH * 0.5 * min(1, 0.9 + DIFFICULTY / 10)
        max_horizontal_dist = JUMP_HEIGHT * 1.75 * PLAYER_HORIZONTAL_VEL / JUMP_SPEED
    else:
        new_layer = False
        prev_platform = top_platforms[0]
        prev_height = prev_platform.pos.y
        new_height = prev_height
        min_horizontal_dist = MAX_PLATFORM_WIDTH * 1.5 + MAX_PLATFORM_WIDTH / 2
        max_horizontal_dist = JUMP_HEIGHT * 4 * PLAYER_HORIZONTAL_VEL / JUMP_SPEED

    # make new platform on left
    r_start_left = max(0, prev_platform.pos.x - max_horizontal_dist)
    r_end_left = max(0, prev_platform.pos.x - min_horizontal_dist)
    left_range = r_end_left - r_start_left
    # make new platform on right
    r_start_right = min(WIDTH, prev_platform.pos.x + min_horizontal_dist)
    r_end_right = min(WIDTH, prev_platform.pos.x + max_horizontal_dist)
    right_range = r_end_right - r_start_right

    total = left_range + right_range

    if random.random() < left_range / total:
        r_end = r_end_left
        r_start = r_start_left
    else:
        r_end = r_end_right
        r_start = r_start_right

    pos_x = (r_end - r_start) * random.random() + r_start
    position = (pos_x, new_height)
    size = (MAX_PLATFORM_WIDTH, PLATFORM_HEIGHT)

    pl = Platform(size=size, position=position, moving=False)
    platforms.add(pl)
    all_sprites.add(pl)

    if new_layer:
        top_platforms = [pl]
    else:
        top_platforms.append(pl)

    if new_layer:
        return 1

    return 0


def add_staircase():
    # logging.debug("Adding a new staircase")
    global top_platforms, platforms, all_sprites
    # start from a random platform
    prev_platform = random.choice(top_platforms)
    # direction is based off of the previous platfrom center

    if prev_platform.pos.x < WIDTH / 2:
        dir = -1  # left
    else:
        dir = 1  # right

    pt_count = PHASE_MAX_LAYERS
    for _ in range(pt_count):
        prev_height = prev_platform.pos.y
        new_height = prev_height - JUMP_HEIGHT * 0.5
        x_center = prev_platform.pos.x + dir * MAX_PLATFORM_WIDTH * min(
            3, DIFFICULTY * 0.5
        )
        if (
            x_center + MAX_PLATFORM_WIDTH / 2 + 5 > WIDTH
            or x_center - MAX_PLATFORM_WIDTH / 2 - 5 < 0
        ):
            dir *= -1
            x_center = prev_platform.pos.x + dir * MAX_PLATFORM_WIDTH / 1.2

        position = x_center, new_height
        pl = Platform(
            size=(MAX_PLATFORM_WIDTH, PLATFORM_HEIGHT), position=position, moving=False
        )
        # logging.debug("Adding a staircase platform")
        platforms.add(pl)
        all_sprites.add(pl)
        prev_platform = pl

    top_platforms = [pl]

    return pt_count


current_phase = 0


def add_platforms():
    global top_platforms, phase_layers, current_phase, DIFFICULTY
    prev_platform = top_platforms[-1]
    prev_height = prev_platform.pos.y
    if prev_height < -50:
        return

    if phase_layers >= PHASE_MAX_LAYERS:
        prev_phase = current_phase
        while prev_phase == current_phase:
            current_phase = random.randint(0, 3)
        phase_layers = 0
        DIFFICULTY += 1

    if current_phase == 0:
        phase_layers += add_staircase()
    elif current_phase == 1:
        phase_layers += add_random_platform()
    elif current_phase == 2:
        phase_layers += add_stack()
    elif current_phase == 3:
        phase_layers += add_stack(staggered=True)


def init():
    global H_INVERSE, all_sprites, platforms, top_platforms, P1, PLAYER_STARTED, hInvert, DIFFICULTY, V_INVERSE, PT1, LIVES
    # reset the game state
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    top_platforms = []
    H_INVERSE = False
    V_INVERSE = False
    PLAYER_STARTED = False
    DIFFICULTY = 0
    hInvert = 100
    LIVES = 5

    P1 = Player()
    all_sprites.add(P1)
    PT1 = Platform(
        size=(WIDTH * 1.5, PLATFORM_HEIGHT),
        position=(WIDTH // 2, HEIGHT - 10),
        moving=False,
    )
    PT1.health = 100 * PLATFORM_HEALTH
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


falling = False
def camera():
    global falling, LIVES
    v = 2

    if P1.pos.y > 0.96 * HEIGHT and P1.collided_platform == None and P1.vel.y >= 0 and not falling:
        falling = True
        LIVES -= 1
        if LIVES == 0:
            return -1

    if falling and P1.collided_platform is not None:
        falling = False
  

    if falling:
        v = -(PLAYER_TERMINAL_VEL + 2)
        
    if falling and P1.pos.y < HEIGHT * 0.35:
        v = -PLAYER_TERMINAL_VEL

    if P1.collided_platform == PT1:
      v = 0          

    P1.pos.y += v
    for plat in platforms:
        plat.pos.y += v
        # if plat.pos.y >= HEIGHT:
        #     plat.kill()


BG1 = (128, 128, 255)
BG2 = (255, 128, 128)


def bg_color():
    global vInvert
    if V_INVERSE:
        flip = 100 - vInvert
    else:
        flip = vInvert
    return tuple(
        map(lambda x: int(x[0] * flip / 100 + x[1] * (1 - flip / 100)), zip(BG1, BG2))
    )


def game_loop():
    global hInvert, hInvertDec, vInvert, vInvertDec, V_INVERSE
    while True:
        # handle keyboard input
        if keyboard_events() == -1:
            return
        
        if camera() == -1:
            return
        # move entities and check for collision
        P1.move()
        [entity.move() for entity in platforms]
        P1.collision()

        if P1.pos.y > HEIGHT:
            end_game()
            return



        add_platforms()

        P1.update_rect()


        # handle the inversion counters
        hInvert -= hInvertDec
        vInvert -= vInvertDec

        if hInvert <= 0:
            flip_state()
            hInvert = 100
            hInvertDec = random.randint(20, 30) / 100

        if vInvert <= 0:
            V_INVERSE = not V_INVERSE
            vInvert = 100
            vInvertDec = random.randint(5, 10) / 100

        if hInvert <= 20:
            floor_val = hInvert // 5
            if floor_val % 2 == 0:
                P1.surf.fill(WHITE)
            else:
                if H_INVERSE:
                    P1.surf.fill(COLOR_FLIP)
                else:
                    P1.surf.fill(COLOR_NORMAL)

        if V_INVERSE:
            displaysurface.fill(BG1)
        else:
            displaysurface.fill(BG2)

        if vInvert <= 20:
            floor_val = vInvert // 5
            if floor_val % 2 == 0:
                displaysurface.fill((230, 230, 230))


        f = pygame.font.SysFont("Verdana", 20)
        g = f.render(str(LIVES), True, (123, 255, 0))
        displaysurface.blit(g, (WIDTH / 2, 10))
        for entity in all_sprites:
            displaysurface.blit(entity.surf, entity.rect)

        if V_INVERSE:
          displaysurface.blit(pygame.transform.rotate(displaysurface, 180), (0, 0))

        pygame.display.update()
        FramePerSec.tick(FPS)


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    while True:
        init()
        game_loop()


if __name__ == "__main__":
    main()
