# Hermes ↔ OpenCode A2A Bridge

Двунаправленный мост меж-агентного взаимодействия (**Agent-to-Agent / A2A Protocol**) между **Hermes Agent** (Nous Research) и средой разработки **OpenCode + Oh-My-OpenAgent (OMO)**.

Стандарт протокола: [Linux Foundation / Google A2A v1.0.0](https://github.com/a2a-protocol).

---

## 💡 Зачем это нужно?

Разделение обязанностей между агентами разного профиля:
- **Hermes Agent (Top-Level Orchestrator)**: диалог с пользователем (Telegram / CLI / Desktop), долгосрочная память (Mem0, Qdrant), глубокий веб-поиск и ресерч, декомпозиция крупных целей и валидация результатов.
- **OpenCode + OMO (Engineering Execution)**: автономная кодогенерация, многофайловый рефакторинг, запуск LSP (Rust Analyzer, TypeScript), компиляция (`cargo`, `pnpm`, `just`), прогон тестов и создание Pull Request через GitHub CLI.

Благодаря протоколу **A2A** агенты общаются как равные узлы (Peers) без жесткой привязки к внутренностям друг друга.

---

## 🏛️ Архитектура системы

```
Пользователь (Telegram / CLI / Desktop)
  ↓
Hermes Agent (Port :9900)
  │
  ├── [Hermes → OpenCode] a2a_call / opencode_delegate
  │     ↓
  │   opencode-a2a Adapter (Port :8000)
  │     ↓ (REST / SSE)
  │   opencode serve (Port :4096)
  │     ↓
  │   Oh-My-OpenAgent (OMO Harness)
  │   (Sisyphus → Hephaestus, Oracle, Momus)
  │
  └── [OpenCode → Hermes] ask-hermes Skill
        ↓ (JSON-RPC A2A)
      Hermes Inbound Gateway (Port :9900)
      (Web Research, Mem0 Memory, User Escalation)
```

---

## 📦 Компоненты репозитория

| Компонент | Назначение | Расположение |
|---|---|---|
| **Hermes Plugin** (`opencode_a2a`) | Нативный инструмент `opencode_delegate` для вызова OpenCode из Hermes | `plugins/hermes/opencode_a2a/` |
| **OpenCode Skill** (`ask-hermes`) | Навык и CLI для вызова Hermes из OpenCode (поиск, память, вопросы) | `skills/opencode/ask-hermes/` |
| **A2A Python Client** | Легковесный клиент с поддержкой синхронных вызовов и SSE Streaming | `scripts/opencode_a2a_client.py` |
| **Примеры использования** | Скрипты синхронного и потокового делегирования | `examples/` |
| **Deep Research & Specs** | Полный отчет исследования стандарта A2A и аудита кода | `docs/deep-research-a2a.md` |

---

## 🚀 Быстрый старт

### 1. Предварительные требования
- Python 3.11+
- Node.js 20+ и `opencode-ai` (`npm install -g opencode-ai`)
- `uv tool install opencode-a2a`

### 2. Запуск сервисов OpenCode

```bash
# 1. Запуск headless runtime OpenCode
opencode serve --hostname 127.0.0.1 --port 4096

# 2. Запуск A2A шлюза OpenCode
A2A_STATIC_AUTH_CREDENTIALS='[{"scheme":"bearer","token":"your-secure-token","principal":"hermes"}]' \
OPENCODE_BASE_URL=http://127.0.0.1:4096 \
A2A_HOST=127.0.0.1 \
A2A_PORT=8000 \
OPENCODE_TIMEOUT=1800.0 \
OPENCODE_TIMEOUT_STREAM=1800.0 \
A2A_ALLOW_DIRECTORY_OVERRIDE=true \
opencode-a2a serve
```

### 3. Установка плагина в Hermes

Скопируйте директорию плагина в домашнюю папку Hermes:

```bash
mkdir -p ~/.hermes/plugins/
cp -r plugins/hermes/opencode_a2a ~/.hermes/plugins/
```

### 4. Установка навыка в OpenCode

Скопируйте скилл в конфигурацию OpenCode:

```bash
mkdir -p ~/.config/opencode/skills/
cp -r skills/opencode/ask-hermes ~/.config/opencode/skills/
```

---

## 💻 Примеры использования

### 1. Делегирование из Hermes в OpenCode (Python)

```python
from opencode_a2a_client import call_opencode, stream_opencode

# Синхронный вызов с таймаутом до 30 минут
result = call_opencode(
    message="Внедрить физику Rapier 3D и написать unit-тесты.",
    context_id="vholume-arena-milestone-2",
    directory="/home/user/projects/my-game",
    timeout=1800
)

print("Статус:", result["state"])
print("Отчет:", result["output"])
```

### 2. Живой SSE-стриминг (Streaming Events)

```python
for event in stream_opencode(
    message="Провести рефакторинг и запустить cargo test",
    context_id="vholume-arena-milestone-2",
    directory="/home/user/projects/my-game",
    on_event=lambda e: print("[Event]", e.get("type"))
):
    pass
```

### 3. Обратный вызов из OpenCode в Hermes (Bash / Skill)

Когда агент Sisyphus или Hephaestus работает над задачей и нуждается в данных из интернета или памяти:

```bash
python3 ~/.config/opencode/skills/ask-hermes/scripts/ask_hermes.py \
  "Найди документацию по Rapier 3D CCD для WASM и выдели ключевые функции"
```

---

## ⚙️ Решение критических узких мест (Grill-Me Architecture)

1. **Защита от таймаутов (120s Drop Fix):**
   - Параметры `OPENCODE_TIMEOUT=1800.0` и `OPENCODE_TIMEOUT_STREAM=1800.0` устраняют падение при долгой компиляции Rust/WASM и прогоне тестов.
2. **Изоляция сессий (`context_id` per Milestone):**
   - Сессии изолируются по границам задач (`<project>-milestone-<N>`), предотвращая раздувание контекста LLM (Context Ballooning) и перерасход токенов.
3. **Очистка зомби-процессов:**
   - При отмене задачи (`CancelTask`) процессы завершаются по Process Group ID (`kill(-pgid)`), не оставляя висячих фоновых сборок.

---

## 📄 Лицензия

MIT License (c) 2026 Denis & Contributors
