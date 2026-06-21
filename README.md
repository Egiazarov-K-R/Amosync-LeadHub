“AmoSync – LeadHub” – README.md


[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/Telegram-aiogram_3.x-blue.svg)](https://github.com/aiogram/aiogram)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Container-Docker-blue.svg)](https://www.docker.com/)

> Всем привет! Меня зовут Камо — и я начинающий разработчик, хочу решать задачи бизнеса. Это первый серьезный проект, все свои b2b-проекты я строю по формуле:
> **Решаем задачу А с результатом Б за время Т с экономией денег/ростом выручки Х руб.**

---

## 💼 Бизнес-ценность проекта (Бизнес-формула)

*   **Задача А (Проблема):** Ручной и долгий поиск лидов на платформе поставщика (например, бытовой техники Haier), приводящий к потере клиентов из-за низкой скорости первого контакта (*Speed-to-Lead*).
*   **Результат Б (Решение):** Полностью автоматизированный middleware-сервис, мгновенно перехватывающий заявки и распреденяющий их среди дежурных менеджеров.
*   **Время Т (Метрика):** Скорость доставки лида от момента его появления на сайте поставщика до экрана смартфона менеджера составляет **менее 30 секунд**.
*   **Рост выручки Х:** Повышение конверсии из клика в успешную сделку до **35-40%** за счет моментальной обработки «горячего» клиента (лид падает нашему клиенту-дилеру раньше, чем конкурентам).

---

## 🗺 Схема работы и Архитектура системы


text

[Платформа Поставщика] (randomuser.me)

│ 

│ (Async GET-Polling, раз в 30-60 сек)

▼

[AmoSync Middleware] ◄──► [PostgreSQL DB (Async SQLAlchemy 2.0)]

│

┌───────┴───────┐

▼ ▼

[AmoCRM API] [Telegram Bot (aiogram 3.x)]

│ │

│ (Fallback) │ (Распределение Round-Robin)

▼ ▼

[Синхронизация] [Групповой чат менеджеров]

│

▼ (Защита от Race Condition)

[Успешный Менеджер]


## 🛠 Технологический стек

*   **Core:** Python 3.11 (Asyncio)
*   **Database:** PostgreSQL + SQLAlchemy 2.0 (Async Mode) + Alembic (миграции)
*   **Data Validation:** Pydantic v2 (Schemas + Settings)
*   **API Clients:** HTTPX (Asynchronous HTTP)
*   **Messenger API:** Aiogram 3.x (Telegram Bot)
*   **Containerization:** Docker + Docker Compose
*   **Testing:** Pytest

---

## 🗄 Структура Базы Данных (PostgreSQL)

### 1. Таблица `amocrm_tokens` (Строго одна запись)
Хранит и автоматически обновляет ключи авторизации для OAuth 2.0.
| Поле | Тип | Описание |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Идентификатор записи |
| `access_token` | Text | Токен доступа к API AmoCRM |
| `refresh_token` | Text | Токен для обновления пары ключей |
| `updated_at` | Timestamp | Время последнего обновления |

### 2. Таблица `managers` (Реестр сотрудников)
Очередь менеджеров для распределения заявок по алгоритму Round-Robin.
| Поле | Тип | Описание |
| :--- | :--- | :--- |
| `id` | Integer (PK) | Идентификатор |
| `amo_user_id` | Integer | ID пользователя внутри AmoCRM |
| `tg_chat_id` | BigInteger | Telegram ID менеджера |
| `tg_username` | String | Никнейм в Telegram |
| `is_active` | Boolean | Статус доступности на смене |
| `last_assigned_at` | Timestamp | Время назначения последнего лида |

### 3. Таблица `lead_logs` (Журнал транзакций)
Обеспечивает сохранность данных и отслеживание статуса каждого лида.
| Поле | Тип | Статус по умолчанию | Описание |
| :--- | :--- | :--- | :--- |
| `id` | Integer (PK) | - | Идентификатор |
| `external_lead_id` | String (Unique) | - | Уникальный ID на стороне поставщика |
| `client_name` | String | - | Имя потенциального покупателя |
| `client_phone` | String | - | Номер телефона |
| `price` | Numeric | - | Сгенерированный бюджет сделки |
| `status` | Enum | `new` | Текущий статус обработки (см. ниже) |
| `manager_id` | Integer (FK) | Null | Назначенный менеджер |
| `amo_lead_id` | Integer | Null | ID созданной сделки в AmoCRM |
| `created_at` | Timestamp | `NOW()` | Время фиксации лида в системе |

> **Допустимые статусы лида:**
> *   `new` — получен, ожидает обработки и валидации.
> *   `distributed` — успешно назначен свободному менеджеру и отправлен в ТГ.
> *   `crm_offline` — AmoCRM недоступна, лид ушел напрямую дежурному в ТГ.
> *   `synced` — лид успешно синхронизирован с AmoCRM (создан контакт и сделка).
> *   `duplicate` — проигнорирован (предотвращение дублирования данных).

---

## ⚙️ Ключевой функционал и Инженерные решения

### 🔄 1. Сбор, валидация и дедупликация данных (Fetcher)
Асинхронный фоновый воркер опрашивает API поставщика (в демо-версии реализован mock-клиент на `randomuser.me`). Данные проходят валидацию через **Pydantic v2**: номера телефонов очищаются от лишних символов, генерируется случайный бюджет. Перед сохранением происходит транзакционная проверка уникальности `external_lead_id` в PostgreSQL, что исключает дублирование лидов.

### 🛡️ 2. Fallback-режим при отказе CRM
Если внешнее API AmoCRM возвращает `5xx` ошибку или таймаут, софт переключает статус лида на `crm_offline`, не прерывая выполнение. Заявка мгновенно летит в Telegram-бот. Раз в 5-10 минут фоновый асинхронный таск ищет в БД записи со статусом `crm_offline` и досылает их в ожившую AmoCRM. Бизнес гарантированно не теряет ни одного лида.

### 📊 3. Алгоритм распределения Round-Robin
При получении нового лида система ищет в таблице `managers` активного сотрудника (`is_active = True`) с наименьшей (самой старой) датой `last_assigned_at`. После отправки заявки дата обновляется, перемещая менеджера в конец очереди.

### 🔒 4. Защита от Race Condition в Telegram
В чате менеджеров кнопка **[Взять в работу]** защищена от ситуации, когда два сотрудника кликают на неё одновременно. Обработка нажатия кнопки атомарна на уровне СУБД:

sql

UPDATE lead_logs 

SET manager_id = :manager_id, status = 'synced' 

WHERE id = :lead_id AND manager_id IS NULL;
Если строка уже обновлена другим менеджером, СУБД вернет 0 измененных строк. Система выдаст остальным менеджерам вежливое уведомление: *"Заявку уже забрал @username"*.

### 🔑 5. Автоматическое обновление OAuth 2.0
Токены для интеграции с AmoCRM обновляются автоматически за 1 час до истечения их срока жизни (раз в 23 часа), исключая риск внезапной остановки синхронизации.

---

## 🚀 Быстрый старт в Docker

### 1. Клонирование репозитория


bash

git clone https://github.com/yourusername/AmoSync-LeadHub.git

cd AmoSync-LeadHub
### 2. Настройка окружения
Создайте файл `.env` в корневой папке проекта на основе примера:


env

Database Settings

POSTGRES_DB=amosync_db

POSTGRES_USER=postgres

POSTGRES_PASSWORD=super_secure_password

DB_HOST=db

DB_PORT=5432

Telegram Bot

BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ

AmoCRM Configuration

AMO_SUBDOMAIN=your_subdomain

AMO_CLIENT_ID=your_client_id

AMO_CLIENT_SECRET=your_client_secret

AMO_REDIRECT_URI=https://yourdomain.com
### 3. Запуск системы через Docker Compose
Сборка контейнеров и запуск всех сервисов (БД, бот, воркеры, миграции Alembic) одной командой:


bash

docker-compose up -d --build
---

## 🧪 Качество и стандарты кода
*   **Соблюдение PEP 8:** Код отформатирован линтерами (Black, Flake8).
*   **Type Hinting:** Полная аннотация типов повышает читаемость и защищает от скрытых багов на этапе статического анализа (MyPy).
*   **Документация:** Все модули, классы и функции задокументированы согласно международному стандарту **Google Style Python Docstrings**.

****
