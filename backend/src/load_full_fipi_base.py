#!/usr/bin/env python3
"""
Загрузка полной базы заданий в стиле ФИПИ
Все предметы, все уровни, реалистичные задания
"""
import asyncio
import sys
import os

sys.path.insert(0, '/app')

import asyncpg

# Полная база заданий в стиле ФИПИ
# Структурирована по предметам, номерам заданий, темам

TASKS = []

# ═══════════════════════════════════════════════════════════
# МАТЕМАТИКА (ПРОФИЛЬ) - ЕГЭ
# ═══════════════════════════════════════════════════════════

# Задание 1 - Практические задачи
TASKS.extend([
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Практические задачи', 'subtopic': 'Проценты',
     'condition': 'Цена товара снизилась на 20%, а затем ещё на 15%. На сколько процентов снизилась цена товара от первоначальной?',
     'solution': 'Пусть начальная цена 100. После первого снижения: 100 × 0.8 = 80. После второго: 80 × 0.85 = 68. Снижение: 100 - 68 = 32%.',
     'answer': '32'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Практические задачи', 'subtopic': 'Оптимизация',
     'condition': 'Для строительства гаража можно использовать один из двух типов фундамента: бетонный или пеноблочный. Для бетонного фундамента необходимо 3 тонны бетона и 5 мешков цемента. Для пеноблочного — 2 тонны пеноблоков и 7 мешков цемента. Тонна бетона стоит 2500 рублей, тонна пеноблоков — 3000 рублей, мешок цемента — 400 рублей. Найдите стоимость более дешёвого фундамента.',
     'solution': 'Бетонный: 3×2500 + 5×400 = 7500 + 2000 = 9500 руб. Пеноблочный: 2×3000 + 7×400 = 6000 + 2800 = 8800 руб. Дешевле пеноблочный.',
     'answer': '8800'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Практические задачи', 'subtopic': 'Скорость и время',
     'condition': 'Поезд, двигаясь равномерно со скоростью 80 км/ч, проезжает мимо придорожного столба за 36 секунд. Найдите длину поезда в метрах.',
     'solution': '36 секунд = 0.01 часа. Длина = скорость × время = 80 × 0.01 = 0.8 км = 800 м.',
     'answer': '800'},
])

# Задание 5 - Уравнения
TASKS.extend([
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 5, 'difficulty': 'base',
     'topic': 'Уравнения', 'subtopic': 'Тригонометрические',
     'condition': 'Решите уравнение cos(x) = -1/2. В ответе запишите наибольший отрицательный корень.',
     'solution': 'cos(x) = -1/2 → x = ±2π/3 + 2πn. Наибольший отрицательный: x = -2π/3.',
     'answer': '-2π/3'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 5, 'difficulty': 'base',
     'topic': 'Уравнения', 'subtopic': 'Иррациональные',
     'condition': 'Решите уравнение √(3x - 2) = x - 2.',
     'solution': 'Возводим в квадрат: 3x - 2 = x² - 4x + 4. x² - 7x + 6 = 0. x = 1 или x = 6. Проверка: x=1 не подходит (√1 = -1 — неверно), x=6 подходит (√16 = 4 ✓).',
     'answer': '6'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 5, 'difficulty': 'base',
     'topic': 'Уравнения', 'subtopic': 'Показательные',
     'condition': 'Решите уравнение 5^(x-7) = 1/25.',
     'solution': '1/25 = 5^(-2). Получаем: x - 7 = -2, x = 5.',
     'answer': '5'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 5, 'difficulty': 'base',
     'topic': 'Уравнения', 'subtopic': 'Логарифмические',
     'condition': 'Решите уравнение log₅(2x - 3) = 2.',
     'solution': 'По определению: 2x - 3 = 5² = 25. 2x = 28, x = 14.',
     'answer': '14'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 5, 'difficulty': 'base',
     'topic': 'Уравнения', 'subtopic': 'Комбинированные',
     'condition': 'Решите уравнение (x-3)² = x-3.',
     'solution': '(x-3)² - (x-3) = 0. (x-3)(x-3-1) = 0. (x-3)(x-4) = 0. x = 3 или x = 4.',
     'answer': '3;4'},
])

