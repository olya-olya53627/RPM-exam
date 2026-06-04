import unittest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock

# путь к корню проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class MockScreen:
    """объект для pygame экрана"""
    def get_size(self):
        return (1024, 768)

    def blit(self, *args, **kwargs):
        pass

    def copy(self):
        return MockScreen()


class TestGameVerification(unittest.TestCase):
    """Тесты верификации"""

    def setUp(self):
        """Подготовка к тестам - создание экземпляра"""
        # Создаём моки для pygame
        self.mock_display_patcher = patch('pygame.display.set_mode')
        self.mock_display = self.mock_display_patcher.start()
        self.mock_display.return_value = MockScreen()

        self.mock_caption_patcher = patch('pygame.display.set_caption')
        self.mock_caption_patcher.start()

        self.mock_font_patcher = patch('pygame.font.Font')
        self.mock_font = self.mock_font_patcher.start()
        self.mock_font.return_value = Mock()

        self.mock_init_patcher = patch('pygame.init')
        self.mock_init_patcher.start()

        # Создаём экземпляр игры
        from game import GraphicalGame
        self.game = GraphicalGame()

        # Очищаем инвентарь перед каждым тестом
        self.game.inventory = []
        self.game.tasks = {
            "usb_logs": False,
            "crack_safe": False,
            "upload_trojan": False
        }
        self.game.current_room = "hall"

    def tearDown(self):
        """Очистка после тестов"""
        self.mock_display_patcher.stop()
        self.mock_caption_patcher.stop()
        self.mock_font_patcher.stop()
        self.mock_init_patcher.stop()

    # ТЕСТЫ ВЗЯТИЯ ПРЕДМЕТОВ

    def test_take_key_from_flower(self):
        """Тест: взятие ключа из цветка"""
        flower_obj = {
            "name": "цветок",
            "action": "take_key",
            "item": "ключ",
            "result": "Найден ключ!"
        }

        with patch.object(self.game, 'set_message'):
            self.game.interact_with_object(flower_obj)

        self.assertIn("ключ", self.game.inventory)

    def test_take_screwdriver_from_drawer(self):
        """Тест: взятие отвёртки из тумбы"""
        screwdriver_obj = {
            "name": "тумба",
            "action": "take_screwdriver",
            "item": "отвертка",
            "result": "Найдена отвёртка!"
        }

        with patch.object(self.game, 'set_message'):
            self.game.interact_with_object(screwdriver_obj)

        self.assertIn("отвертка", self.game.inventory)

    def test_cannot_take_item_twice(self):
        """Тест: нельзя взять один и тот же предмет дважды"""
        key_obj = {"name": "цветок", "action": "take_key", "item": "ключ"}

        with patch.object(self.game, 'set_message'):
            self.game.interact_with_object(key_obj)
            self.assertIn("ключ", self.game.inventory)

            initial_count = len(self.game.inventory)
            self.game.interact_with_object(key_obj)

            self.assertEqual(len(self.game.inventory), initial_count)

    #ТЕСТЫ ПЕРЕХОДОВ

    def test_transition_to_office_without_key(self):
        """Тест: переход в кабинет без ключа - должен быть запрещён"""
        start_room = self.game.current_room

        transition_obj = {
            "name": "дверь в кабинет",
            "action": "transition",
            "target": "office",
            "requires_key": True
        }

        with patch.object(self.game, 'set_message'):
            self.game.interact_with_object(transition_obj)

        self.assertEqual(self.game.current_room, start_room)

    def test_transition_to_office_with_key(self):
        """Тест: переход в кабинет с ключом - должен быть разрешён"""
        self.game.inventory.append("ключ")

        transition_obj = {
            "name": "дверь в кабинет",
            "action": "transition",
            "target": "office",
            "requires_key": True
        }

        with patch.object(self.game, 'set_message'):
            self.game.interact_with_object(transition_obj)

        self.assertEqual(self.game.current_room, "office")

    def test_transition_to_living_room(self):
        """Тест: переход в гостиную"""
        transition_obj = {
            "name": "дверь в гостиную",
            "action": "transition",
            "target": "living",
            "requires_key": False
        }

        with patch.object(self.game, 'set_message'):
            self.game.interact_with_object(transition_obj)

        self.assertEqual(self.game.current_room, "living")

    #ТЕСТЫ ГОЛОВОЛОМОК

    def test_safe_puzzle_correct_password(self):
        """Тест: правильный код сейфа (1234)"""
        self.game.current_puzzle = "safe"
        self.game.input_text = "1234"
        self.game.puzzles["safe"]["solved"] = False

        with patch.object(self.game, 'set_message'):
            self.game.check_puzzle_answer()

        self.assertTrue(self.game.puzzles["safe"]["solved"])
        self.assertTrue(self.game.tasks["crack_safe"])

    def test_safe_puzzle_wrong_password(self):
        """Тест: неправильный код сейфа"""
        self.game.current_puzzle = "safe"
        self.game.input_text = "9999"
        self.game.puzzles["safe"]["solved"] = False

        with patch.object(self.game, 'set_message'):
            self.game.check_puzzle_answer()

        self.assertFalse(self.game.puzzles["safe"]["solved"])
        self.assertFalse(self.game.tasks["crack_safe"])

    def test_laptop_puzzle_correct_password(self):
        """Тест: правильный пароль компьютера (4321)"""
        self.game.current_puzzle = "laptop"
        self.game.input_text = "4321"
        self.game.puzzles["laptop"]["solved"] = False

        with patch.object(self.game, 'set_message'):
            self.game.check_puzzle_answer()

        self.assertTrue(self.game.puzzles["laptop"]["solved"])
        self.assertTrue(self.game.tasks["upload_trojan"])

    def test_laptop_puzzle_wrong_password(self):
        """Тест: неправильный пароль компьютера"""
        self.game.current_puzzle = "laptop"
        self.game.input_text = "0000"
        self.game.puzzles["laptop"]["solved"] = False

        with patch.object(self.game, 'set_message'):
            self.game.check_puzzle_answer()

        self.assertFalse(self.game.puzzles["laptop"]["solved"])
        self.assertFalse(self.game.tasks["upload_trojan"])

    #ТЕСТЫ РОЗЕТКИ И ОТВЁРТКИ

    def test_use_screwdriver_on_outlet(self):
        """Тест: использование отвёртки на розетке"""
        self.game.inventory.append("отвертка")

        outlet_obj = {
            "name": "розетка",
            "action": "use_screwdriwer",
            "requires": "отвертка",
            "gives_item": "флешка",
            "result": "Розетка вскрыта!"
        }

        with patch.object(self.game, 'set_message'):
            self.game.interact_with_object(outlet_obj)

        self.assertNotIn("отвертка", self.game.inventory)
        self.assertIn("флешка", self.game.inventory)
        self.assertTrue(self.game.tasks["usb_logs"])

    def test_use_screwdriver_without_screwdriver(self):
        """Тест: попытка использовать розетку без отвёртки"""
        outlet_obj = {
            "name": "розетка",
            "action": "use_screwdriwer",
            "requires": "отвертка",
            "gives_item": "флешка"
        }

        with patch.object(self.game, 'set_message'):
            self.game.interact_with_object(outlet_obj)

        self.assertNotIn("флешка", self.game.inventory)

    #ТЕСТЫ КОНЕЦ ИГРЫ

    def test_win_condition(self):
        """Тест: проверка условия победы"""
        self.game.tasks["usb_logs"] = True
        self.game.tasks["crack_safe"] = True
        self.game.tasks["upload_trojan"] = True

    # Сбрасываем флаги
        self.game.won = False
        self.game.game_over = False
        self.game.game_active = True

        result = self.game.check_win()

        self.assertTrue(result)
    # Не проверяем won и game_over, так как check_win больше их не меняет
    # Эти флаги устанавливаются только через apply_win()

    def test_not_win_condition(self):
        """Тест: победа не наступает, если не все задания выполнены"""
    # Сохраняем исходные значения
        self.game.tasks["usb_logs"] = True
        self.game.tasks["crack_safe"] = False
        self.game.tasks["upload_trojan"] = False

    # Сбрасываем флаги перед тестом
        self.game.won = False
        self.game.game_over = False

        result = self.game.check_win()

        self.assertFalse(result)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.game_over)  # game_over не должен стать True

    #ТЕСТЫ ИНВЕНТАРЯ

    def test_take_item_from_room(self):
        """Тест: взятие предмета из комнаты"""
        room = self.game.rooms["hall"]
        room["items"] = ["тестовый_предмет"]

        result = self.game.take_item("тестовый_предмет")

        self.assertTrue(result)
        self.assertIn("тестовый_предмет", self.game.inventory)
        self.assertNotIn("тестовый_предмет", room["items"])

    def test_take_nonexistent_item(self):
        """Тест: попытка взять несуществующий предмет"""
        result = self.game.take_item("несуществующий_предмет")

        self.assertFalse(result)

    def test_show_inventory_empty(self):
        """Тест: отображение пустого инвентаря"""
        self.game.inventory = []

        with patch.object(self.game, 'set_message') as mock_message:
            self.game.show_inventory()
            mock_message.assert_called_with("Инвентарь пуст")

    def test_show_inventory_with_items(self):
        """Тест: отображение инвентаря с предметами"""
        self.game.inventory = ["ключ", "отвертка"]

        with patch.object(self.game, 'set_message') as mock_message:
            self.game.show_inventory()
            call_args = mock_message.call_args[0][0]
            self.assertIn("ключ", call_args)
            self.assertIn("отвертка", call_args)


