# Hermes ↔ OpenCode (OMO) A2A Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Protocol: A2A v1.0](https://img.shields.io/badge/Protocol-A2A%20v1.0-orange.svg)](https://github.com/a2a-protocol)

**Hermes ↔ OpenCode A2A Bridge** — двунаправленный мост взаимодействия по стандартному протоколу **Agent-to-Agent (A2A)** (Linux Foundation & Google) между **Hermes Agent** (Nous Research) и инженерным рантаймом **OpenCode**, усиленным многоагентным харнессом **Oh-My-OpenAgent (OMO)**.

---

## 🎯 Назначение и разделение ролей

Система построена на связке двух независимых уровней:

- **Hermes Agent (Top-Level Orchestrator & Memory)**: 
  - Главный интерфейс общения с пользователем (Telegram, CLI, Desktop).
  - Хранилище долговременной памяти (Mem0, Qdrant).
  - Глобальное планирование, постановка целей и валидация результатов.
- **OpenCode + Oh-My-OpenAgent / OMO (Engineering Engine)**:
  - Автономная кодогенерация и многофайловый рефакторинг.
  - Параллельный запуск специализированных агентов OMO (Sisyphus, Hephaestus, Oracle, Momus).
  - Работа с языковыми серверами (LSP), компиляция (`cargo`, `pnpm`, `pytest`), прогон тестов и оформление Pull Request.

---

## 👥 Агенты Oh-My-OpenAgent (OMO) в архитектуре

Когда Hermes делегирует задачу в OpenCode, харнесс OMO задействует специализированную команду агентов:

| Агент OMO | Роль | Зона ответственности |
|---|---|---|
| **`sisyphus`** | Ultraworker / Lead Orchestrator | Декомпозирует задачу на шаги (`todowrite`), координирует суб-агентов и управляет циклом выполнения |
| **`sisyphus-junior`** | Task Worker | Выполняет точечные изолированные подзадачи, делегированные Sisyphus |
| **`prometheus`** | Strategic Planner | Долгосрочное архитектурное планирование и анализ зависимостей в крупных проектах |
| **`hephaestus`** | Deep Implementer | Тяжелое написание кода, рефакторинг, разработка алгоритмов и написание тестов |
| **`oracle`** | Advisor & Debugger | Архитектурные консультации, поиск тонких багов и математическая верификация |
| **`momus`** | Adversarial Reviewer | Строгий код-ревью, проверка граничных условий, диффов и полноты тестов |
| **`metis`** | Pre-implementation Analyst | Анализ требований, стресс-тестирование планов и поиск белых пятен до написания кода |
| **`explore` & `atlas`** | Recon & Navigation | Быстрый поиск по кодовой базе (grep/regex) и построение графа вызовов |
| **`compaction`** | Context Manager | Автоматическое сжатие контекста диалога для сохранения prompt cache locality |

---

## 🏛️ Архитектура моста

```
                       Пользователь (Telegram / CLI / Web)
                                        │
                                        ▼
                                   Hermes Agent
                      (Оркестратор, Mem0 Память, Порт :9900)
                                  │          ▲
            [1. opencode_delegate]│          │[2. ask-hermes Skill]
                                  ▼          │
                       OpenCode A2A Adapter (Порт :8000)
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

## 🔄 Двунаправленные сценарии работы

### 1. Hermes → OpenCode / OMO (`opencode_delegate`)
Hermes вызывает нативный инструмент для делегирования инженерных задач:

```python
opencode_delegate(
    goal="Внедрить модуль аутентификации JWT и написать unit-тесты.",
    directory="/home/user/projects/my-app",
    context_id="feature-auth-service",
    timeout=1800
)
```

### 2. OMO → Hermes (`ask-hermes`)
Когда агент OMO (Sisyphus, Hephaestus, Oracle) во время работы сталкивается с необходимостью:
- Проверить долговременную память проекта в Mem0 / Qdrant;
- Уточнить архитектурные договоренности из прошлых сессий;
- Запросить у человека в Telegram подтверждение развилки в архитектуре.

Агент вызывает утилиту:
```bash
python3 ~/.config/opencode/skills/ask-hermes/scripts/ask_hermes.py \
  "Какой алгоритм хеширования паролей был согласован для auth-модуля?"
```

---

## 📦 Структура репозитория

```
hermes-opencode-a2a/
├── plugins/
│   └── hermes/
│       └── opencode_a2a/          # Плагин Hermes (инструмент opencode_delegate)
│           ├── plugin.yaml
│           ├── __init__.py
│           └── client.py
├── skills/
│   └── opencode/
│       └── ask-hermes/            # Навык для OpenCode + OMO (обратный вызов Hermes)
│           ├── SKILL.md
│           └── scripts/
│               └── ask_hermes.py
├── LICENSE
└── README.md
```

---

## 🚀 Быстрый старт

### 1. Запуск OpenCode с OMO
```bash
# OpenCode сервер
opencode serve --hostname 127.0.0.1 --port 4096

# A2A адаптер с расширенным таймаутом для тяжелых OMO-сборок
A2A_STATIC_AUTH_CREDENTIALS='[{"scheme":"bearer","token":"your-secure-token","principal":"hermes"}]' \
OPENCODE_BASE_URL=http://127.0.0.1:4096 \
A2A_HOST=127.0.0.1 \
A2A_PORT=8000 \
OPENCODE_TIMEOUT=1800.0 \
OPENCODE_TIMEOUT_STREAM=1800.0 \
A2A_ALLOW_DIRECTORY_OVERRIDE=true \
opencode-a2a serve
```

### 2. Установка плагина в Hermes
```bash
mkdir -p ~/.hermes/plugins/
cp -r plugins/hermes/opencode_a2a ~/.hermes/plugins/
```

### 3. Установка навыка в OpenCode
```bash
mkdir -p ~/.config/opencode/skills/
cp -r skills/opencode/ask-hermes ~/.config/opencode/skills/
```

---

## 📄 Лицензия

MIT License (c) 2026 Denis & Contributors