# Задание 6 - Стереометрия
TASKS.extend([
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 6, 'difficulty': 'base',
     'topic': 'Стереометрия', 'subtopic': 'Объёмы',
     'condition': 'Объём куба равен 27. Найдите объём треугольной пирамиды, вершинами которой являются вершины A, B, C и D₁ этого куба.',
     'solution': 'Объём такой пирамиды = 1/6 объёма куба = 27/6 = 4.5.',
     'answer': '4.5'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 6, 'difficulty': 'base',
     'topic': 'Стереометрия', 'subtopic': 'Площади поверхности',
     'condition': 'Найдите площадь поверхности прямоугольного параллелепипеда с рёбрами 2, 3 и 4.',
     'solution': 'S = 2(ab + bc + ac) = 2(2×3 + 3×4 + 2×4) = 2(6 + 12 + 8) = 52.',
     'answer': '52'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 6, 'difficulty': 'base',
     'topic': 'Стереометрия', 'subtopic': 'Цилиндр',
     'condition': 'Объём цилиндра равен 12π. Радиус основания увеличили в 2 раза, а высоту уменьшили в 3 раза. Найдите объём нового цилиндра.',
     'solution': 'V = πr²h. Новый: V\' = π(2r)²(h/3) = π·4r²·h/3 = 4/3 · πr²h = 4/3 · 12π = 16π.',
     'answer': '16π'},
])

# Задание 9 - Теория вероятностей
TASKS.extend([
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 9, 'difficulty': 'base',
     'topic': 'Теория вероятностей', 'subtopic': 'Классическая',
     'condition': 'В случайном эксперименте бросают две игральные кости. Найдите вероятность того, что сумма выпавших очков равна 8.',
     'solution': 'Всего исходов: 36. Сумма 8: (2,6), (3,5), (4,4), (5,3), (6,2) — 5 исходов. P = 5/36 ≈ 0.14.',
     'answer': '5/36'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 9, 'difficulty': 'base',
     'topic': 'Теория вероятностей', 'subtopic': 'Условная',
     'condition': 'Вероятность того, что новая батарейка бракованная, равна 0.05. Покупатель выбирает одну батарейку. Найдите вероятность того, что она исправна.',
     'solution': 'P(исправна) = 1 - P(бракованная) = 1 - 0.05 = 0.95.',
     'answer': '0.95'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 9, 'difficulty': 'base',
     'topic': 'Теория вероятностей', 'subtopic': 'Комбинаторика',
     'condition': 'Из 10 учащихся выбирают 3 для участия в олимпиаде. Сколькими способами это можно сделать?',
     'solution': 'C(10,3) = 10!/(3!·7!) = (10·9·8)/(3·2·1) = 120.',
     'answer': '120'},
])

# Задание 11 - Производные
TASKS.extend([
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 11, 'difficulty': 'profile',
     'topic': 'Производные', 'subtopic': 'Нахождение производной',
     'condition': 'Найдите производную функции f(x) = 3x⁴ - 2x³ + 5x - 7 в точке x = 1.',
     'solution': 'f\'(x) = 12x³ - 6x² + 5. f\'(1) = 12 - 6 + 5 = 11.',
     'answer': '11'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 11, 'difficulty': 'profile',
     'topic': 'Производные', 'subtopic': 'Экстремумы',
     'condition': 'Найдите точку максимума функции y = x³ - 3x² - 9x + 5.',
     'solution': 'y\' = 3x² - 6x - 9 = 3(x² - 2x - 3) = 3(x-3)(x+1). Критические точки: x = -1, x = 3. При x = -1 производная меняет знак с + на - → максимум.',
     'answer': '-1'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 11, 'difficulty': 'profile',
     'topic': 'Производные', 'subtopic': 'Наибольшее/наименьшее значение',
     'condition': 'Найдите наибольшее значение функции y = x³ - 6x² + 9x + 2 на отрезке [0; 4].',
     'solution': 'y\' = 3x² - 12x + 9 = 3(x-1)(x-3). Критические точки: x = 1, x = 3. Значения: y(0) = 2, y(1) = 6, y(3) = 2, y(4) = 6. Наибольшее: 6.',
     'answer': '6'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 11, 'difficulty': 'profile',
     'topic': 'Производные', 'subtopic': 'Касательная',
     'condition': 'К графику функции f(x) = x² проведена касательная в точке x₀ = 3. Найдите угловой коэффициент этой касательной.',
     'solution': 'Угловой коэффициент = f\'(x₀). f\'(x) = 2x. f\'(3) = 6.',
     'answer': '6'},
])

