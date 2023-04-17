import pygame
from pygame.locals import *
import sys
import random
import logging
from sprite_sheet import SpriteSheet
vec = pygame.math.Vector2

# constants!
HEIGHT = 900
WIDTH = 900
PLAYER_HORIZONTAL_VEL = 8
PLAYER_TERMINAL_VEL = 10
FPS = 60
GRAVITY = 0.5
VMAX = 4
JUMP_SPEED = 12
PLAYER_HEIGHT = 40
PLAYER_WIDTH = 40
PLATFORM_HEIGHT = 15
PLATFORM_VEL = 2
MAX_PLATFORM_WIDTH = 100
MIN_CAMERA_SPEED = 0.3
MAX_CAMERA_SPEED = 5
PHASE_MAX_LAYERS = 10
MOVE_BY = 3
JUMP_HEIGHT = JUMP_SPEED**2 / (2 * GRAVITY) - PLATFORM_HEIGHT
PLATFORM_HEALTH = 50
DAMAGE_THRESHOLD = PLATFORM_HEALTH / 2
BG1 = (128, 128, 255)
BG2 = (255, 128, 128)
COLOR_NORMAL = (255, 255, 0)
COLOR_FLIP = (0, 255, 255)
WHITE = (255, 255, 255)
COLOR_NEW = (255, 0, 0)


def _get_platform_sprite(file, size):
    sprite_sheet = SpriteSheet(file)
    position = (0, 0, size[0], size[1])
    sprite = sprite_sheet.image_at(position)
    return sprite


class Platform(pygame.sprite.Sprite):
    def __init__(self, size=None, position=None, moving=True):
        super().__init__()
        if size is None:
            size = (MAX_PLATFORM_WIDTH, PLATFORM_HEIGHT)
        self.surf = _get_platform_sprite("assets/sprites/platforms/platform.png", size)
        pygame.Surface(size)

        self.height = self.surf.get_height()
        self.width = self.surf.get_width()
        self.health = PLATFORM_HEALTH
        self.half_broken = False

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
        self.half_broken = True
        self.surf.fill((255, 0, 0))

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



def _get_player_sprite(file):
    sprite = pygame.image.load(file).convert()
    colorkey = sprite.get_at((0,0))
    sprite.set_colorkey(colorkey, pygame.RLEACCEL)

    return pygame.transform.scale(sprite, (PLAYER_WIDTH, PLAYER_HEIGHT))

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.sprites = {}
        normal_sprite = _get_player_sprite("assets/sprites/player/normal.png")

        self.sprites["normal"] = normal_sprite
        self.surf = normal_sprite

        self.sprites["invert"] = _get_player_sprite("assets/sprites/player/invert.png")

        self.sprites["middle"] = _get_player_sprite("assets/sprites/player/middle.png")
        
        self.rect = self.surf.get_rect()
        self.vel = vec(0, 0)
        self.jumping = False
        self.score = 0
        self.collided_platform = None
        self.pos = vec(WIDTH // 2, HEIGHT - 50)
        self.update_rect()
        self.flash = True

    def collision(self):
        gs.P1.collided_platform = None
        hits = pygame.sprite.spritecollide(self, gs.platforms, False)

        if len(hits) == 0:
            return
        # TODO move gs.platforms also
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

            # if players and platform move in opposite directions then shift the player by the gs.platforms velocity
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
        if gs.horizontally_inverted:
            self.surf = self.sprites["invert"]
        else:
            self.surf = self.sprites["normal"]
        
        self.vel = vec(0, self.vel.y)
        self.vel.y += GRAVITY

        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[K_LEFT]:
            # pygame.mixer.Sound.play(gs.sounds["x_movement"])
            self.vel.x = -PLAYER_HORIZONTAL_VEL
        if pressed_keys[K_RIGHT]:
            # pygame.mixer.Sound.play(gs.sounds["x_movement"])
            self.vel.x = PLAYER_HORIZONTAL_VEL
        self.vel.x *= -1 if gs.horizontally_inverted else 1


        hits = pygame.sprite.spritecollide(self, gs.platforms, False)
        if pressed_keys[K_SPACE] and len(hits) > 0 and not self.jumping:
            # jumping
            self.jumping = True
            self.vel.y = -JUMP_SPEED
            self.collided_platform = None

        for event in pygame.event.get():
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    gs.P1.cancel_jump()
    
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

    def update_rect(self):
        self.rect.midbottom = int(self.pos.x), int(self.pos.y)

class GlobalState:
    def __init__(self) -> None:
        self.P1 = None
        self.hInvert = 100
        self.hInvertDec = random.randint(20, 30) / 100
        self.vInvert = 100
        self.vInvertDec = random.randint(5, 8) / 100
        self.displaysurface = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.SCALED, vsync=1)
        self.horizontally_inverted = False
        self.vertically_inverted = False
        self.lives = 5
        self.PT1 = None
        self.difficulty = 0
        self.phase_layers = PHASE_MAX_LAYERS + 1
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.falling = False
        self.top_platforms = []
        self.current_phase = 0
        self.save_platform = None
        self.FramePerSec = pygame.time.Clock()
        self.score = 0
        self.sounds = {}

    def load_sounds(self):
        sounds = ["damage", "background", "x_movement", "death", "gonna_flip", "vertical_flip"]
        for sound in sounds:
            self.sounds[sound] = pygame.mixer.Sound(f"assets/sound/{sound}.mp3")

        self.sounds["flip"] = pygame.mixer.Sound(f"assets/sound/flip.wav")
        self.sounds["jump"] = pygame.mixer.Sound(f"assets/sound/jump.wav")
        print("LOADED SOUND")

