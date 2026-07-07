"""Утилиты: АГРЕССИВНАЯ конвертация математических символов"""
import re

def convert_to_math_symbols(text: str | None) -> str:
    """
    АГРЕССИВНАЯ конвертация текстовых обозначений в математические символы.
    Работает даже если ИИ написал текстом.
    """
    
    # 1. LaTeX-команды (ИИ часто их использует)
    text = str(text or "")

    latex_replacements = {
        r'\\alpha\b': 'α', r'\\beta\b': 'β', r'\\gamma\b': 'γ', 
        r'\\delta\b': 'δ', r'\\Delta\b': 'Δ', r'\\epsilon\b': 'ε',
        r'\\theta\b': 'θ', r'\\Theta\b': 'Θ', r'\\lambda\b': 'λ',
        r'\\mu\b': 'μ', r'\\pi\b': 'π', r'\\sigma\b': 'σ',
        r'\\Sigma\b': 'Σ', r'\\phi\b': 'φ', r'\\Phi\b': 'Φ',
        r'\\omega\b': 'ω', r'\\Omega\b': 'Ω', r'\\infty\b': '∞',
        r'\\partial\b': '∂', r'\\nabla\b': '∇', r'\\times\b': '×',
        r'\\div\b': '÷', r'\\cdot\b': '·', r'\\pm\b': '±',
        r'\\leq\b': '≤', r'\\geq\b': '≥', r'\\neq\b': '≠',
        r'\\approx\b': '≈', r'\\equiv\b': '≡', r'\\subset\b': '⊂',
        r'\\supset\b': '⊃', r'\\in\b': '∈', r'\\notin\b': '∉',
        r'\\cup\b': '∪', r'\\cap\b': '∩', r'\\emptyset\b': '∅',
        r'\\forall\b': '∀', r'\\exists\b': '∃', r'\\neg\b': '¬',
        r'\\wedge\b': '∧', r'\\vee\b': '', r'\\perp\b': '⊥',
        r'\\parallel\b': '∥', r'\\angle\b': '∠', r'\\triangle\b': '△',
        r'\\square\b': '□', r'\\circle\b': '○', r'\\degree\b': '°',
        r'\\rightarrow\b': '→', r'\\leftarrow\b': '←',
        r'\\Rightarrow\b': '⇒', r'\\Leftarrow\b': '',
        r'\\leftrightarrow\b': '↔', r'\\Leftrightarrow\b': '⇔',
        r'\\uparrow\b': '↑', r'\\downarrow\b': '↓',
        r'\\therefore\b': '∴', r'\\because\b': '∵',
    }
    
    for pattern, symbol in latex_replacements.items():
        text = re.sub(pattern, symbol, text)
    
    # 2. Текстовые обозначения (без \b, более агрессивно)
    text_replacements = [
        # Греческие буквы (с приоритетом на математический контекст)
        (r'\bAlpha\b', 'Α'), (r'\bBeta\b', 'Β'), (r'\bGamma\b', 'Γ'),
        (r'\bDelta\b', 'Δ'), (r'\bEpsilon\b', 'Ε'), (r'\bTheta\b', 'Θ'),
        (r'\bLambda\b', 'Λ'), (r'\bPi\b', 'Π'), (r'\bSigma\b', 'Σ'),
        (r'\bPhi\b', 'Φ'), (r'\bPsi\b', ''), (r'\bOmega\b', 'Ω'),
        (r'\balpha\b', 'α'), (r'\bbeta\b', 'β'), (r'\bgamma\b', 'γ'),
        (r'\bdelta\b', 'δ'), (r'\bepsilon\b', 'ε'), (r'\bzeta\b', 'ζ'),
        (r'\beta\b', 'β'), (r'\bgamma\b', 'γ'), (r'\bdelta\b', 'δ'),
        (r'\btheta\b', 'θ'), (r'\blambda\b', 'λ'), (r'\bmu\b', 'μ'),
        (r'\bnu\b', 'ν'), (r'\bxi\b', 'ξ'), (r'\bpi\b', 'π'),
        (r'\brho\b', 'ρ'), (r'\bsigma\b', 'σ'), (r'\btau\b', 'τ'),
        (r'\bphi\b', 'φ'), (r'\bchi\b', 'χ'), (r'\bpsi\b', 'ψ'),
        (r'\bomega\b', 'ω'),
        
        # Математические функции и операторы
        (r'\binfinity\b', '∞'), (r'\bInfinity\b', '∞'),
        (r'\bpartial\b', '∂'), (r'\bnabla\b', '∇'),
        (r'\btimes\b', '×'), (r'\bdiv\b', '÷'), (r'\bcdot\b', '·'),
        (r'\bpm\b', '±'), (r'\bmp\b', ''),
        (r'\bleq\b', '≤'), (r'\bgeq\b', '≥'), (r'\bneq\b', '≠'),
        (r'\bapprox\b', '≈'), (r'\bequiv\b', '≡'),
        (r'\bsubset\b', '⊂'), (r'\bsupset\b', '⊃'),
        (r'\bin\b', '∈'), (r'\bnotin\b', '∉'),
        (r'\bcup\b', '∪'), (r'\bcap\b', '∩'), (r'\bemptyset\b', '∅'),
        (r'\bforall\b', '∀'), (r'\bexists\b', '∃'),
        (r'\bneg\b', '¬'), (r'\bwedge\b', '∧'), (r'\bvee\b', '∨'),
        (r'\bperp\b', '⊥'), (r'\bparallel\b', '∥'),
        (r'\bangle\b', '∠'), (r'\btriangle\b', '△'),
        (r'\btherefore\b', '∴'), (r'\bbecause\b', '∵'),
        
        # Стрелки
        (r'\brightarrow\b', '→'), (r'\bleftarrow\b', '←'),
        (r'\bRightarrow\b', '⇒'), (r'\bLeftarrow\b', '⇐'),
        (r'\bleftrightarrow\b', '↔'), (r'\bLeftrightarrow\b', ''),
        (r'\buparrow\b', '↑'), (r'\bdownarrow\b', '↓'),
        
        # Математические слова → символы
        (r'\bintegral\b', '∫'), (r'\bIntegral\b', '∫'),
        (r'\bsum\b', '∑'), (r'\bSum\b', '∑'),
        (r'\bsqrt\b', '√'), (r'\bSqrt\b', '√'),
        (r'\bsquare root\b', '√'),
        (r'\blim\b', 'lim'),  # lim оставляем, но добавляем пробел после
    ]
    
    for pattern, symbol in text_replacements:
        text = re.sub(pattern, symbol, text)
    
    # 3. Специальные паттерны (частые комбинации)
    special_patterns = [
        # Стрелки
        (r'\s*->\s*', ' → '),
        (r'\s*=>\s*', ' ⇒ '),
        (r'\s*<-\s*', ' ← '),
        (r'\s*<=>\s*', ' ⇔ '),
        (r'\s*!=\s*', ' ≠ '),
        (r'\s*<=\s*', ' ≤ '),
        (r'\s*>=\s*', ' ≥ '),
        
        # Многоточие
        (r'\.\.\.', '…'),
        
        # Градусы
        (r'\bdeg\b', '°'),
        (r'\bdegree\b', '°'),
    ]
    
    for pattern, replacement in special_patterns:
        text = re.sub(pattern, replacement, text)
    
    # 4. Степени: x^2 → x², x^n → xⁿ
    superscripts = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '', '7': '⁷', '8': '⁸', '9': '⁹',
        'n': 'ⁿ', 'i': 'ⁱ', '+': '⁺', '-': '⁻', 'x': 'ˣ'
    }
    
    def replace_superscript(match):
        char = match.group(1)
        return superscripts.get(char, match.group(0))
    
    text = re.sub(r'\^([0-9n+\-ix])', replace_superscript, text)
    
    # 5. Простые дроби
    fractions = {
        '1/2': '½', '1/3': '⅓', '2/3': '⅔', '1/4': '¼', '3/4': '¾',
        '1/5': '', '2/5': '⅖', '3/5': '⅗', '4/5': '⅘',
        '1/6': '⅙', '5/6': '⅚', '1/8': '⅛', '3/8': '⅜', '5/8': '⅝', '7/8': '⅞'
    }
    
    for frac, symbol in fractions.items():
        text = text.replace(frac, symbol)
    
    # 6. Чистим лишние пробелы вокруг символов
    text = re.sub(r'\s+([→⇒←⇔≠≤≥])\s+', r' \1 ', text)
    text = re.sub(r'([αβγδεζηθικλμνξπρστυφχψω])\s+', r'\1 ', text)
    
    return text

