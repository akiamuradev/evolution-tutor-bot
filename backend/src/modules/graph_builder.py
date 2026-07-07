"""Построение графиков функций"""
import matplotlib.pyplot as plt
import numpy as np
import io
from sympy import sympify, lambdify, symbols

def build_graph(expression: str) -> bytes:
    """
    Строит график функции и возвращает PNG в байтах.
    Пример: "sin(x)", "x**2", "2*x + 1"
    """
    try:
        # Парсим выражение
        x = symbols('x')
        expr = sympify(expression.replace('^', '**'))
        
        # Создаём функцию
        f = lambdify(x, expr, modules=['numpy'])
        
        # Генерируем точки
        x_vals = np.linspace(-10, 10, 400)
        y_vals = f(x_vals)
        
        # Обрабатываем бесконечности
        y_vals = np.nan_to_num(y_vals, nan=np.nan, posinf=10, neginf=-10)
        
        # Строим график
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(x_vals, y_vals, 'b-', linewidth=2, label=f'y = {expression}')
        ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        ax.axvline(x=0, color='k', linestyle='-', linewidth=0.5)
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('x', fontsize=12)
        ax.set_ylabel('y', fontsize=12)
        ax.set_title(f'График функции y = {expression}', fontsize=14, pad=15)
        ax.legend(fontsize=10)
        ax.set_xlim(-10, 10)
        ax.set_ylim(-10, 10)
        
        # Сохраняем в байты
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        return buf.read()
    except Exception as e:
        print(f"Ошибка построения графика: {e}")
        return None
