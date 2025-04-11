import random
import pygame
import pygame_menu

pygame.init()

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 550

CHARACTER_WIDTH = 300
CHARACTER_HEIGHT = 375

FIREBALL_WIDTH = 200
FIREBALL_HEIGHT = 150

FIREBALL_COOLDOWN = 1000

FPS = 60

font = pygame.font.Font(None, 40)


def load_image(file, width, height):
    image = pygame.image.load(file).convert_alpha()
    image = pygame.transform.scale(image, (width, height))
    return image


def text_render(text):
    return font.render(str(text), True, "black")


class Menu:
    def __init__(self):
        self.surface = pygame.display.set_mode((900, 550))
        self.menu = pygame_menu.Menu(
            width=900,
            height=550,
            theme=pygame_menu.themes.THEME_SOLARIZED,
            title="КОРЕЙСКАЯ БИТВА МАГОВ"
        )
        self.menu.add.label(title="Безумству храбрых поём мы песню...")
        self.menu.add.label(title="Одиночный режим")
        self.menu.add.selector("Противник: ", [("Маг молний", 1), ("Монах земли", 2), ("Случайный враг", 3)], onchange=self.set_enemy)
        self.menu.add.button("Войти в игру", self.start_single_player_game)  # Pass method reference
        self.menu.add.label(title="Кооперативный режим")
        self.menu.add.selector("Левый игрок: ", [("Маг огня", 1), ("Маг молний", 2), ("Монах земли", 3),
                               ("Случайный выбор", 4)], onchange=self.set_left_player)
        self.menu.add.selector("Правый игрок: ", [("Маг огня", 1), ("Маг молний", 2), ("Монах земли", 3),
                               ("Случайный выбор", 4)], onchange=self.set_right_player)
        self.menu.add.button("Войти в игру", self.start_cooperative_game)  # Pass method reference
        self.menu.add.button("Выйти", quit)

        self.enemies = ["lightning wizard", "earth monk"]
        self.enemy = self.enemies[0]

        self.players = ["fire wizard", "lightning wizard", "earth monk"]
        self.left_player = self.players[0]
        self.right_player = self.players[0]

        self.run()

    def set_enemy(self, selected, value):
        if value in (1, 2):
            self.enemy = self.enemies[value - 1]
        else:
            self.enemy = random.choice(self.enemies)

    def set_left_player(self, selected, value):
        if value in (1, 2, 3):
            self.left_player = self.players[value - 1]
        else:
            self.left_player = random.choice(self.players)

    def set_right_player(self, selected, value):
        if value in (1, 2, 3):
            self.right_player = self.players[value - 1]
        else:
            self.right_player = random.choice(self.players)

    def start_single_player_game(self):
        Game("single player", (self.enemy,))

    def start_cooperative_game(self):
        Game("cooperative", (self.left_player, self.right_player))

    def run(self):
        self.menu.mainloop(self.surface)



