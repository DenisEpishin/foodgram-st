# Продуктовый помощник Foodgram 


## Описание проекта

«Foodgram» — сайт, на котором пользователи могут публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Зарегистрированным пользователям доступен сервис «Список покупок», он позволяет формировать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Технологии

- Django
- React
- Docker
- Nginx
- Gunicorn
- PostgreSQL

## Запуск проекта

1. Клонируйте репозиторий:
    ```bash
    git clone https://github.com/DenisEpishin/foodgram-st.git
    ```
2. Перейдите в поддиректорию infra проекта:
    ```bash
    cd foodgram-st/infra
    ```
3. При необходимости измените файл .env:
4. Выполните сборку docker контейнеров:
    ```bash
    docker compose up -d --build
    ```
5. Выполните миграции:
    ```bash
    docker compose exec backend python manage.py migrate
    ```
6. Создайте суперпользователя:
    ```bash
    docker compose exec backend python manage.py createsuperuser
    ```
7. Заполните базу тестовыми ингредиентами:
    ```bash
    docker compose exec backend python manage.py load_ingredients data/ingredients.json
    ```
8. Загрузите статику:
    ```bash
    docker compose exec backend python manage.py collectstatic --no-input
    ```

# Автор

Епишин Денис