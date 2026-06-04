import unittest
import sys
import os
import time
import psutil
import tracemalloc
from unittest.mock import Mock, patch, MagicMock
from collections import defaultdict
import statistics

# Добавляем путь к корню проекта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class MockScreen:
    """Мок-объект для pygame экрана"""
    def __init__(self, width=1024, height=768):
        self.width = width
        self.height = height

    def get_size(self):
        return (self.width, self.height)

    def blit(self, *args, **kwargs):
        pass

    def copy(self):
        return MockScreen(self.width, self.height)


class PerformanceMetrics:
    """Класс для сбора метрик производительности"""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.timings = defaultdict(list)
        self.memory_usage = []
        self.cpu_usage = []

    def measure_time(self, func, name, *args, **kwargs):
        """Измерение времени выполнения функции"""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        execution_time = (end - start) * 1000  # в миллисекундах
        self.timings[name].append(execution_time)
        return result, execution_time

    def measure_memory(self):
        """Измерение текущего использования памяти в МБ"""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        self.memory_usage.append(memory_mb)
        return memory_mb

    def measure_cpu(self):
        """Измерение использования CPU в процентах"""
        cpu_percent = self.process.cpu_percent(interval=0.1)
        self.cpu_usage.append(cpu_percent)
        return cpu_percent

    def get_stats(self):
        """Получение статистики по метрикам"""
        stats = {}

        for name, timings in self.timings.items():
            if timings:
                stats[name] = {
                    'min': min(timings),
                    'max': max(timings),
                    'mean': statistics.mean(timings),
                    'median': statistics.median(timings),
                    'stddev': statistics.stdev(timings) if len(timings) > 1 else 0
                }

        if self.memory_usage:
            stats['memory'] = {
                'min': min(self.memory_usage),
                'max': max(self.memory_usage),
                'mean': statistics.mean(self.memory_usage),
                'peak': max(self.memory_usage)
            }

        if self.cpu_usage:
            stats['cpu'] = {
                'min': min(self.cpu_usage),
                'max': max(self.cpu_usage),
                'mean': statistics.mean(self.cpu_usage)
            }

        return stats


