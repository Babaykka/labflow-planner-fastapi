# LabFlow Planner

LabFlow Planner - REST-сервис на FastAPI для управления лабораторными проектами,
образцами, оборудованием и расписанием аналитических запусков.

Проект выбран как самостоятельная предметная область: лабораторное планирование
для небольших исследовательских команд. Сервис помогает не только хранить данные,
но и автоматически рассчитывает расписание анализов с учетом приоритетов,
дедлайнов, требуемого метода и дневной мощности оборудования.

## Возможности

- Регистрация пользователя и вход через OAuth2 Password Flow.
- JWT Bearer-токены для защищенных эндпоинтов.
- Реляционная SQLite-БД, которая создается автоматически при запуске.
- Связанные таблицы: users, projects, samples, equipment, analysis_runs.
- CRUD для проектов, образцов, оборудования и запусков анализов.
- Алгоритм оптимизации расписания через `/planner/optimize`.
- Сохранение рассчитанного плана через `/planner/commit`.
- Наполненный демо-аккаунт создается автоматически при старте приложения.
- Валидация входных данных Pydantic-схемами.
- Автоматические тесты на TestClient с покрытием выше 70%.
- Стартовая визуальная страница на `/`, Swagger на `/docs`, ReDoc на `/redoc`.

## Бизнес-задача

В лаборатории есть набор образцов, каждый из которых требует конкретный метод
анализа, имеет приоритет, оценку трудоемкости в часах и срок выполнения.
Оборудование поддерживает только определенный метод и имеет ограниченную
дневную мощность. Нужно быстро получить план, который:

1. сначала ставит в очередь более приоритетные образцы;
2. не назначает образец на несовместимый прибор;
3. не превышает дневную мощность оборудования;
4. штрафует просрочку дедлайна;
5. учитывает уже запланированные или выполняемые запуски.

Алгоритм находится в `app/services/planner.py`. Он сортирует образцы по
приоритету, дедлайну и трудоемкости, затем для каждого образца ищет лучший слот
по функции оценки.

## Стек

- Python 3.14
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- Pytest + TestClient
- Pylint

## Структура проекта

```text
app/
  core/            JWT, настройки, зависимости FastAPI
  routers/         REST-эндпоинты
  services/        алгоритмическая бизнес-логика
  static/          стили стартовой страницы
  templates/       HTML-интерфейс
  db.py            подключение и создание БД
  models.py        SQLAlchemy-модели
  schemas.py       Pydantic-схемы
tests/             тесты TestClient
docs/              инструкция для видеопрезентации и Postman-коллекция
```

## Запуск локально

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

После запуска:

- визуальная страница: http://127.0.0.1:8000/
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Если `DATABASE_URL` не задан, приложение создаст `labflow.db` в корне проекта.
Для стабильной авторизации между перезапусками задайте `SECRET_KEY` в `.env`.

## Демо-аккаунт

При первом запуске сервис автоматически создает наполненный аккаунт:

- email: `demo@labflow.local`
- пароль: `DemoPass123`

В аккаунте уже есть проект, приборы, образцы и запланированные анализы.

## Основные эндпоинты

| Метод | URL | Назначение |
| --- | --- | --- |
| POST | `/auth/register` | регистрация пользователя |
| POST | `/auth/token` | вход и получение JWT |
| GET | `/users/me` | текущий пользователь |
| POST | `/projects` | создать проект |
| GET | `/projects` | список проектов |
| GET | `/projects/{id}` | проект по id |
| PATCH | `/projects/{id}` | обновить проект |
| DELETE | `/projects/{id}` | удалить проект |
| POST | `/equipment` | создать прибор |
| GET | `/equipment` | список приборов |
| GET | `/equipment/{id}` | прибор по id |
| PATCH | `/equipment/{id}` | обновить прибор |
| DELETE | `/equipment/{id}` | удалить прибор |
| POST | `/samples` | создать образец |
| GET | `/samples` | список образцов |
| GET | `/samples/{id}` | образец по id |
| PATCH | `/samples/{id}` | обновить образец |
| DELETE | `/samples/{id}` | удалить образец |
| POST | `/runs` | создать запуск вручную |
| GET | `/runs` | список запусков |
| GET | `/runs/{id}` | запуск по id |
| PATCH | `/runs/{id}` | обновить запуск |
| DELETE | `/runs/{id}` | удалить запуск |
| POST | `/planner/optimize` | рассчитать план |
| POST | `/planner/commit` | сохранить рассчитанный план |

## Быстрая проверка через curl

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"manager@example.com","username":"labmanager","password":"StrongPass123","role":"manager"}'
```

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=manager@example.com&password=StrongPass123" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

```bash
curl -X POST http://127.0.0.1:8000/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Enzyme stability sprint","description":"Short-cycle screening","deadline":"2026-05-20","status":"active"}'
```

Для демонстрации удобнее открыть Swagger, нажать Authorize, вставить JWT и
последовательно выполнить запросы из `docs/labflow.postman_collection.json`.

## Тесты

```bash
pytest
```

Текущий результат: 6 тестов проходят, покрытие 85%.

## Pylint

```bash
pylint app > pylint.txt
```

Текущий результат: 10.00/10. Файл `pylint.txt` находится в корне проекта.

## Видеопрезентация

Подробный сценарий записи находится в `docs/video_presentation_guide.md`.
В нем расписаны подготовка, структура на 5-7 минут, порядок демонстрации API,
фрагмент кода для объяснения и команда для показа результата pylint.

В конце демонстрации можно сказать, что для быстрой проверки можно просто войти
в демо-аккаунт и посмотреть работоспособность сайта.

## Автор

Саша Леков.
