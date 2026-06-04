from ctypes import HRESULT

import pygame
import sys
import time
from datetime import datetime

# Инициализация pygame
pygame.init()

# Константы
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (255, 100, 100)
BLUE = (100, 100, 255)
GREEN = (100, 255, 100)
YELLOW = (255, 255, 100)

class GraphicalGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Агент под прикрытием - Поиск предметов")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)

        # Загрузка изображений фонов (создаём заглушки, если файлов нет)
        self.backgrounds = {}
        self.load_backgrounds()

        # Игровые переменные
        self.current_room = "hall"
        self.inventory = []
        self.tasks = {
            "usb_logs": False,
            "crack_safe": False,
            "upload_trojan": False
        }
        self.found_passwords = {
            "safe_password": None,    # пароль от сейфа
            "pc_password": None       # пароль от компьютера
        }

        self.start_time = time.time()
        self.time_limit = 300  # 5 минут
        self.game_over = False
        self.game_active = True
        self.won = False
        self.message = ""
        self.message_timer = 0

        # Локации
        self.rooms = {
            "hall": {
                "name": "Прихожая",
                "desc": "Тёмный коридор. На стене висит странная картина.",
                "items": ["ключ"],
                "exits": {"Кабинет": "office", "Гостиная": "living"},
                "hidden": []
            },
            "office": {
                "name": "Кабинет",
                "desc": "Стол, компьютер, книжный шкаф. На полке сейф.",
                "items": [],
                "exits": {"Прихожая": "hall"},
                "hidden": []
            },
            "living": {
                "name": "Гостиная",
                "desc": "Диван, телевизор, журнальный столик. Розетка у стены.",
                "items": [],
                "exits": {"Прихожая": "hall"},
                "hidden": []
            }
        }

        # Интерактивные объекты на локациях (для кликов)
        self.interactive_objects = {
            "hall": [
                {"name": "картина", "rel_rect":(0.33, 0.08, 0.12, 0.14), "action": "examine", "result": "Странная картина... На обороте ничего нет."},
                {"name": "дверь", "rel_rect":(0.53, 0.07, 0.20, 0.40), "action": "examine", "result": "Я не могу сейчас уйти. Задание еще не выполнено."},
                {"name": "комод", "rel_rect":(0.03, 0.29, 0.15, 0.20), "action": "examine", "result": "Бесполезно... Комод пуст."},
                {"name": "цветок", "rel_rect": (0.23, 0.28, 0.07, 0.20), "action": "take_key", "item": "ключ", "result": "В горшке ключ. Теперь можно попасть в кабинет."},


                {"name": "в кабинет", "rel_rect":(0.92, 0.51, 0.07, 0.10), "action": "transition", "target":"office", "requires_key": True},
                {"name": "в гостиную", "rel_rect":(0.01, 0.52, 0.07, 0.10), "action": "transition", "target":"living", "requires_key": True}
            ],
            "office": [
                {"name": "сейф", "rel_rect":(0.72, 0.50, 0.05, 0.12), "action": "puzzle", "puzzle_type": "safe"},
                {"name": "компьютер", "rel_rect":(0.37, 0.27, 0.12, 0.10), "action": "puzzle", "puzzle_type": "laptop"},
                {"name": "книжный шкаф", "rel_rect":(0.75, 0.15, 0.25, 0.30), "action": "search", "result": "Вы обыскали шкаф, но ничего не нашли."},
                {"name": "ящики", "rel_rect":(0.80, 0.65, 0.12, 0.17), "action": "take_key_2","item":"ключ_2", "result": "В одном из ящиков лежал ключ от гостиной."},
                {"name": "документы", "rel_rect":(0.28, 0.32, 0.05, 0.10), "action": "take_pc_password", "item":"пароль(ПК)", "result": "Найден пароль от компьютера!"},

                {"name": "в коридор", "rel_rect":(0.43, 0.85, 0.05, 0.06), "action": "transition", "target":"hall"}
            ],
            "living": [
                {"name": "подушка", "rel_rect":(0.79, 0.63, 0.13, 0.10), "action": "take_password", "item":"пароль(C)", "result":"Вы нашли пароль от сейфа"},
                {"name": "окно", "rel_rect":(0.45, 0.10, 0.20, 0.50), "action": "examine", "result":"За окном никого..но это пока."},
                {"name": "тумба","rel_rect":(0.20, 0.70, 0.17, 0.12),"action": "take_screwdriver", "item": "отвертка", "result":"Вы нашли отвертку!"},
                {"name": "розетка", "rel_rect":(0.01, 0.77, 0.03, 0.05), "action": "use_screwdriwer", "gives_item": "флешка", "result": "Вы вскрыли розетку и нашли тайник!", "requires":"отвертка"},
                {"name": "телевизор", "rel_rect":(0.15, 0.35, 0.15, 0.20), "action": "examine", "result":"Телевизор не работает."},

                {"name": "в коридор", "rel_rect":(0.43, 0.90, 0.05, 0.07), "action": "transition", "target":"hall"}
            ]
        }

        self.current_rects = {}
        self.update_interactive_rects()

        # Головоломки
        self.puzzles = {
            "safe": {
                "solved": False,
                "question": "Код от сейфа (4 цифры):",
                "answer": "1234",
                "success": "Сейф открыт! Вы нашли документы."
            },
            "laptop": {
                "solved": False,
                "question": "Пароль администратора:",
                "answer": "4321",
                "success": "Вы загрузили троян."
            }
        }

        # Кнопки интерфейса
        self.buttons = []
        self.create_buttons()

        # Поле для ввода (для головоломок)
        self.input_active = False
        self.input_text = ""
        self.current_puzzle = None

    def update_interactive_rects(self):
        screen_width, screen_height = self.screen.get_size()
        top_offset = 80

        for room_name, objects in self.interactive_objects.items():
            for obj in objects:
                if "rel_rect" in obj:
                    rel_x, rel_y, rel_w, rel_h = obj["rel_rect"]
                    obj["rect"] = pygame.Rect(
                        int(rel_x * screen_width),
                        int(top_offset + rel_y * (screen_height - top_offset)),
                        int(rel_w * screen_width),
                        int(rel_h * (screen_height - top_offset))
                    )


    def load_backgrounds(self):
        """Загрузка фоновых изображений (создаём цветные заглушки, если нет файлов)"""
        rooms = ["hall", "office", "living"]
        colors = [GRAY, DARK_GRAY, (80, 80, 100)]

        for i, room in enumerate(rooms):
            try:
                img = pygame.image.load(f"images/{room}.jpg")
                img = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.backgrounds[room] = img
            except:
                # Создаём цветной фон-заглушку
                surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                surf.fill(colors[i])
                # Рисуем простой паттерн
                for x in range(0, SCREEN_WIDTH, 50):
                    pygame.draw.line(surf, WHITE, (x, 0), (x, SCREEN_HEIGHT), 1)
                for y in range(0, SCREEN_HEIGHT, 50):
                    pygame.draw.line(surf, WHITE, (0, y), (SCREEN_WIDTH, y), 1)
                self.backgrounds[room] = surf
                print(f"Создан фон-заглушка для {room}. Добавьте изображения в папку images/")

    def create_buttons(self):
        """Создание кнопок интерфейса"""
        screen_width, screen_height = self.screen.get_size()
        button_y = screen_height - 50
        buttons_data = [
            ("Задания", screen_width - 290, button_y, self.show_tasks),
            ("Выход", screen_width - 170, button_y, self.quit_game)
        ]
        self.buttons = []
        for text, x, y, action in buttons_data:
            self.buttons.append({
                "rect": pygame.Rect(x, y, 120, 40),
                "text": text,
                "action": action
            })

    def draw_room(self):
        """Отрисовка текущей комнаты"""
        screen_width, screen_height = self.screen.get_size()

        # Фон
        scaled_bg = pygame.transform.scale(self.backgrounds[self.current_room], (screen_width, screen_height))
        self.screen.blit(scaled_bg, (0, 0))

        # Название комнаты
        room_name = self.rooms[self.current_room]["name"]
        title_surf = self.font.render(room_name, True, WHITE)
        title_rect = title_surf.get_rect(center = (screen_width//2, int(100*screen_height/1000)))

        bg_rect = pygame.Rect(0, int(10 * screen_height / 1000), screen_width, int(50*screen_height/1000))
        s = pygame.Surface((screen_width, int(50*screen_height/1000)), pygame.SRCALPHA)
        self.screen.blit(s, (0, int(10*screen_height/1000)))
        self.screen.blit(title_surf, title_rect)

        # Описание комнаты
        font_size = max(20, int(24*screen_height/1000))
        self.small_font = pygame.font.Font(None, font_size)

        desc_lines = self.wrap_text(self.rooms[self.current_room]["desc"], 40)
        for i, line in enumerate(desc_lines):
            desc_surf = self.small_font.render(line, True, WHITE)
            self.screen.blit(desc_surf, (int(50*screen_width/1500), int(100*screen_height/1000 + i * 25 * screen_height/1000)))

        # Инвентарь (внизу)
        self.draw_inventory_bar()

        # Таймер
        if self.game_active:
            time_left = max(0, self.time_limit - (time.time() - self.start_time))
        else:
            if self.won:
                elapsed = self.time_limit - (time.time() - self.start_time)
                time_left = max(0, elapsed)
            else:
                time_left = 0

        minutes = int(time_left // 60)
        seconds = int(time_left % 60)
        timer_text = f"⏰ {minutes:02d}:{seconds:02d}"
        timer_surf = self.font.render(timer_text, True, RED if time_left < 60 and self.game_active else WHITE)
        self.screen.blit(timer_surf, (SCREEN_WIDTH - 150, 20))

        self.draw_passwords()

        # Сообщение
        if self.message and time.time() < self.message_timer:
            msg_surf = self.small_font.render(self.message, True, BLACK)
            msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
            self.screen.blit(msg_surf, msg_rect)

        # Кнопки интерфейса
        for button in self.buttons:
            pygame.draw.rect(self.screen, GRAY, button["rect"])
            pygame.draw.rect(self.screen, WHITE, button["rect"], 2)
            text = self.small_font.render(button["text"], True, WHITE)
            text_rect = text.get_rect(center=button["rect"].center)
            self.screen.blit(text, text_rect)

        # Рисуем интерактивные объекты (подсветка при наведении)
        mouse_pos = pygame.mouse.get_pos()
        for obj in self.interactive_objects.get(self.current_room, []):
            if obj["rect"].collidepoint(mouse_pos):
                s = pygame.Surface((obj["rect"].width, obj["rect"].height), pygame.SRCALPHA)
                s.fill((255, 255, 255, 80))
                self.screen.blit(s, obj["rect"])
                # Показываем название
                name_surf = self.small_font.render(obj["name"], True, BLACK)
                self.screen.blit(name_surf, (obj["rect"].x, obj["rect"].y - 25))

    def draw_inventory_bar(self):
        """Отрисовка инвентаря внизу экрана"""
        screen_width, screen_height = self.screen.get_size()
        bar_height = 60
        s = pygame.Surface((screen_width, bar_height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 90))
        self.screen.blit(s, (0, 0))

        inv_text = self.font.render("ИНВЕНТАРЬ:", True, WHITE)
        self.screen.blit(inv_text, (10, 25))

        # Отображаем предметы
        for i, item in enumerate(self.inventory):
            x = 150 + i * 100
            pygame.draw.rect(self.screen, DARK_GRAY, (x, 15, 75, 30))
            pygame.draw.rect(self.screen, WHITE, (x, 15, 75, 30), 1)

            if len(item) > 10:
                item_text = self.small_font.render(item[:15], True, WHITE)
            else:
                item_text = self.small_font.render(item, True, WHITE)
                self.screen.blit(item_text, (x + 5, 20))

    def wrap_text(self, text, max_chars):
        """Перенос текста на новую строку"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            if len(' '.join(current_line + [word])) <= max_chars:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def handle_click(self, pos):
        """Обработка кликов мыши"""
        if not self.game_active:
            return

        # Проверка кнопок выходов
        if hasattr(self, 'exit_buttons'):
            for btn in self.exit_buttons:
                if btn["rect"].collidepoint(pos):
                    target_room = btn["room"]

                    if target_room == "office" and "ключ" not in self.inventory:
                        self.set_message("Дверь в кабинет заперта! Нужен ключ.")
                        return

                    self.current_room = target_room
                    self.message = f"Вы перешли в {self.rooms[self.current_room]['name']}"
                    self.message_timer = time.time() + 2
                    return

        # Проверка кнопок интерфейса
        for button in self.buttons:
            if button["rect"].collidepoint(pos):
                button["action"]()
                return

        # Проверка интерактивных объектов
        for obj in self.interactive_objects.get(self.current_room, []):
            if obj["rect"].collidepoint(pos):
                self.interact_with_object(obj)
                return

    def interact_with_object(self, obj):
        """Взаимодействие с объектом"""
        # Обработка переходов между комнатами
        if obj.get("action") == "transition":
            target = obj.get("target")
            requires_key = obj.get("requires_key", False)

            # Проверка на наличие ключа для входа в кабинет
            if requires_key and target == "office" and "ключ" not in self.inventory:
                self.set_message("🔒 Дверь в кабинет заперта!")
                return

            # Проверка на наличие ключа для входа в гостиную
            if requires_key and target == "living" and "ключ" not in self.inventory:
                self.set_message("🔒 Дверь в гостиную заперта!")
                return

            if target:
                self.current_room = target
                self.message = f"Вы перешли в {self.rooms[self.current_room]['name']}"
                self.message_timer = time.time() + 2
            return

        # Обработка взятия ключа из цветка
        if obj.get("action") == "take_key":
            item_name = obj.get("item")
            if item_name and item_name not in self.inventory:
                self.inventory.append(item_name)
                self.set_message(obj.get("result", f"Вы нашли {item_name}!"))
                # Удаляем предмет из комнаты, если он там был
                room = self.rooms[self.current_room]
                if item_name in room["items"]:
                    room["items"].remove(item_name)
                obj["action"] = "examine"
                obj["result"] = "Обычный цветок. Под ним уже ничего нет."
                return
            else:
                self.set_message("Под цветком больше ничего нет.")
                return

        #обработка взятия отвертки
        if obj.get("action") == "take_screwdriver":
            item_name = obj.get("item")
            if item_name and item_name not in self.inventory:
                self.inventory.append(item_name)
                self.set_message(obj.get("result", f"Вы нашли {item_name}!"))
                # Удаляем предмет из комнаты, если он там был
                room = self.rooms[self.current_room]
                if item_name in room["items"]:
                    room["items"].remove(item_name)
                # Меняем описание тумбы
                obj["action"] = "examine"
                obj["result"] = "Обычная тумба. Там уже ничего нет."
                return
            else:
                self.set_message("Просто старая тумба. Я ее уже осмотрел..")
                return

        #использование отвертки с розеткой
        if obj.get("action") == "use_screwdriwer":
            required_item = obj.get("requires")
            if required_item in self.inventory:
                self.inventory.remove(required_item)

                self.set_message(obj.get("result", f"Вы использовали {required_item}!"))

                gives_item = obj.get("gives_item")
                if gives_item and gives_item not in self.inventory:
                    self.inventory.append(gives_item)
                    self.set_message(f"Вы нашли {gives_item}!")

                    if gives_item == "флешка":
                        self.tasks["usb_logs"] = True
                        self.set_message("Задание выполнено: найдена флешка с логами!")

                obj["action"] = "examine"
                obj["result"] = "Сломанная розетка. Внутри больше ничего нет."
                return
            else:
                self.set_message(f"Вам нужна {required_item} для этого.")

        # Обработка взятия ключа из книжного шкафа
        if obj.get("action") == "take_key_2":
            item_name = obj.get("item")
            if item_name and item_name not in self.inventory:
                self.inventory.append(item_name)
                self.set_message(obj.get("result", f"Вы нашли {item_name}!"))
                # Удаляем предмет из комнаты, если он там был
                room = self.rooms[self.current_room]
                if item_name in room["items"]:
                    room["items"].remove(item_name)
                # Меняем описание шкафа, чтобы ключ нельзя было взять дважды
                obj["action"] = "examine"
                obj["result"] = "В шкафу больше ничего нет."
                return
            else:
                self.set_message("Шкаф пуст.")
                return

        #обработка взятия пароля от ПК
        if obj.get("action") == "take_pc_password":
            item_name = obj.get("item")
            if item_name and item_name not in self.inventory:
                self.inventory.append(item_name)
                self.found_passwords["pc_password"] = "4321"
                self.set_message(obj.get("result", f"Вы нашли {item_name}!"))

                room = self.rooms[self.current_room]
                if item_name in room["items"]:
                    room["items"].remove(item_name)
                obj["action"] = "examine"
                obj["result"] = "Просто квартальные отчеты. Ничего интересного."
                return
            else:
                self.set_message("Здесь больше нечего искать.")
                return

        #обработка взятия пароля от сейфа
        #обработка взятия пароля от сейфа
        if obj.get("action") == "take_password":
            item_name = obj.get("item")
            if item_name and item_name not in self.inventory:
                self.inventory.append(item_name)
                self.found_passwords["safe_password"] = "1234"
                self.set_message(obj.get("result", f"Вы нашли {item_name}!"))

                room = self.rooms[self.current_room]
                if item_name in room["items"]:
                    room["items"].remove(item_name)

                obj["action"] = "examine"
                obj["result"] = "Под подушкой больше ничего нет."
                return
            else:
                self.set_message("Просто подушка")
                return

        # Проверяем, можно ли взять предмет (если это клик по предмету в комнате)
        room = self.rooms[self.current_room]
        for item in room["items"]:
            # Простая проверка - если название предмета есть в имени объекта
            if item in obj["name"].lower():
                self.take_item(item)
                return

        # Остальные взаимодействия
        if obj["action"] == "examine":
            self.set_message(obj["result"])
        elif obj["action"] == "search":
            self.set_message(obj["result"])
            # Если при поиске находим предмет
            if "find_item" in obj:
                self.take_item(obj["find_item"])
        elif obj["action"] == "interact":
            if "requires" in obj:
                if obj["requires"] in self.inventory:
                    self.set_message(obj["result"])
                    # Добавляем новые предметы
                    if "тайник" not in self.rooms["living"]["items"]:
                        self.rooms["living"]["items"].append("тайник")
                        self.set_message("Появился предмет 'тайник'!")
                else:
                    self.set_message(f"Вам нужна {obj['requires']} для этого")
        elif obj["action"] == "puzzle":
            puzzle_type = obj.get("puzzle_type")
            if puzzle_type and puzzle_type in self.puzzles:
                if not self.puzzles[puzzle_type]["solved"]:
                    if not self.input_active:
                        self.start_puzzle(puzzle_type)
                    else:
                        self.set_message("Сначала решите текущую головоломку.")
                else:
                    self.set_message("Головоломка уже решена")
            else:
                self.set_message("Ошибка, неизвестная головоломка")

    def start_puzzle(self, puzzle_type):
        """Начало головоломки с вводом"""
        self.input_active = True
        self.current_puzzle = puzzle_type
        self.input_text = ""

        if puzzle_type in self.puzzles:
            self.set_message(f"Введите {self.puzzles[puzzle_type]['question']}")
        else:
            self.set_message(f"Ошибка: головоломка '{puzzle_type}' не найдена!")
            self.input_active = False
            self.current_puzzle = None

    def handle_input(self, event):
        """Обработка ввода для головоломок"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.check_puzzle_answer()
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.input_active = False
                self.current_puzzle = None
                self.input_text = ""
                self.set_message("Ввод отменен.")
            else:
                if len(self.input_text) < 20 and event.unicode.isprintable():
                    self.input_text += event.unicode

    def check_puzzle_answer(self):
        """Проверка ответа головоломки"""
        if self.current_puzzle is None:
            self.input_active = False
            return

        if self.current_puzzle not in self.puzzles:
            self.set_message("Ошибка: головоломка не найдена!")
            self.input_active = False
            self.current_puzzle = None
            return

        puzzle = self.puzzles[self.current_puzzle]
        user_answer = self.input_text.strip()

        if user_answer == puzzle["answer"]:
            puzzle["solved"] = True
            self.set_message(puzzle["success"])

            if self.current_puzzle == "safe":
                self.tasks["crack_safe"] = True
                if "документы" not in self.rooms["office"]["items"]:
                    self.rooms["office"]["items"].append("документы")
                    self.set_message("📄 Документы с компроматом появились в комнате!")
            elif self.current_puzzle == "laptop":
                self.tasks["upload_trojan"] = True
                self.set_message("💻 Троян загружен!")
        else:
            self.set_message(f"❌ Неверный {puzzle['question']}")

        self.input_active = False
        self.current_puzzle = None
        self.input_text = ""

    def search_room(self):
        """Поиск скрытых предметов в комнате"""
        room = self.rooms[self.current_room]
        if room["hidden"]:
            found = []
            for h in room["hidden"]:
                if h not in self.inventory and h not in room["items"]:
                    room["items"].append(h)
                    found.append(h)
            room["hidden"] = []
            if found:
                self.set_message(f"Вы нашли: {', '.join(found)}. Взять предметы можно кликнув на них.")
            else:
                self.set_message("Вы ничего нового не нашли.")
        else:
            self.set_message("Здесь больше нечего искать.")

    def draw_passwords(self):
        """Отрисовка найденных паролей на экране"""
        screen_width, screen_height = self.screen.get_size()

    # Позиция для отображения паролей (правый верхний угол, ниже таймера)
        start_x = screen_width - 250
        start_y = 60

    # Фон для области паролей
        bg_rect = pygame.Rect(start_x - 10, start_y - 10, 240, 70)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        self.screen.blit(s, bg_rect)

    # Заголовок
        title_surf = self.small_font.render("НАЙДЕННЫЕ ПАРОЛИ:", True, YELLOW)
        self.screen.blit(title_surf, (start_x, start_y))

    # Пароль от сейфа
        if self.found_passwords["safe_password"]:
            safe_text = f"🔐 Сейф: {self.found_passwords['safe_password']}"
            safe_surf = self.small_font.render(safe_text, True, GREEN)
            self.screen.blit(safe_surf, (start_x, start_y + 25))
        else:
            safe_text = "🔐 Сейф: ???"
            safe_surf = self.small_font.render(safe_text, True, RED)
            self.screen.blit(safe_surf, (start_x, start_y + 25))

    # Пароль от ПК
        if self.found_passwords["pc_password"]:
            pc_text = f"💻 Компьютер: {self.found_passwords['pc_password']}"
            pc_surf = self.small_font.render(pc_text, True, GREEN)
            self.screen.blit(pc_surf, (start_x, start_y + 45))
        else:
            pc_text = "💻 Компьютер: ???"
            pc_surf = self.small_font.render(pc_text, True, RED)
            self.screen.blit(pc_surf, (start_x, start_y + 45))

    def show_inventory(self):
        """Показать инвентарь"""
        if self.inventory:
            self.set_message(f"Инвентарь: {', '.join(self.inventory)}")
        else:
            self.set_message("Инвентарь пуст")

    def show_tasks(self):
        """Показать задания в модальном окне поверх игры"""
    # Сохраняем текущий экран
        current_screen = self.screen.copy()

    # Создаём полупрозрачный фон
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

    # Окно заданий
        task_window = pygame.Rect(SCREEN_WIDTH//2 - 250, SCREEN_HEIGHT//2 - 150, 500, 300)
        pygame.draw.rect(self.screen, DARK_GRAY, task_window)
        pygame.draw.rect(self.screen, WHITE, task_window, 3)

    # Заголовок
        title = self.font.render("СПИСОК ЗАДАНИЙ", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, task_window.y + 40))
        self.screen.blit(title, title_rect)

    # Задания
        tasks_list = [
            ("Найти флешку с логами", self.tasks["usb_logs"]),
            ("Взломать сейф", self.tasks["crack_safe"]),
            ("Загрузить троян на компьютер", self.tasks["upload_trojan"])
        ]

        y_offset = task_window.y + 90
        for task_text, completed in tasks_list:
            color = GREEN if completed else RED
            status = "✓" if completed else "✗"
            task_line = f"{status} {task_text}"
            task_surf = self.small_font.render(task_line, True, color)
            self.screen.blit(task_surf, (task_window.x + 30, y_offset))
            y_offset += 45

    # Подсказка
        hint = self.small_font.render("Нажмите любую клавишу для продолжения", True, GRAY)
        hint_rect = hint.get_rect(center=(SCREEN_WIDTH//2, task_window.y + 260))
        self.screen.blit(hint, hint_rect)

        pygame.display.flip()

    # Ожидание нажатия клавиши
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    waiting = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
                if event.type == pygame.QUIT:
                    waiting = False
                    self.game_over = True
                    return

    # Восстанавливаем экран
        self.screen.blit(current_screen, (0, 0))
        pygame.display.flip()

    def set_message(self, msg):
        """Установить временное сообщение"""
        self.message = msg
        self.message_timer = time.time() + 3

    def take_item(self, item_name):
        """Взять предмет из комнаты"""
        room = self.rooms[self.current_room]
        if item_name in room["items"]:
            self.inventory.append(item_name)
            room["items"].remove(item_name)
            self.set_message(f"Вы взяли: {item_name}")

            if item_name == "флешка":
                self.tasks["usb_logs"] = True
                self.set_message("Задание выполнено: Найдена флешка с логами!")
            return True
        return False

    def check_win(self):
        """Проверка победы"""
        return self.tasks["usb_logs"] and self.tasks["crack_safe"] and self.tasks["upload_trojan"]

        if not self.won:
            self.won = True
            self.game_over = True
            self.game_active = False
            return True
        return False

    def apply_win(self):
        """Применить состояние победы (вызывается когда условия выполнены)"""
        if self.check_win() and not self.won:
            self.won = True
            self.game_over = True
            self.game_active = False
            return True
        return False

    def quit_game(self):
        """Выход из игры"""
        self.game_over = True
        self.game_active = False

    def run(self):
        """Главный игровой цикл"""
        running = True

        while running:
            self.create_buttons()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.update_interactive_rects()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.input_active and self.game_active:
                        self.handle_click(event.pos)
                        room = self.rooms[self.current_room]
                        for item in room["items"][:]:
                            if 50 < event.pos[0] < 400 and 200 < event.pos[1] < 250:
                                self.take_item(item)

                if event.type == pygame.KEYDOWN and self.input_active and self.game_active:
                    self.handle_input(event)

            # Проверка времени (только если игра активна)
            if self.game_active and not self.game_over:
                if time.time() - self.start_time > self.time_limit:
                    self.game_over = True
                    self.game_active = False
                    self.won = False
                    self.set_message("ВРЕМЯ ВЫШЛО! Миссия провалена.")

            # Проверка победы (только если игра активна и не окончена)
            if self.game_active and not self.game_over:
                if self.check_win():
                    self.apply_win()
                    self.set_message("ПОБЕДА! Вы собрали все улики и покинули дом!")

        # Отрисовка
            self.draw_room()

        # Поле ввода для головоломок (только если игра активна)
            if self.input_active and self.current_puzzle is not None and self.game_active:
                # Полупрозрачный фон
                s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                s.fill((0, 0, 0, 200))
                self.screen.blit(s, (0, 0))

            # Окно ввода
                dialog_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 100, 400, 150)
                pygame.draw.rect(self.screen, DARK_GRAY, dialog_rect)
                pygame.draw.rect(self.screen, WHITE, dialog_rect, 3)

                question = self.puzzles[self.current_puzzle]["question"]
                q_surf = self.font.render(question, True, WHITE)
                self.screen.blit(q_surf, (dialog_rect.x + 20, dialog_rect.y + 20))

            # Поле ввода
                input_rect = pygame.Rect(dialog_rect.x + 20, dialog_rect.y + 90, 460, 40)
                pygame.draw.rect(self.screen, WHITE, input_rect, 2)
                pygame.draw.rect(self.screen, BLACK, input_rect, 0)

                text_surf = self.font.render(self.input_text + "_", True, WHITE)
                self.screen.blit(text_surf, (input_rect.x + 10, input_rect.y + 8))

                inst_surf = self.small_font.render("Нажмите ENTER для ответа", True, GRAY)
                self.screen.blit(inst_surf, (dialog_rect.x + 20, dialog_rect.y + 120))

            # Сообщение о конце игры
            if self.game_over:
                s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                s.fill((0, 0, 0, 200))
                self.screen.blit(s, (0, 0))

                elapsed_time = time.time() - self.start_time
                minutes = int(elapsed_time // 60)
                seconds = int(elapsed_time % 60)
                time_spent = f"Время: {minutes:02d}:{seconds:02d}"

                if self.won:
                    msg = "МИССИЯ ВЫПОЛНЕНА! Вы покидаете дом с уликами."
                    time_surf = self.small_font.render(time_spent, True, GREEN)
                else:
                    msg = "МИССИЯ ПРОВАЛЕНА! Вас обнаружили."
                    time_surf = self.small_font.render(time_spent, True, RED)

                msg_surf = self.font.render(msg, True, WHITE if self.won else RED)
                msg_rect = msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
                self.screen.blit(msg_surf, msg_rect)

                time_rect = time_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
                self.screen.blit(time_surf, time_rect)

                restart_surf = self.small_font.render("Закройте окно для выхода", True, WHITE)
                restart_rect = restart_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
                self.screen.blit(restart_surf, restart_rect)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
# Запуск игры
if __name__ == "__main__":
    game = GraphicalGame()
    game.run()