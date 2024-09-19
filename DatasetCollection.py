import requests
from bs4 import BeautifulSoup
import csv
import os
import re


# Функция для вычисления среднего значения из диапазона
def average_of_range(range_text):
    numbers = re.findall(r'\d+', range_text)  # Найти все числа в диапазоне
    if len(numbers) == 2:
        return str((int(numbers[0]) + int(numbers[1])) / 2)  # Вычислить среднее
    elif len(numbers) == 1:
        return numbers[0]  # Если только одно число, вернуть его
    return 'N/A'  # Если не удалось извлечь числа


# Функция для извлечения данных с одной страницы
def extract_data_from_page(page_number):
    url = f'https://cosmily.com/ingredients?page={page_number}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    ingredients_data = []

    for h3_tag in soup.find_all('h3', class_='MuiTypography-root MuiTypography-h4 css-m40ztq'):
        name = h3_tag.get_text(strip=True)

        # Найти все <div> элементы, следующие за <h3> для получения рейтингов
        parent_div = h3_tag.find_next('div', class_='MuiBox-root')

        # Извлечь EWG рейтинг
        ewg = 'N/A'
        cmg = 'N/A'

        if parent_div:
            # Найти все <p> элементы в родительском <div>
            for p in parent_div.find_all('p', class_='MuiTypography-root MuiTypography-body1 css-13hon30'):
                b_tag = p.find('b')
                if b_tag:
                    rating_text = b_tag.get_text(strip=True)
                    if 'EWG' in rating_text:
                        ewg = average_of_range(rating_text)  # Вычислить среднее значение для EWG
                    elif 'CMG' in rating_text:
                        cmg = average_of_range(rating_text)  # Вычислить среднее значение для CMG

        ingredients_data.append([name, ewg, cmg])

    return ingredients_data


# Основной код для сбора данных со всех страниц
all_ingredients_data = []

# Перебор всех страниц
for page_number in range(1, 459):  # Предполагаем, что на сайте 458 страниц
    print(f"Сбор данных со страницы {page_number}...")
    page_data = extract_data_from_page(page_number)
    all_ingredients_data.extend(page_data)

# Запись данных в CSV файл
csv_file_path = os.path.join(os.path.expanduser('~'), 'ingredients.csv')
with open(csv_file_path, 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['Ingredient', 'EWG Rating', 'CMG Rating'])  # Заголовки CSV
    writer.writerows(all_ingredients_data)  # Данные

print(f"Данные успешно записаны в {csv_file_path}")
