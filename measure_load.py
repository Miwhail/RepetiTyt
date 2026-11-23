import time
import urllib.request
import urllib.parse

BASE = 'http://127.0.0.1:8000'


targets = [
    ('Каталог, страница 1', '/catalog/'),
    ('Каталог, последняя страница', '/catalog/?page=84'),
    ('Пустой результат поиска', '/catalog/?search=' + urllib.parse.quote('математика')),
    ('Фильтр без совпадений', '/catalog/?subject=1&price_min=9999'),
    ('Живой поиск (AJAX)', '/api/live-search/?q=' + urllib.parse.quote('а')),
]


for name, path in targets:
    times = []
    for _ in range(3):
        start = time.perf_counter()
        try:
            urllib.request.urlopen(BASE + path, timeout=30).read()
        except Exception as e:
            print(f'{name}: ОШИБКА — {e}')
            break
        times.append(time.perf_counter() - start)
    else:
        print(f'{name}: {sum(times) / len(times):.2f} с (среднее из 3)')
