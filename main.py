import pygame
import sys
import math
import os
import json

# -------------------- НАСТРОЙКИ --------------------
BASE_WIDTH, BASE_HEIGHT = 1280, 720
FPS = 60

# Цвета
BLACK = (20, 20, 30)
WHITE = (240, 240, 240)
GOLD = (255, 215, 0)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
BLUE = (70, 130, 250)
PURPLE = (150, 50, 200)
SKIN_COLORS = [RED, (255, 100, 0), GOLD, PURPLE, (0, 180, 250), (255, 50, 255)]

# -------------------- ИНИЦИАЛИЗАЦИЯ --------------------
pygame.init()
screen = pygame.display.set_mode((BASE_WIDTH, BASE_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption("Кликер: Непризнанный школой владыка демонов")
clock = pygame.time.Clock()

# Гладкие шрифты
def get_font(size):
    try:
        win_dir = os.environ.get('WINDIR', 'C:\\Windows')
        font_path = os.path.join(win_dir, 'Fonts', 'segoeui.ttf')
        return pygame.font.Font(font_path, size)
    except:
        return pygame.font.Font(None, size)

font = get_font(28)
small_font = get_font(22)
title_font = get_font(32)

# -------------------- МУЗЫКА --------------------
try:
    pygame.mixer.music.load("maou.mp3")
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)
    music_playing = True
except:
    music_playing = False

# -------------------- ЗАГРУЗКА ФОНОВ --------------------
try:
    bg_image = pygame.image.load("background.png")
    bg_image = pygame.transform.smoothscale(bg_image, (BASE_WIDTH, BASE_HEIGHT))
except:
    bg_image = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
    bg_image.fill(BLACK)

try:
    battle_bg = pygame.image.load("battle_bg.png")
    battle_bg = pygame.transform.smoothscale(battle_bg, (BASE_WIDTH, BASE_HEIGHT))
except:
    battle_bg = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
    battle_bg.fill((10, 0, 20))

# -------------------- ЗАГРУЗКА СКИНОВ --------------------
skin_images = []
skin_names = [
    "Обычный Анос",
    "Пробужденный демон",
    "Владыка разрушения",
    "Божественная форма",
    "Истинный бог хаоса",
    "Анос Волдигоад (Абсолют)"
]
for i in range(1, 7):
    try:
        img = pygame.image.load(f"anos_{i}.png")
        img = pygame.transform.smoothscale(img, (200, 200))
        skin_images.append(img)
    except:
        surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        pygame.draw.circle(surf, SKIN_COLORS[i-1], (100, 100), 100)
        text = font.render("A", True, WHITE)
        surf.blit(text, (80, 70))
        skin_images.append(surf)

# -------------------- ЗАГРУЗКА ИКОНОК УЛУЧШЕНИЙ --------------------
upgrade_icons = []
icon_colors = [BLUE, (255, 100, 0), RED, GOLD, (180, 0, 220), (50, 50, 50)]
for i in range(1, 7):
    try:
        icon = pygame.image.load(f"upgrade_{i}.png")
        icon = pygame.transform.smoothscale(icon, (40, 40))
        upgrade_icons.append(icon)
    except:
        surf = pygame.Surface((40, 40))
        surf.fill(icon_colors[i-1])
        num = small_font.render(str(i), True, WHITE)
        surf.blit(num, (12, 8))
        upgrade_icons.append(surf)

# Картинка для клика (необязательно)
try:
    anos_click_img = pygame.image.load("anos_click.png")
    anos_click_img = pygame.transform.smoothscale(anos_click_img, (200, 200))
    use_click_img = True
except:
    use_click_img = False

# -------------------- БОССЫ --------------------
class Boss:
    def __init__(self, name, filename, hp, reward, requirement):
        self.name = name
        self.filename = filename
        self.max_hp = hp
        self.current_hp = hp
        self.reward = reward
        self.requirement = requirement
        self.image = None
        try:
            img = pygame.image.load(filename)
            img = pygame.transform.smoothscale(img, (300, 300))
            self.image = img
        except:
            self.image = pygame.Surface((300, 300), pygame.SRCALPHA)
            pygame.draw.circle(self.image, GOLD, (150, 150), 140)
            letter = font.render(name[0], True, BLACK)
            self.image.blit(letter, (130, 120))

bosses = [
    Boss("Ивис Некрон", "boss_1.png", 50, 200, 0),
    Boss("Цепес Инду", "boss_2.png", 600, 1800, 500),
    Boss("Эрдмейд", "boss_3.png", 3500, 9000, 3000),
    Boss("Канон", "boss_4.png", 15000, 40000, 15000),
    Boss("Амур", "boss_5.png", 80000, 200000, 100000),
]

# -------------------- ИГРОВЫЕ КЛАССЫ --------------------
class FloatingText:
    def __init__(self, x, y, text, color=GOLD):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 1.0
        self.fade_speed = 0.02
        self.vy = -2

    def update(self):
        self.y += self.vy
        self.life -= self.fade_speed
        return self.life > 0

    def draw(self, surf):
        alpha = int(255 * max(0, self.life))
        txt = font.render(self.text, True, self.color)
        txt.set_alpha(alpha)
        surf.blit(txt, (self.x - txt.get_width()//2, self.y - txt.get_height()//2))

class Game:
    def __init__(self):
        self.magic_power = 0.0
        self.click_power = 1
        self.auto_power = 0.1
        self.crit_multiplier = 1
        self.current_skin = 1
        self.unlocked_skin = 1

        self.upgrades = [
            ["Усиление клика", 15, 1, 0, "+1 к клику"],
            ["Демонический слуга", 100, 0.2, 0, "+0.2 автоклик/сек"],
            ["Анти-Глаз", 500, 0, 0, "Клик x2 навсегда"],
            ["Магический круг", 2000, 1.0, 0, "+1.0 автоклик/сек"],
            ["Кольцо разрушения", 10000, 5, 0, "+5 к клику"],
            ["Армия тьмы", 50000, 4.0, 0, "+4 автоклик/сек"],
        ]
        self.skin_thresholds = [
            (0, "Обычный Анос"),
            (500, "Пробужденный демон"),
            (2000, "Владыка разрушения"),
            (10000, "Божественная форма"),
            (50000, "Истинный бог хаоса"),
            (200000, "Анос Волдигоад (Абсолют)"),
        ]

        self.flash_timer = 0
        self.floating_texts = []
        self.click_rect = pygame.Rect(350, 220, 200, 200)
        self.shop_rects = []

        self.state = "idle"
        self.current_boss = None
        self.boss_rect = pygame.Rect(490, 150, 300, 300)

    def click(self):
        if self.state == "battle" and self.current_boss:
            dmg = self.click_power * self.crit_multiplier
            self.current_boss.current_hp -= dmg
            self.flash_timer = 5
            self.floating_texts.append(FloatingText(640, 300, f"-{dmg:.0f}", RED))
            if self.current_boss.current_hp <= 0:
                reward = self.current_boss.reward
                self.magic_power += reward
                self.floating_texts.append(FloatingText(640, 250, f"Победа! +{reward}", GREEN))
                self.state = "boss_select"
                self.current_boss = None
        else:
            gained = self.click_power * self.crit_multiplier
            self.magic_power += gained
            self.flash_timer = 5
            self.floating_texts.append(FloatingText(450, 300, f"+{gained:.1f}"))

    def update(self):
        if self.state == "idle":
            self.magic_power += self.auto_power / FPS

        self.current_skin = 1
        for i, (threshold, _) in enumerate(self.skin_thresholds):
            if self.magic_power >= threshold:
                self.current_skin = i + 1
        self.unlocked_skin = max(self.unlocked_skin, self.current_skin)

        if self.flash_timer > 0:
            self.flash_timer -= 1
        self.floating_texts = [ft for ft in self.floating_texts if ft.update()]

    def buy_upgrade(self, index):
        upgrade = self.upgrades[index]
        base_cost = upgrade[1]
        cost = int(base_cost * (1.5 ** upgrade[3]))
        if self.magic_power >= cost:
            self.magic_power -= cost
            upgrade[3] += 1
            if upgrade[0] in ("Усиление клика", "Кольцо разрушения"):
                self.click_power += upgrade[2]
            elif upgrade[0] in ("Демонический слуга", "Магический круг", "Армия тьмы"):
                self.auto_power += upgrade[2]
            elif upgrade[0] == "Анти-Глаз":
                if upgrade[3] == 1:
                    self.crit_multiplier = 2
                else:
                    self.magic_power += cost
                    upgrade[3] -= 1
                    return False
            return True
        return False

    def set_state(self, new_state):
        self.state = new_state
        if new_state != "battle":
            self.current_boss = None

    def apply_upgrades_from_save(self, bought_list):
        self.click_power = 1
        self.auto_power = 0.1
        self.crit_multiplier = 1
        for i, upgrade in enumerate(self.upgrades):
            upgrade[3] = bought_list[i]
            for _ in range(upgrade[3]):
                if upgrade[0] in ("Усиление клика", "Кольцо разрушения"):
                    self.click_power += upgrade[2]
                elif upgrade[0] in ("Демонический слуга", "Магический круг", "Армия тьмы"):
                    self.auto_power += upgrade[2]
                elif upgrade[0] == "Анти-Глаз" and upgrade[3] == 1:
                    self.crit_multiplier = 2

# -------------------- СОХРАНЕНИЕ И ЗАГРУЗКА --------------------
SAVE_FILE = "save.json"

def save_game(game_obj):
    data = {
        "magic_power": game_obj.magic_power,
        "unlocked_skin": game_obj.unlocked_skin,
        "upgrades_bought": [upg[3] for upg in game_obj.upgrades]
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def load_game(game_obj):
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        game_obj.magic_power = data["magic_power"]
        game_obj.unlocked_skin = data["unlocked_skin"]
        bought_list = data["upgrades_bought"]
        game_obj.apply_upgrades_from_save(bought_list)
        return True
    except (FileNotFoundError, json.JSONDecodeError):
        return False

# -------------------- ОТРИСОВКА ИНТЕРФЕЙСОВ --------------------
def draw_idle():
    screen.blit(bg_image, (0, 0))

    display_skin = game.unlocked_skin - 1
    current_img = skin_images[display_skin]
    if game.flash_timer > 0 and use_click_img:
        display_img = anos_click_img
    else:
        display_img = current_img

    img_rect = display_img.get_rect(center=(450, 320))
    screen.blit(display_img, img_rect)

    if game.flash_timer > 0 and not use_click_img:
        flash_surf = pygame.Surface((200, 200), pygame.SRCALPHA)
        flash_surf.fill((255, 255, 255, 100))
        screen.blit(flash_surf, (img_rect.x, img_rect.y))

    game.click_rect = img_rect

    for ft in game.floating_texts:
        ft.draw(screen)

    mp_text = font.render(f"Магическая сила: {game.magic_power:.1f}", True, GOLD)
    screen.blit(mp_text, (30, 30))

    skin_name = skin_names[display_skin]
    skin_text = font.render(f"Форма: {skin_name}", True, PURPLE)
    screen.blit(skin_text, (30, 70))

    # Магазин
    shop_x = 700
    shop_title = title_font.render("Магазин улучшений", True, WHITE)
    screen.blit(shop_title, (shop_x, 30))

    game.shop_rects = []
    y_offset = 90
    for i, upgrade in enumerate(game.upgrades):
        name, base_cost, effect, bought, desc = upgrade
        if name == "Анти-Глаз" and bought > 0:
            cost_str = "КУПЛЕНО"
            can_buy = False
        else:
            cost = int(base_cost * (1.5 ** bought))
            cost_str = str(cost)
            can_buy = game.magic_power >= cost

        icon = upgrade_icons[i]
        screen.blit(icon, (shop_x, y_offset))

        text_x = shop_x + 50
        line1 = f"{name} ({desc}) — Цена: {cost_str}"
        if name == "Анти-Глаз" and bought > 0:
            line1 += " (активен)"
        color = GREEN if can_buy else RED
        txt1 = small_font.render(line1, True, color)
        screen.blit(txt1, (text_x, y_offset))
        y_offset += 28

        line2 = f"Нажми {i+1} | Куплено: {bought}"
        txt2 = small_font.render(line2, True, WHITE)
        screen.blit(txt2, (text_x, y_offset))

        row_rect = pygame.Rect(shop_x, y_offset - 28, 550, 62)
        game.shop_rects.append(row_rect)
        y_offset += 34

    # Кнопка "Сражения"
    battle_btn = pygame.Rect(BASE_WIDTH - 200, BASE_HEIGHT - 60, 180, 40)
    pygame.draw.rect(screen, (200, 0, 0), battle_btn, border_radius=8)
    txt_btn = small_font.render("Сражения", True, WHITE)
    screen.blit(txt_btn, (battle_btn.x + 50, battle_btn.y + 10))
    game.battle_button = battle_btn

    hint = small_font.render("Кликай по Аносу или улучшениям. M — музыка. Esc — выход", True, WHITE)
    screen.blit(hint, (30, BASE_HEIGHT - 30))

def draw_boss_select():
    screen.fill((10, 0, 20))
    title_txt = title_font.render("Выбор босса", True, RED)
    screen.blit(title_txt, (BASE_WIDTH//2 - 100, 30))

    y = 100
    boss_buttons = []
    for i, boss in enumerate(bosses):
        unlocked = game.magic_power >= boss.requirement
        color = GOLD if unlocked else (100, 100, 100)
        name_line = f"{boss.name} (HP {boss.max_hp}, награда {boss.reward})"
        if not unlocked:
            name_line += f" [требуется {boss.requirement} магии]"
        txt = small_font.render(name_line, True, color)
        screen.blit(txt, (100, y))
        btn_rect = pygame.Rect(100, y, 800, 30)
        boss_buttons.append((btn_rect, i, unlocked))
        y += 50
    game.boss_buttons = boss_buttons

    back_btn = pygame.Rect(50, BASE_HEIGHT - 60, 150, 40)
    pygame.draw.rect(screen, (100, 100, 100), back_btn, border_radius=8)
    screen.blit(small_font.render("Назад", True, WHITE), (back_btn.x + 45, back_btn.y + 10))
    game.back_button_select = back_btn

def draw_battle():
    screen.blit(battle_bg, (0, 0))

    boss = game.current_boss
    if not boss:
        return

    boss_img = boss.image
    boss_rect = boss_img.get_rect(center=(BASE_WIDTH//2, BASE_HEIGHT//2-20))
    game.boss_rect = boss_rect
    screen.blit(boss_img, boss_rect)

    if game.flash_timer > 0:
        flash_surf = pygame.Surface((300, 300), pygame.SRCALPHA)
        flash_surf.fill((255, 255, 255, 80))
        screen.blit(flash_surf, (boss_rect.x, boss_rect.y))

    bar_width = 600
    bar_height = 30
    bar_x = BASE_WIDTH//2 - bar_width//2
    bar_y = 50
    hp_ratio = max(0, boss.current_hp / boss.max_hp)
    pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, (200, 50, 50), (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
    hp_text = small_font.render(f"{boss.current_hp:.0f} / {boss.max_hp}", True, WHITE)
    screen.blit(hp_text, (bar_x + 20, bar_y + 5))

    name_txt = font.render(boss.name, True, WHITE)
    screen.blit(name_txt, (bar_x, bar_y - 30))

    for ft in game.floating_texts:
        ft.draw(screen)

    flee_btn = pygame.Rect(BASE_WIDTH - 160, BASE_HEIGHT - 60, 120, 40)
    pygame.draw.rect(screen, (100, 100, 100), flee_btn, border_radius=8)
    screen.blit(small_font.render("Сбежать", True, WHITE), (flee_btn.x + 25, flee_btn.y + 10))
    game.flee_button = flee_btn

    hint = small_font.render("Кликай по боссу, чтобы атаковать!", True, WHITE)
    screen.blit(hint, (30, BASE_HEIGHT - 30))

# -------------------- ГЛАВНЫЙ ЦИКЛ --------------------
game = Game()
load_game(game)

running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game(game)
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game.state == "idle":
                    save_game(game)
                    running = False
                else:
                    game.set_state("idle")
            elif event.key == pygame.K_m:
                if music_playing:
                    pygame.mixer.music.pause()
                    music_playing = False
                else:
                    pygame.mixer.music.unpause()
                    music_playing = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if game.state == "idle":
                if game.battle_button.collidepoint(pos):
                    game.set_state("boss_select")
                clicked_shop = False
                for i, rect in enumerate(game.shop_rects):
                    if rect.collidepoint(pos):
                        game.buy_upgrade(i)
                        clicked_shop = True
                        break
                if not clicked_shop and game.click_rect.collidepoint(pos):
                    game.click()
            elif game.state == "boss_select":
                if game.back_button_select.collidepoint(pos):
                    game.set_state("idle")
                for rect, idx, unlocked in game.boss_buttons:
                    if rect.collidepoint(pos) and unlocked:
                        game.current_boss = bosses[idx]
                        game.current_boss.current_hp = game.current_boss.max_hp
                        game.state = "battle"
                        break
            elif game.state == "battle":
                if game.flee_button.collidepoint(pos):
                    game.set_state("idle")
                elif game.boss_rect.collidepoint(pos):
                    game.click()

    game.update()

    if game.state == "idle":
        draw_idle()
    elif game.state == "boss_select":
        draw_boss_select()
    elif game.state == "battle":
        draw_battle()

    pygame.display.flip()

pygame.quit()
sys.exit()