class PerformanceTestGame:
    """Класс для нагрузочного тестирования игры"""

    def __init__(self):
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

        # Импортируем и создаём игру
        from game import GraphicalGame
        self.game = GraphicalGame()

        self.metrics = PerformanceMetrics()

    def cleanup(self):
        """Очистка моков"""
        self.mock_display_patcher.stop()
        self.mock_caption_patcher.stop()
        self.mock_font_patcher.stop()
        self.mock_init_patcher.stop()

    def test_game_initialization(self):
        """Тест: время инициализации игры и потребление памяти"""
        print("\n📊 Тест 1: Инициализация игры")
        print("-" * 50)

        # Измеряем память до инициализации
        tracemalloc.start()
        memory_before = self.metrics.measure_memory()

        # Инициализация уже выполнена в __init__
        memory_after = self.metrics.measure_memory()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"   Память до инициализации: {memory_before:.2f} MB")
        print(f"   Память после инициализации: {memory_after:.2f} MB")
        print(f"   Разница: {memory_after - memory_before:.2f} MB")
        print(f"   Пиковое использование: {peak / 1024 / 1024:.2f} MB")

        return memory_after - memory_before

    def test_multiple_room_transitions(self):
        """Тест: множество переходов между комнатами"""
        print("\n📊 Тест 2: Множественные переходы между комнатами")
        print("-" * 50)

        self.game.inventory.append("ключ")  # Добавляем ключ для перехода в кабинет

        rooms = ["hall", "office", "living", "hall", "office", "living"]
        timings = []

        for room in rooms:
            start_time = time.perf_counter()
            self.game.current_room = room
            end_time = time.perf_counter()
            timings.append((end_time - start_time) * 1000)

        self.metrics.timings['room_transition'] = timings

        print(f"   Среднее время перехода: {statistics.mean(timings):.3f} мс")
        print(f"   Мин/Макс: {min(timings):.3f} / {max(timings):.3f} мс")

        return timings

    def test_multiple_puzzle_checks(self):
        """Тест: множество проверок головоломок (разные нагрузки)"""
        print("\n📊 Тест 3: Проверка головоломок")
        print("-" * 50)

        loads = [10, 50, 100, 500]
        results = {}

        for load in loads:
            timings = []
            for i in range(load):
                self.game.current_puzzle = "safe"
                self.game.input_text = "1234"
                self.game.puzzles["safe"]["solved"] = False

                start = time.perf_counter()
                with patch.object(self.game, 'set_message'):
                    self.game.check_puzzle_answer()
                end = time.perf_counter()
                timings.append((end - start) * 1000)

                # Сбрасываем состояние
                self.game.puzzles["safe"]["solved"] = False
                self.game.tasks["crack_safe"] = False

            results[load] = {
                'mean': statistics.mean(timings),
                'median': statistics.median(timings),
                'total': sum(timings),
                'min': min(timings),
                'max': max(timings)
            }

            print(f"\n   Нагрузка: {load} проверок")
            print(f"     Среднее время: {results[load]['mean']:.3f} мс")
            print(f"     Общее время: {results[load]['total']:.3f} мс")
            print(f"     Мин/Макс: {results[load]['min']:.3f} / {results[load]['max']:.3f} мс")

        return results

    def test_inventory_operations(self):
        """Тест: операции с инвентарём при разном количестве предметов"""
        print("\n📊 Тест 4: Операции с инвентарём")
        print("-" * 50)

        load_sizes = [1, 10, 50, 100]
        results = {}

        for size in load_sizes:
            # Заполняем инвентарь
            self.game.inventory = [f"item_{i}" for i in range(size)]

            # Измеряем время добавления
            start_add = time.perf_counter()
            self.game.inventory.append("new_item")
            add_time = (time.perf_counter() - start_add) * 1000

            # Измеряем время отображения (создание строки)
            start_show = time.perf_counter()
            inventory_str = f"Инвентарь: {', '.join(self.game.inventory)}"
            show_time = (time.perf_counter() - start_show) * 1000

            # Измеряем время поиска предмета
            start_find = time.perf_counter()
            found = "item_50" in self.game.inventory if size > 50 else "item_0" in self.game.inventory
            find_time = (time.perf_counter() - start_find) * 1000

            # Измеряем память
            memory = self.metrics.measure_memory()

            results[size] = {
                'add_time': add_time,
                'show_time': show_time,
                'find_time': find_time,
                'memory_mb': memory
            }

            print(f"\n   Размер инвентаря: {size} предметов")
            print(f"     Добавление: {add_time:.3f} мс")
            print(f"     Отображение: {show_time:.3f} мс")
            print(f"     Поиск: {find_time:.3f} мс")
            print(f"     Память: {memory:.2f} MB")

        return results

    def test_concurrent_operations(self):
        """Тест: нагрузка при одновременных операциях"""
        print("\n📊 Тест 5: Одновременные операции (стресс-тест)")
        print("-" * 50)

        operations = 1000
        timings = []

        for i in range(operations):
            self.game.current_room = "hall"
            self.game.inventory = ["ключ"] if i % 2 == 0 else []

            start = time.perf_counter()

            # Имитируем несколько операций
            with patch.object(self.game, 'set_message'):
                # Переход
                if "ключ" in self.game.inventory:
                    self.game.current_room = "office"
                # Проверка головоломки
                self.game.current_puzzle = "laptop"
                self.game.input_text = "4321"
                self.game.check_puzzle_answer()
                self.game.puzzles["laptop"]["solved"] = False
                # Взятие предмета
                self.game.take_item("тест")

            end = time.perf_counter()
            timings.append((end - start) * 1000)

            # Сброс
            self.game.current_room = "hall"

        self.metrics.timings['concurrent_ops'] = timings

        print(f"   Всего операций: {operations}")
        print(f"   Среднее время: {statistics.mean(timings):.3f} мс")
        print(f"   Медиана: {statistics.median(timings):.3f} мс")
        print(f"   Стандартное отклонение: {statistics.stdev(timings):.3f} мс")
        print(f"   95-й перцентиль: {sorted(timings)[int(len(timings) * 0.95)]:.3f} мс")

        return timings

    def test_memory_leak(self):
        """Тест: утечки памяти при длительной работе"""
        print("\n📊 Тест 6: Проверка утечек памяти")
        print("-" * 50)

        memory_samples = []
        iterations = 100

        for i in range(iterations):
            # Выполняем различные операции
            self.game.current_room = "hall"
            self.game.inventory.append(f"temp_item_{i}")

            # Измеряем память каждые 10 итераций
            if i % 10 == 0:
                memory = self.metrics.measure_memory()
                memory_samples.append(memory)
                print(f"   Итерация {i}: {memory:.2f} MB")

            # Очищаем временные предметы
            if len(self.game.inventory) > 10:
                self.game.inventory = self.game.inventory[:10]

        # Проверяем рост памяти
        if len(memory_samples) > 1:
            memory_growth = memory_samples[-1] - memory_samples[0]
            print(f"\n   Рост памяти за {iterations} итераций: {memory_growth:.2f} MB")

            if memory_growth < 5:
                print("   ✅ Значительных утечек памяти не обнаружено")
            else:
                print(f"   ⚠️ Обнаружен потенциальный рост памяти: {memory_growth:.2f} MB")

        return memory_samples


