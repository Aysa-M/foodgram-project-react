![WORKFLOW_STATUS](https://github.com/Aysa-M/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)

# ***Foodgram-project-react***
## **Описание проекта API для Foodgram.**
API для проекта Foodgram - приложение «Продуктовый помощник - FOODGRAM»: сайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на других авторов. Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд. 
- API проекта позволяет: 
    - регистрироваться и получать токен пользователям;
    - управлять своими постами;
    - добавлять в Избранное полюбившиеся рецепты;
    - длу удобства, пользователь может скачать список продуктов, необходимых для приготовления того или иного рецепта.

## **Технологии (основные инструменты):**
- Python==3.7
- gunicorn==20.0.4
- pytest==6.2.4
- Docker
- Django==3.2.14
- django-filter==22.1
- djangorestframework==3.13.1
- djoser==2.1.0
- docker==5.0.3
- docker-compose==1.29.2
- flake8==4.0.1
- isort==5.10.1
- Jinja2==3.1.2
- jsonschema==3.2.0
- MarkupSafe==2.1.1
- mccabe==0.6.1
- oauthlib==3.2.0
- Pillow==9.2.0
- psycopg2==2.9.3
- PyYAML==5.4.1

### Деплой в Dev режиме:
1. Клонируйте репозиторий:
    *$ git clone https://github.com/Aysa-M/foodgram-project-react.git*
 
2. Создайте виртуальное окружение (venv) - должен быть флажок в начале строки:
    *$ python -m venv venv*
 
3. Установите зависимости:
    *$ pip install -r requirements.txt*

4. Создайте и примените миграции:
    *$ python manage.py makemigrations*
    *$ python manage.py migrate*

5. Запустите django сервер:
    *$ python manage.py runserver*

### Деплой проекта на боевой сервер с помощью образа Docker:
1. Входим на боевой сервер (ваша виртуальная машина).

2. Необходимо установить **Docker** для дальнейшего процесса размещения проекта на боевом сервере. 
    *$ sudo apt install docker.io*

3. Проверьте наличие на сервере docker-compose. Если его нет, то установите его выполнив следующие команды по порядку:
   
    - Установите утилиту curl для скачивания docker-compose:
    *$ sudo apt -y install curl*
  
    - Скачиваем docker-compose с помощью утилитыЖ
    *$ sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose*

    - Добавим право исполняемости файла docker-compose:
    *sudo chmod +x /usr/local/bin/docker-compose*

    - Проверьте, что docker-compose работает путем проверки отображения списка комманд при его вызове:
    *docker-compose*

4. Запустите образ под названием проекта - *____* и разверните контейнеры с приложениями:
    *docker run _____*

5. Создайте и примените миграции внутри основного контейнера **web**:
    *$ docker-compose exec web python manage.py makemigrations*
    *$ docker-compose exec web python manage.py migrate*

6. Админка доступна по адресу http://

## **Документация к API:**
После запуска проекта 
по адресу http:// доступна документация для API **FoodGram**.

## **Автор:**
*Matsakova Aysa*