gs = GlobalState()

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

def add_stack(staggered=False):
    center = (random.random() * 0.33 + 0.33) * WIDTH
    prev_plat = gs.top_platforms[-1]

    offsets = [0, 1, -1]
    for idx in range(PHASE_MAX_LAYERS):
        for offset in offsets:
            new_height = prev_plat.pos.y - JUMP_HEIGHT * min(0.9 + gs.difficulty / 10, 1)
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
            gs.platforms.add(pl)
            gs.all_sprites.add(pl)
        prev_plat = pl

    gs.top_platforms = [pl]

    return PHASE_MAX_LAYERS * len(offsets)


def add_random_platform():
    
    new_layer = False
    if len(gs.top_platforms) >= 2 or random.random() < 0.5:
        new_layer = True
        prev_platform = random.choice(gs.top_platforms)
        prev_height = prev_platform.pos.y
        new_height = prev_height - JUMP_HEIGHT * min(1, 0.75 + gs.difficulty / 10)
        min_horizontal_dist = MAX_PLATFORM_WIDTH * 0.5 * min(1, 0.9 + gs.difficulty / 10)
        max_horizontal_dist = JUMP_HEIGHT * 1.75 * PLAYER_HORIZONTAL_VEL / JUMP_SPEED
    else:
        new_layer = False
        prev_platform = gs.top_platforms[0]
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
    gs.platforms.add(pl)
    gs.all_sprites.add(pl)

    if new_layer:
        gs.top_platforms = [pl]
    else:
        gs.top_platforms.append(pl)

    if new_layer:
        return 1

    return 0


def add_staircase():
    # logging.debug("Adding a new staircase")
    # start from a random platform
    prev_platform = random.choice(gs.top_platforms)
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
            3, gs.difficulty * 0.5
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
        gs.platforms.add(pl)
        gs.all_sprites.add(pl)
        prev_platform = pl

    gs.top_platforms = [pl]

    return pt_count


def add_platforms():
    prev_platform = gs.top_platforms[-1]
    prev_height = prev_platform.pos.y
    if prev_height < -50:
        return

    if gs.phase_layers >= PHASE_MAX_LAYERS:
        prev_phase = gs.current_phase
        while prev_phase == gs.current_phase:
            gs.current_phase = random.randint(0, 3)
        gs.phase_layers = 0
        gs.difficulty += 1

    if gs.current_phase == 0:
        gs.phase_layers += add_staircase()
    elif gs.current_phase == 1:
        gs.phase_layers += add_random_platform()
    elif gs.current_phase == 2:
        gs.phase_layers += add_stack()
    elif gs.current_phase == 3:
        gs.phase_layers += add_stack(staggered=True)