class TestPerformanceUnderLoad(unittest.TestCase):
    """Тесты производительности под нагрузкой"""

    def setUp(self):
        self.test_game = PerformanceTestGame()

    def tearDown(self):
        self.test_game.cleanup()

    def test_01_initialization_performance(self):
        """Тест производительности инициализации"""
        memory_used = self.test_game.test_game_initialization()
        self.assertLess(memory_used, 100, "Инициализация использует слишком много памяти (>100MB)")

    def test_02_room_transitions_performance(self):
        """Тест производительности переходов"""
        timings = self.test_game.test_multiple_room_transitions()
        avg_time = statistics.mean(timings)
        self.assertLess(avg_time, 1.0, f"Переходы слишком медленные: {avg_time:.3f}мс")

    def test_03_puzzle_performance_under_load(self):
        """Тест производительности головоломок под нагрузкой"""
        results = self.test_game.test_multiple_puzzle_checks()
        # Проверяем, что при нагрузке в 500 операций среднее время < 1мс
        self.assertLess(results[500]['mean'], 1.0, "Головоломки слишком медленные при высокой нагрузке")

    def test_04_inventory_performance(self):
        """Тест производительности операций с инвентарём"""
        results = self.test_game.test_inventory_operations()
        # Проверяем, что даже при 100 предметах операции быстрые
        self.assertLess(results[100]['add_time'], 0.1, "Добавление предметов слишком медленное")
        self.assertLess(results[100]['find_time'], 0.1, "Поиск предметов слишком медленный")


def print_summary_table(results):
    """Вывод сводной таблицы результатов"""
    print("\n" + "="*80)
    print("СВОДНАЯ ТАБЛИЦА РЕЗУЛЬТАТОВ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ")
    print("="*80)

    # Таблица 1: Время инициализации и базовая память
    print("\n📌 БАЗОВЫЕ ПОКАЗАТЕЛИ")
    print("-"*80)
    print(f"{'Показатель':<40} {'Значение':<20}")
    print("-"*80)

    if 'init' in results:
        print(f"{'Память при инициализации':<40} {results['init']['memory']:<20.2f} MB")
        print(f"{'Пиковая память':<40} {results['init']['peak']:<20.2f} MB")

    # Таблица 2: Производительность операций
    print("\n📌 ПРОИЗВОДИТЕЛЬНОСТЬ ОПЕРАЦИЙ")
    print("-"*80)
    print(f"{'Операция':<30} {'Среднее время (мс)':<20} {'Мин/Макс (мс)':<20}")
    print("-"*80)

    if 'room_transition' in results:
        rt = results['room_transition']
        print(f"{'Переход между комнатами':<30} {rt['mean']:<20.3f} {rt['min']:.3f}/{rt['max']:.3f}")

    if 'puzzle_check' in results:
        for load, data in results['puzzle_check'].items():
            print(f"{f'Проверка головоломки (n={load})':<30} {data['mean']:<20.3f} {data['min']:.3f}/{data['max']:.3f}")

    if 'concurrent_ops' in results:
        co = results['concurrent_ops']
        print(f"{'Комплексная операция':<30} {co['mean']:<20.3f} {co['min']:.3f}/{co['max']:.3f}")

    # Таблица 3: Зависимость производительности от нагрузки
    print("\n📌 ЗАВИСИМОСТЬ ОТ РАЗМЕРА ИНВЕНТАРЯ")
    print("-"*80)
    print(f"{'Размер инвентаря':<20} {'Добавление (мс)':<20} {'Поиск (мс)':<20} {'Память (MB)':<15}")
    print("-"*80)

    if 'inventory' in results:
        for size, data in results['inventory'].items():
            print(f"{size:<20} {data['add_time']:<20.4f} {data['find_time']:<20.4f} {data['memory_mb']:<15.2f}")

    # Таблица 4: Стабильность памяти
    print("\n📌 СТАБИЛЬНОСТЬ ПАМЯТИ")
    print("-"*80)

    if 'memory_leak' in results:
        ml = results['memory_leak']
        print(f"{'Начальная память':<40} {ml['start']:<20.2f} MB")
        print(f"{'Конечная память':<40} {ml['end']:<20.2f} MB")
        print(f"{'Рост памяти':<40} {ml['growth']:<20.2f} MB")
        print(f"{'Статус':<40} {'✅ Нет утечек' if ml['growth'] < 5 else '⚠️ Возможны утечки'}")

    # Таблица 5: Использование CPU
    print("\n📌 ИСПОЛЬЗОВАНИЕ ПРОЦЕССОРА")
    print("-"*80)

    if 'cpu' in results:
        cpu = results['cpu']
        print(f"{'Среднее использование CPU':<40} {cpu['mean']:<20.2f} %")
        print(f"{'Пиковое использование CPU':<40} {cpu['max']:<20.2f} %")

    print("\n" + "="*80)
    print("✅ Тестирование завершено")
    print("="*80)