class MagicBall(pygame.sprite.Sprite):
    def __init__(self, coord, side, power, folder):
        super().__init__()

        self.side = side
        self.power = power

        self.image = load_image(f"assets/{folder}/magicball.png",
                                FIREBALL_WIDTH, FIREBALL_HEIGHT)

        if self.side == "right":
            self.image = pygame.transform.flip(self.image, True, False)

        self.rect = self.image.get_rect()

        if self.side == "right":
            self.rect.midleft = coord
        else:
            self.rect.midright = coord

        self.rect.center = coord[0], coord[1] + 120

    def update(self):
        if self.side == "right":
            self.rect.x += 4
            if self.rect.left >= SCREEN_WIDTH:
                self.kill()
        else:
            self.rect.x -= 4
            if self.rect.right <= 0:
                self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, folder="fire wizard", single_player=True):
        super().__init__()

        self.folder = folder

        self.load_animations()

        if single_player:
            self.coord = (100, SCREEN_HEIGHT // 2)
            self.current_animation = self.idle_animation_right
            self.side = "right"

            self.k_left = pygame.K_a
            self.k_right = pygame.K_d
            self.k_up = pygame.K_w
            self.k_down = pygame.K_s
            self.k_charge = pygame.K_SPACE
        else:
            self.coord = (SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2)
            self.current_animation = self.idle_animation_left
            self.side = "left"

            self.k_left = pygame.K_LEFT
            self.k_right = pygame.K_RIGHT
            self.k_up = pygame.K_UP
            self.k_down = pygame.K_DOWN
            self.k_charge = pygame.K_RCTRL

        self.hp = 200

        self.image = self.current_animation[0]
        self.current_image = 0

        self.rect = self.image.get_rect()
        self.rect.center = self.coord

        self.timer = pygame.time.get_ticks()
        self.interval = 300
        self.animation_mode = True

        self.charge_power = 0
        self.charge_indicator = pygame.Surface((self.charge_power, 10))
        self.charge_indicator.fill("red")

        self.charge_mode = False

        self.attack_mode = False
        self.attack_interval = 500
        self.fireball_timer = 0
        self.magic_balls = pygame.sprite.Group()

    def load_animations(self):
        self.idle_animation_right = [load_image(f"assets/{self.folder}/idle{i}.png",
                                                CHARACTER_WIDTH, CHARACTER_HEIGHT)
                                     for i in range(1, 4)]

        self.idle_animation_left = [pygame.transform.flip(image, True, False)
                                    for image in self.idle_animation_right]

        self.moving_animation_right = [load_image(f"assets/{self.folder}/move{i}.png",
                                                  CHARACTER_WIDTH, CHARACTER_HEIGHT)
                                       for i in range(1, 4)]

        self.moving_animation_left = [pygame.transform.flip(image, True, False)
                                      for image in self.moving_animation_right]

        self.charge = [load_image(f"assets/{self.folder}/charge.png", CHARACTER_WIDTH, CHARACTER_HEIGHT)]

        self.charge.append(pygame.transform.flip(self.charge[0], True, False))

        self.attack = [load_image(f"assets/{self.folder}/attack.png", CHARACTER_WIDTH, CHARACTER_HEIGHT)]

        self.attack.append(pygame.transform.flip(self.attack[0], True, False))

        self.down = [load_image(f"assets/{self.folder}/down.png", CHARACTER_WIDTH, CHARACTER_HEIGHT)]

        self.down.append(pygame.transform.flip(self.down[0], True, False))

    def update(self):
        direction = 0
        keys = pygame.key.get_pressed()
        if keys[self.k_left]:
            direction = -1
            self.side = "left"
        elif keys[self.k_right]:
            direction = 1
            self.side = "right"
        else:
            direction = 0
        self.handle_movement(direction, keys)
        self.handle_attack_mode()
        self.handle_animation()

    def handle_movement(self, direction, keys):
        if not self.charge_mode and not self.attack_mode:
            if direction != 0:
                self.animation_mode = True
                self.charge_mode = False
                self.rect.x += direction
                self.current_animation = self.moving_animation_left if direction == -1 else self.moving_animation_right
            elif keys[self.k_down]:
                self.animation_mode = False
                self.charge_mode = False
                self.image = self.down[self.side != "right"]

        if keys[self.k_charge] and not self.attack_mode:
            self.animation_mode = False
            self.image = self.charge[self.side != "right"]
            self.charge_mode = True
        elif not keys[self.k_charge] and self.charge_mode:
            self.charge_mode = False
            self.animation_mode = True
            self.image = self.idle_animation_right if self.side == "right" else self.idle_animation_left

            if self.attack_mode:
                return

        if self.rect.right >= SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.left <= 0:
            self.rect.left = 0

    def handle_attack_mode(self):
        if self.attack_mode and pygame.time.get_ticks() - self.timer > self.attack_interval:
            self.attack_mode = False
            self.timer = pygame.time.get_ticks()
            self.fireball_timer = pygame.time.get_ticks()

    def handle_animation(self):
        if not self.charge_mode and self.charge_power > 0:
            self.attack_mode = True

        if self.animation_mode and not self.attack_mode and pygame.time.get_ticks() - self.timer > self.interval:
            self.current_image += 1
            if self.current_image >= len(self.current_animation):
                self.current_image = 0
            self.image = self.current_animation[self.current_image]
            self.timer = pygame.time.get_ticks()

        if self.charge_mode:
            self.charge_power += 1
            self.charge_indicator = pygame.Surface((self.charge_power, 10))
            self.charge_indicator.fill("red")
            if self.charge_power == 100:
                self.attack_mode = True


        if self.attack_mode and self.charge_power > 0:
            magicball_position = self.rect.topright if self.side == "right" else self.rect.topleft
            self.magic_balls.add(MagicBall(magicball_position, self.side, self.charge_power, folder=self.folder))
            self.charge_power = 0
            self.charge_mode = False
            self.image = self.attack[self.side != "right"]
            self.timer = pygame.time.get_ticks()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, folder):
        super().__init__()

        self.hp = 200
        self.healthbar_edge = pygame.Rect(20, 20, 200, 20)

        self.folder = folder
        self.load_animations()

        self.image = self.idle_animation_right[0]
        self.current_image = 0
        self.current_animation = self.idle_animation_left

        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2)

        self.timer = pygame.time.get_ticks()
        self.interval = 300
        self.side = "left"
        self.animation_mode = True

        self.magic_balls = pygame.sprite.Group()

        self.attack_mode = False
        self.attack_interval = 500

        self.move_interval = 800
        self.move_duration = 0
        self.direction = 0
        self.move_timer = pygame.time.get_ticks()

        self.charge_power = 0

    def load_animations(self):
        self.idle_animation_right = [load_image(f"assets/{self.folder}/idle{i}.png", CHARACTER_WIDTH, CHARACTER_HEIGHT)
                                     for i in range(1, 4)]
        self.idle_animation_left = [pygame.transform.flip(image, True, False) for image in self.idle_animation_right]
        self.move_animation_right = [load_image(f"assets/{self.folder}/move{i}.png", CHARACTER_WIDTH, CHARACTER_HEIGHT)
                                     for i in range(1, 5)]
        self.move_animation_left = [pygame.transform.flip(image, True, False) for image in self.move_animation_right]
        self.attack = [load_image(f"assets/{self.folder}/attack.png", CHARACTER_WIDTH, CHARACTER_HEIGHT)]
        self.attack.append(pygame.transform.flip(self.attack[0], True, False))

        self.down = [load_image(f"assets/{self.folder}/down.png", CHARACTER_WIDTH, CHARACTER_HEIGHT)]
        self.down.append(pygame.transform.flip(self.down[0], True, False))

    def update(self, player):
        self.handle_attack_mode(player)
        self.handle_movement()
        self.handle_animation()

    def handle_attack_mode(self, player):
        if not self.attack_mode:
            attack_probability = 1

            if player.charge_mode:
                attack_probability += 2

            if random.randint(1, 150) <= attack_probability:
                self.attack_mode = True
                self.charge_power = random.randint(1, 100)

                if player.rect.centerx < self.rect.centerx:
                    self.side = "left"
                else:
                    self.side = "right"

                self.animation_mode = False
                self.image = self.attack[self.side != "right"]

        if self.attack_mode:
            if pygame.time.get_ticks() - self.timer > self.attack_interval:
                self.attack_mode = False
                self.timer = pygame.time.get_ticks()
                self.animation_mode = True
                self.handle_movement()
                self.image = self.idle_animation_left[0] if self.side == "left" else self.idle_animation_right[0]

    def handle_movement(self):
        if self.attack_mode:
            return

        now = pygame.time.get_ticks()

        if now - self.move_timer < self.move_duration:
            self.animation_mode = True
            self.rect.x += self.direction
            if self.direction == -1:
                self.current_animation = self.move_animation_left
            elif self.direction == 1:
                self.current_animation = self.move_animation_right
            elif self.direction == 2:
                self.current_animation = self.down

        else:
            if random.randint(1, 100) == 1 and now - self.move_timer > self.move_interval:
                self.move_timer = pygame.time.get_ticks()
                self.move_duration = random.randint(400, 1500)
                self.direction = random.choice([-1, 2])
            else:
                self.animation_mode = True
                self.current_animation = self.idle_animation_left if self.side == "left" else self.idle_animation_right

        if self.attack_mode:
            return

        if self.rect.right >= SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.left <= 0:
            self.rect.left = 0

    def handle_animation(self):
        if self.attack_mode and self.charge_power > 0:
            magicball_position = self.rect.topright if self.side == "right" else self.rect.topleft
            self.magic_balls.add(MagicBall(magicball_position, self.side, self.charge_power, self.folder))
            self.charge_power = 0
            self.image = self.attack[self.side != "right"]

        if self.animation_mode and not self.attack_mode and pygame.time.get_ticks() - self.timer > self.interval:
            self.current_image = (self.current_image + 1) % len(self.current_animation)
            self.image = self.current_animation[self.current_image]
            self.timer = pygame.time.get_ticks()


