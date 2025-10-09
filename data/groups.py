# data/groups.py
"""Файл с данными о группах для всего приложения"""

# Бакалавриат и магистратура
BACHELOR_PREFIXES = ['ПМК', 'ИВТ', 'ИНФ', 'ПИ', 'САУ']
MASTER_PREFIXES = ['ПМКм', 'ИВТм', 'ИНФм', 'ПИм', 'САУм']

# Годы набора (ключи словаря GROUPS_BY_YEAR)
YEARS = [2025, 2024, 2023, 2022]

# Суффиксы в названии групп (используем двухзначные)
YEAR_SUFFIX = {
    2025: '25',
    2024: '24',
    2023: '23',
    2022: '22',
}

def _make_groups_for_year(year: int):
    """Сформировать список групп для указанного года (бакалавр + магистр)."""
    suf = YEAR_SUFFIX[year]
    # Формат: <префикс>-<двухзначный год>, напр. ПИ-25, ПИм-25
    bachelors = [f"{p}-{suf}" for p in BACHELOR_PREFIXES]
    masters = [f"{p}-{suf}" for p in MASTER_PREFIXES]
    return bachelors + masters

# Группы по годам
GROUPS_BY_YEAR = {year: _make_groups_for_year(year) for year in YEARS}

# Полный плоский список всех групп
DEFAULT_GROUPS = [g for year in YEARS for g in GROUPS_BY_YEAR[year]]

# Факультеты (если нужно разбивать по факультетам; здесь все считаем «ИСП»)
FACULTY_GROUPS = {
    'ИСП': DEFAULT_GROUPS,
    'Другие': []
}

def get_all_groups():
    """Возвращает все группы"""
    return DEFAULT_GROUPS

def get_groups_by_faculty(faculty):
    """Возвращает группы по факультету"""
    return FACULTY_GROUPS.get(faculty, [])

def get_groups_by_year(year):
    """Возвращает группы по году поступления (например, 2025)"""
    return GROUPS_BY_YEAR.get(year, [])

def _base_prefix(name: str) -> str:
    """
    Базовый префикс без суффикса 'м' (для определения факультета).
    Примеры: 'ПМКм' -> 'ПМК', 'ПИм' -> 'ПИ', 'ПМК' -> 'ПМК'
    """
    return name[:-1] if name.endswith('м') else name

def get_group_info(group_name):
    """Возвращает информацию о группе:
       {
         'name': <имя>,
         'year': <полный год, напр. 2025>,
         'faculty': 'ИСП' | 'Другие'
       }
    """
    if group_name in DEFAULT_GROUPS:
        parts = group_name.split('-')
        if len(parts) == 2 and parts[1].isdigit():
            yy = int(parts[1])         # 25 -> 2025
            year_full = 2000 + yy
        else:
            # На случай нестандартного имени
            year_full = None

        prefix = _base_prefix(parts[0])
        faculty = 'ИСП' if prefix in BACHELOR_PREFIXES else 'Другие'

        return {
            'name': group_name,
            'year': year_full,
            'faculty': faculty
        }
    return None