# Задание 12 - Текстовые задачи
TASKS.extend([
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 12, 'difficulty': 'profile',
     'topic': 'Текстовые задачи', 'subtopic': 'Движение',
     'condition': 'Из пункта A в пункт B одновременно выехали два автомобиля. Первый ехал со скоростью 60 км/ч, второй — 50 км/ч. Первый,到达 B, сразу вернулся и встретил второй в 40 км от B. Найдите расстояние AB.',
     'solution': 'Пусть AB = S. Время до встречи одинаковое. Первый проехал S + 40, второй — S - 40. (S+40)/60 = (S-40)/50. 50S + 2000 = 60S - 2400. 10S = 4400. S = 440.',
     'answer': '440'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 12, 'difficulty': 'profile',
     'topic': 'Текстовые задачи', 'subtopic': 'Работа',
     'condition': 'Первая труба пропускает на 4 литра воды в минуту меньше, чем вторая. Сколько литров в минуту пропускает вторая труба, если резервуар объёмом 120 литров она заполняет на 4 минуты быстрее?',
     'solution': 'Пусть вторая пропускает x л/мин, первая — x-4. 120/(x-4) - 120/x = 4. 120x - 120(x-4) = 4x(x-4). 480 = 4x² - 16x. x² - 4x - 120 = 0. x = 12 (x = -10 не подходит).',
     'answer': '12'},
    {'subject_code': 'math-profile', 'year': 2024, 'task_number': 12, 'difficulty': 'profile',
     'topic': 'Текстовые задачи', 'subtopic': 'Смеси',
     'condition': 'Имеется 30%-ный раствор соли массой 200 г и 10%-ный раствор соли массой 300 г. Найдите концентрацию соли в полученном растворе.',
     'solution': 'Соли в первом: 200 × 0.3 = 60 г. Во втором: 300 × 0.1 = 30 г. Всего соли: 90 г. Всего раствора: 500 г. Концентрация: 90/500 = 0.18 = 18%.',
     'answer': '18'},
])

# ═══════════════════════════════════════════════════════════
# МАТЕМАТИКА (БАЗА) - ОГЭ
# ═══════════════════════════════════════════════════════════

TASKS.extend([
    {'subject_code': 'math-base', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Вычисления', 'subtopic': 'Дроби',
     'condition': 'Найдите значение выражения: 3/4 + 5/6.',
     'solution': 'Приводим к общему знаменателю 12: 9/12 + 10/12 = 19/12.',
     'answer': '19/12'},
    {'subject_code': 'math-base', 'year': 2024, 'task_number': 5, 'difficulty': 'base',
     'topic': 'Функции', 'subtopic': 'Графики',
     'condition': 'На рисунке изображён график функции y = f(x). Определите, на каком промежутке функция убывает.',
     'solution': 'Функция убывает там, где её значения уменьшаются при увеличении x. По графику: от -2 до 1.',
     'answer': '[-2; 1]'},
    {'subject_code': 'math-base', 'year': 2024, 'task_number': 8, 'difficulty': 'base',
     'topic': 'Геометрия', 'subtopic': 'Треугольники',
     'condition': 'В треугольнике ABC угол C равен 90°, AC = 4, BC = 3. Найдите sin(A).',
     'solution': 'AB = √(AC² + BC²) = √(16+9) = 5. sin(A) = BC/AB = 3/5 = 0.6.',
     'answer': '0.6'},
    {'subject_code': 'math-base', 'year': 2024, 'task_number': 14, 'difficulty': 'base',
     'topic': 'Неравенства', 'subtopic': 'Квадратные',
     'condition': 'Решите неравенство x² - 4x - 5 > 0.',
     'solution': 'Корни: x = -1, x = 5. По методу интервалов: x ∈ (-∞; -1) ∪ (5; +∞).',
     'answer': '(-∞; -1) ∪ (5; +∞)'},
])