class Game:
    def __init__(self, mode, wizards):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Корейская битва магов")

        self.mode = mode

        self.background = load_image("assets/background.png", SCREEN_WIDTH, SCREEN_HEIGHT)
        self.foreground = load_image("assets/foreground.png", SCREEN_WIDTH, SCREEN_HEIGHT)

        if self.mode == "single player":
            self.player = Player()
            self.enemy = Enemy(wizards[0])
        else:
            self.player = Player(wizards[0])
            self.enemy = Player(wizards[1], single_player=False)

        self.clock = pygame.time.Clock()

        self.is_running = True
        self.win = None
        self.run()

    def run(self):
        while self.is_running:
            self.event()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False

            if event.type == pygame.KEYDOWN and self.win is not None:
                self.is_running = False

    def update(self):
        self.player.update()
        self.player.magic_balls.update()

        if self.mode == "single player":
            self.enemy.update(self.player)
        else:
            self.enemy.update()
        self.enemy.magic_balls.update()

        if self.player.image not in self.player.down:
            hits = pygame.sprite.spritecollide(self.player, self.enemy.magic_balls, True, pygame.sprite.collide_rect_ratio(0.3))
            for hit in hits:
                self.player.hp -= hit.power
            if self.mode == "single player" or self.enemy.image not in self.enemy.down:
                hits = pygame.sprite.spritecollide(self.enemy, self.player.magic_balls, True, pygame.sprite.collide_rect_ratio(0.3))
                for hit in hits:
                    self.enemy.hp -= hit.power
        if self.player.hp <= 0:
            self.win = self.enemy
        elif self.enemy.hp <= 0:
            self.win = self.player

    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.player.image, self.player.rect)
        self.screen.blit(self.enemy.image, self.enemy.rect)
        self.enemy.magic_balls.draw(self.screen)
        if self.player.charge_mode:
            self.screen.blit(self.player.charge_indicator, (self.player.rect.left + 120, self.player.rect.top))
        if self.mode == "cooperative":
            if self.enemy.charge_mode:
                self.screen.blit(self.enemy.charge_indicator, (self.enemy.rect.left + 120, self.enemy.rect.top))
        self.player.magic_balls.draw(self.screen)
        self.screen.blit(self.foreground, (0, 0))
        pygame.draw.rect(self.screen, "black", (20, 20, 200, 20), 2)
        pygame.draw.rect(self.screen, "green", (22, 22, self.player.hp - 4, 15))
        pygame.draw.rect(self.screen, "black", (SCREEN_WIDTH - 220, 20, 200, 20), 2)
        pygame.draw.rect(self.screen, "green", (SCREEN_WIDTH - 218, 22, self.enemy.hp - 4, 15))

        if self.win == self.player:
            text = text_render("Конец игры")
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, text_rect)
            text2 = text_render(f"Победитель: Игрок в левом углу")
            text_rect2 = text2.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2 - 200)))
            self.screen.blit(text2, text_rect2)

        elif self.win == self.enemy:
            text = text_render("Конец игры")
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(text, text_rect)
            text2 = text_render(f"Победитель: Игрок в правом углу ")
            text_rect2 = text2.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2 + 200)))
            self.screen.blit(text2, text_rect2)
        pygame.display.flip()


if __name__ == "__main__":
    Menu()