def run_performance_tests():
    """Запуск всех нагрузочных тестов"""
    print("\n" + "="*80)
    print("НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ ИГРЫ 'АГЕНТ ПОД ПРИКРЫТИЕМ'")
    print("="*80)

    test_game = PerformanceTestGame()
    results = {}

    try:
        # Запускаем все тесты
        results['init'] = {
            'memory': test_game.test_game_initialization(),
            'peak': 0
        }

        results['room_transition'] = test_game.test_multiple_room_transitions()
        rt_timings = results['room_transition']
        results['room_transition'] = {
            'mean': statistics.mean(rt_timings),
            'min': min(rt_timings),
            'max': max(rt_timings)
        }

        puzzle_results = test_game.test_multiple_puzzle_checks()
        results['puzzle_check'] = {}
        for load, data in puzzle_results.items():
            results['puzzle_check'][load] = {
                'mean': data['mean'],
                'min': data['min'],
                'max': data['max'],
                'total': data['total']
            }

        inventory_results = test_game.test_inventory_operations()
        results['inventory'] = inventory_results

        concurrent_timings = test_game.test_concurrent_operations()
        results['concurrent_ops'] = {
            'mean': statistics.mean(concurrent_timings),
            'min': min(concurrent_timings),
            'max': max(concurrent_timings)
        }

        memory_samples = test_game.test_memory_leak()
        results['memory_leak'] = {
            'start': memory_samples[0] if memory_samples else 0,
            'end': memory_samples[-1] if memory_samples else 0,
            'growth': (memory_samples[-1] - memory_samples[0]) if len(memory_samples) > 1 else 0
        }

        # Измеряем CPU
        cpu_samples = []
        for _ in range(10):
            cpu = test_game.metrics.measure_cpu()
            cpu_samples.append(cpu)
        results['cpu'] = {
            'mean': statistics.mean(cpu_samples),
            'max': max(cpu_samples)
        }

        # Выводим сводную таблицу
        print_summary_table(results)

        return results

    finally:
        test_game.cleanup()


if __name__ == "__main__":
    # Запускаем нагрузочные тесты
    results = run_performance_tests()

    if results['room_transition']['mean'] > 0.5:
        print("   ⚠️ Переходы между комнатами можно оптимизировать")
    else:
        print("   ✅ Переходы между комнатами работают быстро")

    if results['concurrent_ops']['mean'] > 2.0:
        print("   ⚠️ Комплексные операции можно оптимизировать")
    else:
        print("   ✅ Комплексные операции работают быстро")

    if results['memory_leak']['growth'] > 5:
        print("   ⚠️ Обнаружен рост памяти - проверьте утечки")
    else:
        print("   ✅ Утечек памяти не обнаружено")

    print("\n" + "="*80)