# ═══════════════════════════════════════════════════════════
# РУССКИЙ ЯЗЫК
# ═══════════════════════════════════════════════════════════

TASKS.extend([
    {'subject_code': 'russian', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Средства связи', 'subtopic': 'Анализ текста',
     'condition': 'Укажите предложения, в которых средством связи является личное местоимение. Запишите их номера.',
     'solution': 'Личные местоимения (он, она, оно, они, я, ты, мы, вы) заменяют существительное и связывают предложения.',
     'answer': '2, 4'},
    {'subject_code': 'russian', 'year': 2024, 'task_number': 4, 'difficulty': 'base',
     'topic': 'Орфоэпия', 'subtopic': 'Ударения',
     'condition': 'Установите соответствие: в каком слове ударение падает на второй слог? 1) звонИт 2) тОрты 3) бАнты 4) красивЕе',
     'solution': 'звонИт — ударение на 2-й слог. Остальные: тОрты (1-й), бАнты (1-й), красивЕе (3-й).',
     'answer': '1'},
    {'subject_code': 'russian', 'year': 2024, 'task_number': 5, 'difficulty': 'base',
     'topic': 'Лексика', 'subtopic': 'Паронимы',
     'condition': 'В каком предложении вместо слова ЭФФЕКТНЫЙ нужно употребить ЭФФЕКТНЫЙ? 1) Эффектный поступок 2) Эффектный внешний вид 3) Эффектный результат',
     'solution': 'Эффектный — производящий впечатление (о внешности). Эффектный — дающий эффект (о результате). В предложении 3 нужно "эффективный".',
     'answer': '1'},
    {'subject_code': 'russian', 'year': 2024, 'task_number': 6, 'difficulty': 'base',
     'topic': 'Морфология', 'subtopic': 'Формы слов',
     'condition': 'Укажите предложение с грамматической ошибкой: 1) скучаю по другу 2) нет мест 3) более лучший 4) обе девушки',
     'solution': '"Более лучший" — ошибка, т.к. "лучший" уже сравнительная степень. Правильно: "лучше" или "более хороший".',
     'answer': '3'},
    {'subject_code': 'russian', 'year': 2024, 'task_number': 7, 'difficulty': 'base',
     'topic': 'Синтаксис', 'subtopic': 'Пунктуация',
     'condition': 'Расставьте знаки препинания: "Когда мы вошли в комнату там уже сидели гости."',
     'solution': 'Придаточное предложение "Когда мы вошли в комнату" отделяется запятой: "Когда мы вошли в комнату, там уже сидели гости."',
     'answer': 'запятая после "комнату"'},
])

# ═══════════════════════════════════════════════════════════
# ФИЗИКА
# ═══════════════════════════════════════════════════════════