def force_clean_text(text: str | None) -> str:
    """Очищает текст, но СОХРАНЯЕТ математические символы"""
    # Сначала конвертируем всё в красивые символы
    text = str(text or "")
    text = convert_to_math_symbols(text)
    
    # Убираем оставшиеся LaTeX-команды
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'\1/\2', text)
    text = re.sub(r'\\\((.*?)\\\)', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'\\\[(.*?)\\\]', r'\1', text, flags=re.DOTALL)
    
    # Убираем $$ и $
    text = text.replace('$$', '').replace('$', '')
    
    # Убираем Markdown
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    text = re.sub(r'^#{1,3}\s*', '', text, flags=re.MULTILINE)
    
    # Удаляем иероглифы
    text = re.sub(r'[\u4e00-\u9fff]+', '', text)
    
    # Убираем слова-артефакты
    for word in ['frac', 'latex', 'markdown', 'programming', 'программирование', 'код', 'типизация']:
        text = re.sub(rf'[^.!?]*\b{word}\b[^.!?]*[.!?]?', '', text, flags=re.IGNORECASE)
    
    return text.strip()

def clean_markdown_for_document(text: str | None) -> str:
    """Очищает Markdown для документов, сохраняет математические символы"""
    text = convert_to_math_symbols(text)
    
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\-\*]\s+', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[\u4e00-\u9fff]+', '', text)
    return text.strip()

def split_text_for_telegram(text: str | None, max_len: int = 3000) -> list:
    """Разбивает длинный текст на части для Telegram"""
    text = str(text or "")
    if not text.strip():
        return []
    if len(text) <= max_len:
        return [text]
    parts, current = [], ""
    for chunk in text.split('\n\n'):
        if len(current) + len(chunk) + 2 <= max_len:
            current += ("\n\n" if current else "") + chunk
        else:
            if current:
                parts.append(current)
            current = chunk
            if len(current) > max_len:
                sentences = re.split(r'([.!?]\s+)', current)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) <= max_len:
                        current += sent
                    else:
                        if current:
                            parts.append(current)
                        current = sent
    if current:
        parts.append(current)
    return [p.strip() for p in parts if p.strip()]