class TestGameValidation(unittest.TestCase):
    """Тесты валидации - проверка корректности ввода и обработки ошибок"""

    def setUp(self):
        # Создаём моки для pygame
        self.mock_display_patcher = patch('pygame.display.set_mode')
        self.mock_display = self.mock_display_patcher.start()
        self.mock_display.return_value = MockScreen()

        self.mock_caption_patcher = patch('pygame.display.set_caption')
        self.mock_caption_patcher.start()

        self.mock_font_patcher = patch('pygame.font.Font')
        self.mock_font = self.mock_font_patcher.start()
        self.mock_font.return_value = Mock()

        self.mock_init_patcher = patch('pygame.init')
        self.mock_init_patcher.start()

        from game import GraphicalGame
        self.game = GraphicalGame()

    def tearDown(self):
        self.mock_display_patcher.stop()
        self.mock_caption_patcher.stop()
        self.mock_font_patcher.stop()
        self.mock_init_patcher.stop()

    def test_invalid_puzzle_type(self):
        """Тест: обработка несуществующего типа головоломки"""
        invalid_obj = {
            "name": "неизвестный объект",
            "action": "puzzle",
            "puzzle_type": "nonexistent"
        }

        with patch.object(self.game, 'set_message') as mock_message:
            self.game.interact_with_object(invalid_obj)
            mock_message.assert_called_with("Ошибка, неизвестная головоломка")

    def test_room_existence(self):
        """Тест: проверка существования всех комнат"""
        expected_rooms = ["hall", "office", "living"]
        for room in expected_rooms:
            self.assertIn(room, self.game.rooms)

    def test_puzzle_existence(self):
        """Тест: проверка существования всех головоломок"""
        expected_puzzles = ["safe", "laptop"]
        for puzzle in expected_puzzles:
            self.assertIn(puzzle, self.game.puzzles)

    def test_wrap_text_function(self):
        """Тест: правильный перенос длинного текста"""
        long_text = "Это очень длинный текст который должен быть разбит на несколько строк"
        wrapped = self.game.wrap_text(long_text, 20)

        self.assertGreater(len(wrapped), 1)
        for line in wrapped:
            self.assertLessEqual(len(line), 20)