TASKS.extend([
    {'subject_code': 'physics', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Механика', 'subtopic': 'Кинематика',
     'condition': 'Тело движется по закону x(t) = 2t² + 3t. Найдите скорость тела в момент t = 2 с.',
     'solution': 'v(t) = x\'(t) = 4t + 3. v(2) = 4·2 + 3 = 11 м/с.',
     'answer': '11'},
    {'subject_code': 'physics', 'year': 2024, 'task_number': 2, 'difficulty': 'base',
     'topic': 'Механика', 'subtopic': 'Динамика',
     'condition': 'Тело массой 5 кг движется с ускорением 2 м/с². Найдите силу, действующую на тело.',
     'solution': 'По второму закону Ньютона: F = ma = 5 · 2 = 10 Н.',
     'answer': '10'},
    {'subject_code': 'physics', 'year': 2024, 'task_number': 3, 'difficulty': 'base',
     'topic': 'Молекулярная физика', 'subtopic': 'Термодинамика',
     'condition': 'Идеальный газ получил количество теплоты 500 Дж и совершил работу 200 Дж. Найдите изменение внутренней энергии газа.',
     'solution': 'По первому закону термодинамики: ΔU = Q - A = 500 - 200 = 300 Дж.',
     'answer': '300'},
    {'subject_code': 'physics', 'year': 2024, 'task_number': 4, 'difficulty': 'base',
     'topic': 'Электродинамика', 'subtopic': 'Закон Ома',
     'condition': 'Напряжение на концах проводника 12 В, сопротивление 4 Ом. Найдите силу тока.',
     'solution': 'По закону Ома: I = U/R = 12/4 = 3 А.',
     'answer': '3'},
    {'subject_code': 'physics', 'year': 2024, 'task_number': 5, 'difficulty': 'base',
     'topic': 'Оптика', 'subtopic': 'Линзы',
     'condition': 'Оптическая сила линзы 5 дптр. Найдите её фокусное расстояние.',
     'solution': 'D = 1/F. F = 1/D = 1/5 = 0.2 м = 20 см.',
     'answer': '20'},
])

# ═══════════════════════════════════════════════════════════
# ХИМИЯ
# ═══════════════════════════════════════════════════════════

TASKS.extend([
    {'subject_code': 'chemistry', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Строение атома', 'subtopic': 'Электронная конфигурация',
     'condition': 'Определите элемент с электронной конфигурацией 1s² 2s² 2p⁶ 3s² 3p⁵.',
     'solution': 'Сумма электронов: 2+2+6+2+5 = 17. Элемент с номером 17 — хлор (Cl).',
     'answer': 'Хлор'},
    {'subject_code': 'chemistry', 'year': 2024, 'task_number': 2, 'difficulty': 'base',
     'topic': 'Периодический закон', 'subtopic': 'Свойства элементов',
     'condition': 'Как изменяется электроотрицательность в периоде слева направо?',
     'solution': 'В периоде слева направо электроотрицательность увеличивается.',
     'answer': 'увеличивается'},
    {'subject_code': 'chemistry', 'year': 2024, 'task_number': 3, 'difficulty': 'base',
     'topic': 'Химическая связь', 'subtopic': 'Типы связей',
     'condition': 'Какой тип связи в молекуле NaCl?',
     'solution': 'NaCl — соединение металла (Na) и неметалла (Cl) с большой разницей электроотрицательностей. Связь ионная.',
     'answer': 'ионная'},
    {'subject_code': 'chemistry', 'year': 2024, 'task_number': 4, 'difficulty': 'base',
     'topic': 'Реакции', 'subtopic': 'Уравнения',
     'condition': 'Расставьте коэффициенты в уравнении: Al + O₂ → Al₂O₃',
     'solution': '4Al + 3O₂ → 2Al₂O₃',
     'answer': '4, 3, 2'},
])

# ═══════════════════════════════════════════════════════════
# БИОЛОГИЯ
# ═══════════════════════════════════════════════════════════

