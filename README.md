# Hermes ↔ OpenCode A2A Bridge

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Protocol: A2A v1.0](https://img.shields.io/badge/Protocol-A2A%20v1.0-orange.svg)](https://github.com/a2a-protocol)

**Hermes ↔ OpenCode A2A Bridge** — двунаправленная интеграция между [Hermes Agent](https://github.com/NousResearch/hermes-agent) и средой разработки [OpenCode](https://opencode.ai) + [Oh-My-OpenAgent (OMO)](https://github.com/code-yeongyu/oh-my-openagent) по стандартному протоколу **Agent-to-Agent (A2A)** (Linux Foundation & Google).

---

## 📖 Обзор

Проект реализует строгое разделение ролей между двумя специализированными AI-системами:

- **Hermes Agent (Оркестратор)**: Взаимодействие с пользователем (Telegram / CLI / Desktop), долгосрочная память (Mem0 / Qdrant), глубокий веб-поиск и ресерч, декомпозиция задач и верификация результатов.
- **OpenCode + OMO (Инженерный исполнитель)**: Многофайловая кодогенерация, LSP-анализ кода (Rust Analyzer, TypeScript), запуск компиляторов и линтеров (`cargo`, `pnpm`, `pytest`), прогон тестов и оформление Pull Request.

---

## 🏛️ Архитектура

```
Пользователь (Telegram / CLI / Desktop)
  │
  ▼
Hermes Agent (Port :9900)
  │  [Плагин: opencode_a2a]
  │  Инструмент: opencode_delegate(goal, directory, context_id)
  │
  ├── [Делегирование в OpenCode] ──→ opencode-a2a Adapter (Port :8000)
  │                                    │ (REST / SSE Stream)
  │                                    ▼
  │                                  opencode serve (Port :4096)
  │                                    │
  │                                    ▼
  │                                  Oh-My-OpenAgent (OMO Harness)
  │                                  (Sisyphus → Hephaestus, Oracle, Momus)
  │
  └── [Обратные запросы к Hermes] ←── ask-hermes Skill (JSON-RPC A2A)
                                      (Web Research, Mem0 Memory, User Q&A)
```

---

## 📦 Компоненты репозитория

```
hermes-opencode-a2a/
├── plugins/
│   └── hermes/
│       └── opencode_a2a/          # Нативный плагин для Hermes Agent (тул opencode_delegate)
│           ├── plugin.yaml
│           ├── __init__.py
│           └── client.py
├── skills/
│   └── opencode/
│       └── ask-hermes/            # Навык для OpenCode / OMO (обратный вызов Hermes)
│           ├── SKILL.md
│           └── scripts/
│               └── ask_hermes.py
├── docs/
│   └── deep-research-a2a.md       # Исследование спецификации A2A и аудита архитектуры
├── LICENSE
└── README.md
```

---

## 🚀 Установка и настройка

### 1. Требования
- Python 3.11+
- Node.js 20+
- OpenCode (`npm install -g opencode-ai`)
- OpenCode A2A Adapter (`uv tool install opencode-a2a`)

### 2. Запуск сервисов OpenCode

```bash
# 1. Запуск OpenCode Runtime
opencode serve --hostname 127.0.0.1 --port 4096

# 2. Запуск A2A Шлюза
A2A_STATIC_AUTH_CREDENTIALS='[{"scheme":"bearer","token":"your-secure-token","principal":"hermes"}]' \
OPENCODE_BASE_URL=http://127.0.0.1:4096 \
A2A_HOST=127.0.0.1 \
A2A_PORT=8000 \
OPENCODE_TIMEOUT=1800.0 \
OPENCODE_TIMEOUT_STREAM=1800.0 \
A2A_ALLOW_DIRECTORY_OVERRIDE=true \
opencode-a2a serve
```

### 3. Установка плагина в Hermes Agent

Скопируйте директорию плагина в папку плагинов Hermes:

```bash
mkdir -p ~/.hermes/plugins/
cp -r plugins/hermes/opencode_a2a ~/.hermes/plugins/
```

Плагин автоматически регистрирует нативный инструмент модели `opencode_delegate`.

### 4. Установка навыка в OpenCode

Скопируйте навык в конфигурацию OpenCode:

```bash
mkdir -p ~/.config/opencode/skills/
cp -r skills/opencode/ask-hermes ~/.config/opencode/skills/
```

---

## 💡 Примеры работы

### 1. Делегирование из Hermes в OpenCode
Hermes вызывает инструмент `opencode_delegate` во время диалога:

```python
# Вызов инструмента внутри Hermes:
opencode_delegate(
    goal="Внедрить модуль аутентификации JWT и написать unit-тесты.",
    directory="/home/user/projects/my-app",
    context_id="feature-auth-service",
    timeout=1800
)
```

### 2. Обратный вызов из OpenCode в Hermes
Когда агент внутри OMO (Sisyphus/Hephaestus) сталкивается с необходимостью внешнего поиска, чтения памяти или вопроса человеку:

```bash
python3 ~/.config/opencode/skills/ask-hermes/scripts/ask_hermes.py \
  "Найди паттерны безопасной ротации refresh токенов для FastAPI"
```

---

## ⚙️ Переменные конфигурации

| Переменная | Описание | По умолчанию |
|---|---|---|
| `OPENCODE_A2A_URL` | URL шлюза OpenCode A2A | `http://127.0.0.1:8000` |
| `OPENCODE_A2A_TOKEN` | Bearer-токен для авторизации в адаптере | — |
| `OPENCODE_TIMEOUT` | Таймаут синхронного ожидания задач (секунды) | `1800.0` |
| `OPENCODE_TIMEOUT_STREAM` | Таймаут стриминга задач (секунды) | `1800.0` |
| `A2A_ALLOW_DIRECTORY_OVERRIDE` | Разрешение выбора рабочей папки проекта | `true` |

---

## 📄 Лицензия

Распространяется под лицензией [MIT](LICENSE).
