# Hermes ↔ OpenCode (OMO) A2A Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Protocol: A2A v1.0](https://img.shields.io/badge/Protocol-A2A%20v1.0-orange.svg)](https://github.com/a2a-protocol)

**Hermes ↔ OpenCode A2A Bridge** — двунаправленный мост взаимодействия по стандартному протоколу **Agent-to-Agent (A2A v1.0)** (Linux Foundation & Google) между **Hermes Agent** (Nous Research) и инженерным рантаймом **OpenCode**, усиленным многоагентным харнессом **Oh-My-OpenAgent (OMO)**.

---

## 🎯 Назначение и разделение ролей

Система построена на связке двух независимых уровней:

- **Hermes Agent (Top-Level Orchestrator & Memory)**: 
  - Главный интерфейс общения с пользователем (Telegram, CLI, Desktop).
  - Хранилище долговременной памяти (Mem0, Qdrant).
  - Глобальное планирование, постановка целей и валидация результатов.
- **OpenCode + Oh-My-OpenAgent / OMO (Engineering Engine)**:
  - Автономная кодогенерация и многофайловый рефакторинг в режиме **`ultrawork`**.
  - Параллельный запуск специализированных агентов OMO (Sisyphus, Hephaestus, Oracle, Momus).
  - Работа с языковыми серверами (LSP), компиляция (`cargo`, `pnpm`, `pytest`), прогон тестов и оформление Pull Request.

---

## 👥 Агенты Oh-My-OpenAgent (OMO) в архитектуре

Когда Hermes делегирует задачу в OpenCode, харнесс OMO задействует специализированную команду агентов:

| Агент OMO | Роль | Зона ответственности |
|---|---|---|
| **`sisyphus`** | Ultraworker / Lead Orchestrator | Декомпозирует задачу на шаги, координирует суб-агентов и управляет жизненным циклом задачи |
| **`sisyphus-junior`** | Task Worker | Выполняет точечные изолированные подзадачи, делегированные Sisyphus |
| **`prometheus`** | Strategic Planner | Долгосрочное архитектурное планирование и анализ зависимостей в крупных проектах (`.omo/plans/`) |
| **`hephaestus`** | Deep Implementer | Тяжелое написание кода, рефакторинг, разработка алгоритмов и написание тестов |
| **`oracle`** | Advisor & Debugger | Архитектурные консультации, поиск тонких багов и математическая верификация |
| **`momus`** | Adversarial Reviewer | Строгий код-ревью, проверка граничных условий, диффов и полноты тестов перед сдачей |
| **`metis`** | Pre-implementation Analyst | Анализ требований, стресс-тестирование планов и поиск белых пятен до написания кода |
| **`explore` & `atlas`** | Recon & Navigation | Быстрый поиск по кодовой базе (grep/regex) и построение графа вызовов |
| **`compaction`** | Context Manager | Автоматическое сжатие контекста диалога для сохранения prompt cache locality |

---

## 🏛️ Архитектура моста (A2A v1.0)

```
                       Пользователь (Telegram / CLI / Web)
                                        │
                                        ▼
                                   Hermes Agent
                      (Оркестратор, Mem0 Память, Порт :9900)
                                  │          ▲
            [1. opencode_delegate]│          │[2. ask-hermes Skill]
            (A2A v1.0 HTTP REST)  │          │(A2A v1.0 JSON-RPC)
                                  ▼          │
                       OpenCode A2A Gateway (Порт :8000)
                                        │
                                        ▼
                           OpenCode Server (Порт :4096)
                                        │
                                        ▼
                          Oh-My-OpenAgent (OMO Harness)
                       ┌────────────────────────────────┐
                       │           Sisyphus             │
                       │    ┌───────────┴───────────┐   │
                       │    ▼                       ▼   │
                       │ Hephaestus               Oracle│
                       │ (Coding)              (Advisory)
                       │    │                       │   │
                       │    └───────────┬───────────┘   │
                       │                ▼               │
                       │              Momus             │
                       │          (Code Review)         │
                       └────────────────────────────────┘
```

---

## ⚙️ Переменные окружения (Configuration)

### 1. Прямой канал: Hermes ➔ OpenCode (`opencode_delegate`)
| Переменная | По умолчанию | Описание |
|---|---|---|
| `OPENCODE_A2A_URL` | `http://127.0.0.1:8000` | URL шлюза OpenCode A2A Gateway |
| `OPENCODE_A2A_TOKEN` | `6624bef6...6a85` | Bearer-токен авторизации в A2A Gateway |
| `OPENCODE_A2A_TIMEOUT` | `1800` | Максимальный таймаут выполнения задачи в секундах (30 мин) |

### 2. Обратный канал: OMO ➔ Hermes (`ask-hermes`)
| Переменная | По умолчанию | Описание |
|---|---|---|
| `HERMES_A2A_URL` | `http://127.0.0.1:9900/` | URL входного A2A JSON-RPC шлюза Hermes |
| `HERMES_A2A_TOKEN` | `""` | Опциональный Bearer-токен авторизации в Hermes |
| `HERMES_A2A_TIMEOUT` | `300` | Таймаут ожидания ответа от Hermes в секундах |

---

## 🔄 Протокол и жизненный цикл задач

1. **Асинхронная диспетчеризация (`returnImmediately: true`):**
   - Запрос `POST /message:send` с заголовками `A2A-Version: 1.0` и `A2A-Extensions: urn:opencode-a2a:extension:session-binding:v1`.
   - Мгновенное получение `task_id` и `context_id`.
   - Передача целевой рабочей директории через `metadata.opencode.directory`.
2. **Адаптивный поллинг (`GET /tasks/{id}`):**
   - Опрос состояния с интервалом 2 секунды.
   - Корректная обработка начальных `404` (регистрация задачи).
   - Мгновенная реакция на состояния: `TASK_STATE_COMPLETED`, `TASK_STATE_FAILED`, `TASK_STATE_INPUT_REQUIRED`.
3. **Надежная отмена (`POST /tasks/{id}:cancel`):**
   - При срабатывании таймаута клиент выполняет отмену задачи на стороне OpenCode (до 3 попыток), исключая зависание фоновых процессов-зомби.
4. **Защита от утечек секретов:**
   - Автоматическая маскировка Bearer-токенов и API-ключей в телах ошибок и логах.

---

## 📦 Структура репозитория

```
hermes-opencode-a2a/
├── plugins/
│   └── hermes/
│       └── opencode_a2a/          # Нативный плагин Hermes (opencode_delegate)
│           ├── plugin.yaml
│           ├── __init__.py
│           └── client.py
├── skills/
│   ├── hermes/
│   │   └── omo-agents-guide/      # Руководство по агентам OMO для Hermes
│   │       └── SKILL.md
│   └── opencode/
│       └── ask-hermes/            # Навык OMO для обратных запросов в Hermes
│           ├── SKILL.md
│           └── scripts/
│               └── ask_hermes.py
├── tests/                         # Unit-тесты для A2A моста
│   ├── test_client.py
│   └── test_ask_hermes.py
└── README.md
```

---

## 🧪 Тестирование

Запуск тестов:
```bash
pytest tests/ -v
```