TASKS.extend([
    {'subject_code': 'biology', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Биология как наука', 'subtopic': 'Методы',
     'condition': 'Какой метод используется для изучения хромосомного набора клетки?',
     'solution': 'Для изучения хромосомного набора используется цитогенетический метод.',
     'answer': 'цитогенетический'},
    {'subject_code': 'biology', 'year': 2024, 'task_number': 2, 'difficulty': 'base',
     'topic': 'Клетка', 'subtopic': 'Органоиды',
     'condition': 'Какой органоид отвечает за фотосинтез в растительной клетке?',
     'solution': 'Фотосинтез происходит в хлоропластах.',
     'answer': 'хлоропласты'},
    {'subject_code': 'biology', 'year': 2024, 'task_number': 3, 'difficulty': 'base',
     'topic': 'Генетика', 'subtopic': 'Законы Менделя',
     'condition': 'При скрещивании гетерозиготных организмов Aa × Aa, какова вероятность появления потомка с генотипом aa?',
     'solution': 'По закону расщепления: AA:Aa:aa = 1:2:1. Вероятность aa = 1/4 = 25%.',
     'answer': '25%'},
    {'subject_code': 'biology', 'year': 2024, 'task_number': 4, 'difficulty': 'base',
     'topic': 'Эволюция', 'subtopic': 'Движущие силы',
     'condition': 'Назовите элементарную единицу эволюции.',
     'solution': 'Элементарная единица эволюции — популяция.',
     'answer': 'популяция'},
])

# ═══════════════════════════════════════════════════════════
# ИСТОРИЯ
# ═══════════════════════════════════════════════════════════

TASKS.extend([
    {'subject_code': 'history', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Древняя Русь', 'subtopic': 'Ключевые даты',
     'condition': 'В каком году произошло Крещение Руси?',
     'solution': 'Крещение Руси произошло в 988 году при князе Владимире Святославиче.',
     'answer': '988'},
    {'subject_code': 'history', 'year': 2024, 'task_number': 2, 'difficulty': 'base',
     'topic': 'Средневековая Русь', 'subtopic': 'Правители',
     'condition': 'Кто из князей присоединил Новгород к Москве в 1478 году?',
     'solution': 'Новгород был присоединён Иваном III Васильевичем.',
     'answer': 'Иван III'},
    {'subject_code': 'history', 'year': 2024, 'task_number': 3, 'difficulty': 'base',
     'topic': 'Новое время', 'subtopic': 'Реформы',
     'condition': 'В каком году была отменена крепостное право в России?',
     'solution': 'Крепостное право отменено 19 февраля 1861 года манифестом Александра II.',
     'answer': '1861'},
    {'subject_code': 'history', 'year': 2024, 'task_number': 4, 'difficulty': 'base',
     'topic': 'Новейшее время', 'subtopic': 'СССР',
     'condition': 'В каком году образовался СССР?',
     'solution': 'СССР образован 30 декабря 1922 года.',
     'answer': '1922'},
])

# ═══════════════════════════════════════════════════════════
# ОБЩЕСТВОЗНАНИЕ
# ═══════════════════════════════════════════════════════════

TASKS.extend([
    {'subject_code': 'social-studies', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Человек и общество', 'subtopic': 'Понятие общества',
     'condition': 'Что из перечисленного относится к признакам общества как системы?',
     'solution': 'Признаки: наличие элементов, связей между ними, целостность, динамичность, самоорганизация.',
     'answer': 'целостность, динамичность, самоорганизация'},
    {'subject_code': 'social-studies', 'year': 2024, 'task_number': 2, 'difficulty': 'base',
     'topic': 'Экономика', 'subtopic': 'Рынок',
     'condition': 'Какие функции выполняет цена в рыночной экономике?',
     'solution': 'Функции цены: учёт затрат, распределение ресурсов, стимулирование, сбалансирование спроса и предложения.',
     'answer': 'распределение, стимулирование, балансирование'},
    {'subject_code': 'social-studies', 'year': 2024, 'task_number': 3, 'difficulty': 'base',
     'topic': 'Политика', 'subtopic': 'Государство',
     'condition': 'Назовите признаки государства.',
     'solution': 'Признаки: территория, население, публичная власть, суверенитет, правовая система, налоги.',
     'answer': 'территория, население, суверенитет'},
    {'subject_code': 'social-studies', 'year': 2024, 'task_number': 4, 'difficulty': 'base',
     'topic': 'Право', 'subtopic': 'Конституция',
     'condition': 'Сколько глав в Конституции РФ?',
     'solution': 'Конституция РФ состоит из преамбулы и 9 глав.',
     'answer': '9'},
])