class TestGameUsability(unittest.TestCase):
    """Тесты юзабилити - проверка удобства использования и логики игры"""

    def setUp(self):
        # Создаём моки для pygame
        self.mock_display_patcher = patch('pygame.display.set_mode')
        self.mock_display = self.mock_display_patcher.start()
        self.mock_display.return_value = MockScreen()

        self.mock_caption_patcher = patch('pygame.display.set_caption')
        self.mock_caption_patcher.start()

        self.mock_font_patcher = patch('pygame.font.Font')
        self.mock_font = self.mock_font_patcher.start()
        self.mock_font.return_value = Mock()

        self.mock_init_patcher = patch('pygame.init')
        self.mock_init_patcher.start()

        from game import GraphicalGame
        self.game = GraphicalGame()

        self.game.inventory = []
        self.game.tasks = {
            "usb_logs": False,
            "crack_safe": False,
            "upload_trojan": False
        }

    def tearDown(self):
        self.mock_display_patcher.stop()
        self.mock_caption_patcher.stop()
        self.mock_font_patcher.stop()
        self.mock_init_patcher.stop()

    def test_complete_game_scenario(self):
        """Тест: полный сценарий прохождения игры"""
        with patch.object(self.game, 'set_message'):
            # Шаг 1: Берём ключ из цветка
            self.game.interact_with_object({"name": "цветок", "action": "take_key", "item": "ключ"})
            self.assertIn("ключ", self.game.inventory)

            # Шаг 2: Переходим в кабинет
            self.game.interact_with_object({"name": "дверь", "action": "transition", "target": "office", "requires_key": True})
            self.assertEqual(self.game.current_room, "office")

            # Шаг 3: Взламываем сейф
            self.game.current_puzzle = "safe"
            self.game.input_text = "1234"
            self.game.check_puzzle_answer()
            self.assertTrue(self.game.tasks["crack_safe"])

            # Шаг 4: Взламываем компьютер
            self.game.current_puzzle = "laptop"
            self.game.input_text = "4321"
            self.game.check_puzzle_answer()
            self.assertTrue(self.game.tasks["upload_trojan"])

            # Шаг 5: Идём в гостиную
            self.game.interact_with_object({"name": "дверь", "action": "transition", "target": "living", "requires_key": False})
            self.assertEqual(self.game.current_room, "living")

            # Шаг 6: Берём отвёртку
            self.game.interact_with_object({"name": "тумба", "action": "take_screwdriver", "item": "отвертка"})
            self.assertIn("отвертка", self.game.inventory)

            # Шаг 7: Используем отвёртку на розетке
            self.game.interact_with_object({
                "name": "розетка",
                "action": "use_screwdriwer",
                "requires": "отвертка",
                "gives_item": "флешка"
            })
            self.assertIn("флешка", self.game.inventory)
            self.assertTrue(self.game.tasks["usb_logs"])

            # Шаг 8: Проверяем победу
            self.assertTrue(self.game.check_win())

    def test_logical_item_dependencies(self):
        """Тест: логические зависимости предметов"""
        outlet_obj = {
            "name": "розетка",
            "action": "use_screwdriwer",
            "requires": "отвертка",
            "gives_item": "флешка"
        }

        with patch.object(self.game, 'set_message'):
            # Нельзя использовать розетку без отвёртки
            self.game.interact_with_object(outlet_obj)
            self.assertNotIn("флешка", self.game.inventory)

            # Берём отвёртку
            self.game.interact_with_object({"name": "тумба", "action": "take_screwdriver", "item": "отвертка"})

            # Теперь можно использовать розетку
            self.game.interact_with_object(outlet_obj)
            self.assertIn("флешка", self.game.inventory)

    def test_door_requires_key_logic(self):
        """Тест: логика запертых дверей"""
        door_obj = {"name": "дверь", "action": "transition", "target": "office", "requires_key": True}

        with patch.object(self.game, 'set_message'):
            # Нельзя войти в кабинет без ключа
            self.game.interact_with_object(door_obj)
            self.assertNotEqual(self.game.current_room, "office")

            # Берём ключ
            self.game.interact_with_object({"name": "цветок", "action": "take_key", "item": "ключ"})

            # Теперь можно войти
            self.game.interact_with_object(door_obj)
            self.assertEqual(self.game.current_room, "office")

    def test_all_rooms_have_description(self):
        """Тест: все комнаты имеют описание"""
        for room_name, room_data in self.game.rooms.items():
            self.assertIn("desc", room_data)
            self.assertIsNotNone(room_data["desc"])
            self.assertGreater(len(room_data["desc"]), 0)

    def test_puzzle_answers_are_strings(self):
        """Тест: ответы головоломок - строки"""
        for puzzle_name, puzzle_data in self.game.puzzles.items():
            self.assertIsInstance(puzzle_data["answer"], str)
            self.assertIsInstance(puzzle_data["question"], str)

def run_all_tests():
    """Функция для запуска всех тестов"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestGameVerification))
    suite.addTests(loader.loadTestsFromTestCase(TestGameValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestGameUsability))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("="*60)
    print(f"Всего тестов: {result.testsRun}")
    print(f"Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Провалено: {len(result.failures)}")
    print(f"Ошибок: {len(result.errors)}")
    print("="*60)

    return result

if __name__ == "__main__":
    print("Запуск тестов игры 'Агент под прикрытием'")
    print("="*60)
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)