def init():
    global gs
    gs = GlobalState()
    gs.load_sounds()

    gs.sounds["background"].play(-1)

    gs.P1 = Player()
    gs.all_sprites.add(gs.P1)

    gs.PT1 = Platform(
        size=(WIDTH * 1.5, PLATFORM_HEIGHT),
        position=(WIDTH // 2, HEIGHT - 30),
        moving=False,
    )
    gs.PT1.health = 100 * PLATFORM_HEALTH
    gs.platforms.add(gs.PT1)
    gs.all_sprites.add(gs.PT1)
    gs.top_platforms.append(gs.PT1)

    add_platforms()


def keyboard_events():
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            pressed_keys = pygame.key.get_pressed()
            if pressed_keys[K_SPACE]:
                gs.sounds["jump"].play()
            if pressed_keys[K_x]:
                pygame.quit()
                sys.exit()

            if pressed_keys[K_r]:
                return -1

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                gs.P1.cancel_jump()


def end_game():
    for entity in gs.all_sprites:
        entity.kill()
        # time.sleep(1)
        # gs.displaysurface.fill((255, 0, 0))
        # pygame.display.update()
        # pygame.quit()
        # sys.exit()


def camera():
    global gs
    v = 2

    if gs.P1.pos.y > 0.96 * HEIGHT and gs.P1.collided_platform == None and gs.P1.vel.y >= 0 and not gs.falling:
        gs.falling = True

        # DAMAGE SOUND
        pygame.mixer.Sound.play(gs.sounds["damage"])
        gs.lives -= 1
        if gs.lives == 0:
            pygame.mixer.Sound.play(gs.sounds["death"])
            return -1

    if gs.falling and gs.P1.collided_platform is not None:
        gs.falling = False
        gs.save_platform = gs.P1.collided_platform
  
    if gs.falling:
        v = -(PLAYER_TERMINAL_VEL + 2)
        
    if gs.falling and gs.P1.pos.y < HEIGHT * 0.35:
        v = -PLAYER_TERMINAL_VEL

    if gs.P1.collided_platform != None and (gs.P1.collided_platform == gs.PT1 or gs.P1.collided_platform == gs.save_platform):
        v = 0         

    if gs.P1.pos.y > 0.98 * HEIGHT and gs.P1.collided_platform != None and gs.P1.collided_platform != gs.PT1:
        gs.lives -= 1
        if gs.lives == 0:
            return -1  
        v = -HEIGHT/2
        gs.save_platform = gs.P1.collided_platform

    gs.P1.pos.y += v
    for plat in gs.platforms:
        plat.pos.y += v

    gs.score += v


def game_loop():
    about_to_horizontal = True
    about_to_vertical = True
    while True:
        # handle keyboard input
        if keyboard_events() == -1:
            return
        
        if camera() == -1:
            return
        # move entities and check for collision
        gs.P1.move()
        [entity.move() for entity in gs.platforms]
        gs.P1.collision()

        add_platforms()

        gs.P1.update_rect()

        # handle the inversion counters
        gs.hInvert -= gs.hInvertDec
        gs.vInvert -= gs.vInvertDec

        if gs.hInvert <= 0:
            # HORIZONTAL FLIP SOUND
            gs.sounds["flip"].play()

            gs.horizontally_inverted = not gs.horizontally_inverted
            gs.hInvert = 200
            gs.hInvertDec = random.randint(20, 30) / 100
            about_to_horizontal = True

        if gs.vInvert <= 0:
            # VERTICAL FLIP SOUND
            gs.sounds["flip"].play()

            gs.vertically_inverted = not gs.vertically_inverted
            gs.vInvert = 100
            gs.vInvertDec = random.randint(5, 8) / 100
            about_to_vertical = True

        if gs.vertically_inverted:
            gs.displaysurface.fill(BG1)
        else:
            gs.displaysurface.fill(BG2)

        if gs.vInvert <= 10:
            if about_to_vertical:
                about_to_vertical = False
                gs.sounds["vertical_flip"].play()
            floor_val = gs.vInvert // 5
            if floor_val % 2 == 0:
                gs.displaysurface.fill((200, 200, 200))

        if gs.hInvert <= 40:
            # GONNA FLIP
            if about_to_horizontal:
                gs.sounds["gonna_flip"].play()
                about_to_horizontal = False
            floor_val = gs.hInvert // 5
            if floor_val % 2 == 0:
                gs.P1.surf = gs.P1.sprites["middle"]


        for entity in gs.all_sprites:
            gs.displaysurface.blit(entity.surf, entity.rect)
      
        if gs.vertically_inverted:
          gs.displaysurface.blit(pygame.transform.rotate(gs.displaysurface, 180), (0, 0))

        f = pygame.font.SysFont("Verdana", 20)
        g = f.render(str(f"Score: {int((gs.score - gs.P1.pos.y + 856) // 10)} Lives: {gs.lives}"), True, (0, 0, 0))
        gs.displaysurface.blit(g, (WIDTH / 2, 10))


        pygame.display.update()
        gs.FramePerSec.tick(FPS)


def main():
    global damage
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    pygame.init()
    pygame.mixer.init() 

    pygame.display.set_caption("Right?")
    while True:
        init()
        game_loop()


if __name__ == "__main__":
    main()