# ═══════════════════════════════════════════════════════════
# ИНФОРМАТИКА
# ═══════════════════════════════════════════════════════════

TASKS.extend([
    {'subject_code': 'informatics', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Информация', 'subtopic': 'Кодирование',
     'condition': 'Сколько бит в 5 байтах?',
     'solution': '1 байт = 8 бит. 5 байт = 5 × 8 = 40 бит.',
     'answer': '40'},
    {'subject_code': 'informatics', 'year': 2024, 'task_number': 2, 'difficulty': 'base',
     'topic': 'Системы счисления', 'subtopic': 'Перевод',
     'condition': 'Переведите число 1011₂ в десятичную систему.',
     'solution': '1011₂ = 1·2³ + 0·2² + 1·2¹ + 1·2⁰ = 8 + 0 + 2 + 1 = 11.',
     'answer': '11'},
    {'subject_code': 'informatics', 'year': 2024, 'task_number': 3, 'difficulty': 'base',
     'topic': 'Логика', 'subtopic': 'Высказывания',
     'condition': 'Чему равно значение логического выражения: (1 И 0) ИЛИ 1?',
     'solution': '(1 И 0) = 0. 0 ИЛИ 1 = 1.',
     'answer': '1'},
    {'subject_code': 'informatics', 'year': 2024, 'task_number': 4, 'difficulty': 'base',
     'topic': 'Алгоритмы', 'subtopic': 'Блок-схемы',
     'condition': 'Какое значение будет у переменной S после выполнения: S = 0; for i in 1..5: S = S + i',
     'solution': 'S = 1 + 2 + 3 + 4 + 5 = 15.',
     'answer': '15'},
])

# ═══════════════════════════════════════════════════════════
# ГЕОГРАФИЯ
# ═══════════════════════════════════════════════════════════

TASKS.extend([
    {'subject_code': 'geography', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Источники информации', 'subtopic': 'Карты',
     'condition': 'Определите по карте расстояние от Москвы до Санкт-Петербурга.',
     'solution': 'Расстояние по прямой: около 635 км.',
     'answer': '635'},
    {'subject_code': 'geography', 'year': 2024, 'task_number': 2, 'difficulty': 'base',
     'topic': 'Природа', 'subtopic': 'Климат',
     'condition': 'Какой климатический пояс занимает большая часть России?',
     'solution': 'Большая часть России находится в умеренном климатическом поясе.',
     'answer': 'умеренный'},
    {'subject_code': 'geography', 'year': 2024, 'task_number': 3, 'difficulty': 'base',
     'topic': 'Население', 'subtopic': 'Демография',
     'condition': 'Какой город России является самым населённым?',
     'solution': 'Самый населённый город России — Москва (около 13 млн человек).',
     'answer': 'Москва'},
])

# ═══════════════════════════════════════════════════════════
# ЛИТЕРАТУРА
# ═══════════════════════════════════════════════════════════

TASKS.extend([
    {'subject_code': 'literature', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Литературные роды', 'subtopic': 'Эпос',
     'condition': 'К какому литературному роду относится роман?',
     'solution': 'Роман относится к эпосу (эпическому роду).',
     'answer': 'эпос'},
    {'subject_code': 'literature', 'year': 2024, 'task_number': 2, 'difficulty': 'base',
     'topic': 'Литературные направления', 'subtopic': 'Реализм',
     'condition': 'Кто из писателей является представителем реализма?',
     'solution': 'Представители реализма: Л. Толстой, Ф. Достоевский, И. Тургенев, А. Чехов.',
     'answer': 'Л. Толстой'},
    {'subject_code': 'literature', 'year': 2024, 'task_number': 3, 'difficulty': 'base',
     'topic': 'Золотой век', 'subtopic': 'Пушкин',
     'condition': 'В каком году родился А.С. Пушкин?',
     'solution': 'А.С. Пушкин родился 26 мая (6 июня) 1799 года.',
     'answer': '1799'},
])

