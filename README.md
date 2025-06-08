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
3. Создайте .env файл на основе тестового и отредактируйте его при необходимости:
    ```bash
    cp .env.example .env
    ```
4. Выполните сборку docker контейнеров:
    ```bash
    docker compose up -d --build
    ```
5. Создайте суперпользователя:
    ```bash
    docker exec -it foodgram-back python manage.py createsuperuser
    ```
6. Для остановки используйте:
    ```bash
    docker compose down
    ```
7. Для повторного запуска:
    ```bash
    docker compose up
    ```

# Автор

Епишин Денис