# ═══════════════════════════════════════════════════════════
# АНГЛИЙСКИЙ ЯЗЫК
# ═══════════════════════════════════════════════════════════

TASKS.extend([
    {'subject_code': 'english', 'year': 2024, 'task_number': 1, 'difficulty': 'base',
     'topic': 'Грамматика', 'subtopic': 'Времена',
     'condition': 'Choose the correct form: She ___ (go) to school every day.',
     'solution': 'Every day indicates Present Simple. She goes to school every day.',
     'answer': 'goes'},
    {'subject_code': 'english', 'year': 2024, 'task_number': 2, 'difficulty': 'base',
     'topic': 'Лексика', 'subtopic': 'Синонимы',
     'condition': 'Выберите синоним к слову "big": large, small, tiny, little',
     'solution': 'Синоним "big" — "large" (большой).',
     'answer': 'large'},
    {'subject_code': 'english', 'year': 2024, 'task_number': 3, 'difficulty': 'base',
     'topic': 'Чтение', 'subtopic': 'Понимание',
     'condition': 'What is the main idea of the text? (по тексту о природе)',
     'solution': 'Основная идея обычно выражена в первом или последнем абзаце текста.',
     'answer': 'зависит от текста'},
])


async def main():
    print("🚀 Загрузка полной базы заданий в стиле ФИПИ...\n")
    print(f"📊 Всего заданий для загрузки: {len(TASKS)}\n")
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is required")
    
    print("📥 Подключение к базе данных...")
    pool = await asyncpg.create_pool(db_url)
    
    # Группируем по предметам
    by_subject = {}
    for task in TASKS:
        subj = task['subject_code']
        if subj not in by_subject:
            by_subject[subj] = []
        by_subject[subj].append(task)
    
    print("\n📚 Распределение по предметам:")
    for subj, tasks in by_subject.items():
        print(f"   • {subj}: {len(tasks)} заданий")
    
    # Загружаем задания
    print(f"\n💾 Начинаю загрузку...")
    
    loaded = 0
    errors = 0
    async with pool.acquire() as conn:
        for task in TASKS:
            try:
                subj = await conn.fetchrow(
                    "SELECT id FROM subjects WHERE code = $1",
                    task['subject_code']
                )
                if not subj:
                    print(f"⚠️  Предмет {task['subject_code']} не найден")
                    errors += 1
                    continue
                
                await conn.execute("""
                    INSERT INTO fipi_tasks (
                        subject_id, year, task_number, difficulty,
                        topic, subtopic, condition, solution, answer, source_url
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    ON CONFLICT DO NOTHING
                """,
                    subj['id'],
                    task['year'],
                    task['task_number'],
                    task['difficulty'],
                    task['topic'],
                    task['subtopic'],
                    task['condition'],
                    task['solution'],
                    task['answer'],
                    'http://fipi.ru/'
                )
                loaded += 1
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                errors += 1
    
    # Статистика
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT subject_id) as subjects,
                COUNT(DISTINCT topic) as topics,
                COUNT(DISTINCT task_number) as task_numbers
            FROM fipi_tasks
        """)
        
        print(f"\n📊 ИТОГИ ЗАГРУЗКИ:")
        print(f"   ✅ Успешно загружено: {loaded}")
        print(f"   ❌ Ошибок: {errors}")
        print(f"   📚 Всего заданий в БД: {stats['total']}")
        print(f"   📖 Предметов: {stats['subjects']}")
        print(f"   🎯 Уникальных тем: {stats['topics']}")
        print(f"   🔢 Номеров заданий: {stats['task_numbers']}")
    
    await pool.close()
    print("\n✅ Загрузка завершена!")
    print("\n💡 Теперь проверь команды:")
    print("   /practice math-profile")
    print("   /predict math-profile")
    print("   /practice russian")
    print("   /practice physics")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Прервано")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
