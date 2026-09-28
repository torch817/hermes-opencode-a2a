# Deep Research: Архитектура и интеграция A2A (Agent-to-Agent Protocol) с OpenCode и OMO

**Дата исследования:** 28 сентября 2026 г.  
**Исследователи:** Hermes Agent (Boba) + Parallel Deep Research Subagents  
**Статус артефакта:** Production-Grade Technical Specification & Architecture Review

---

## 1. Спецификация протокола Linux Foundation / Google A2A (v1.0.0)

### 1.1. Концепция и позиционирование
В то время как **MCP (Model Context Protocol)** стандартизирует взаимодействие уровня *Agent-to-Tool* (подключение БД, файловых систем, утилит), **A2A (Agent-to-Agent Protocol)** стандартизирует уровень *Agent-to-Agent* — безопасную, многоагентную оркестрацию между гетерогенными автономными агентами, работающими на разных рантаймах, стеках и языках программирования.

### 1.2. Базовая модель данных (Core Data Model)
* **Agent Card (`.well-known/agent-card.json`):** Манифест агента. Описывает метаданные, возможности (capabilities), поддерживаемые протоколы (`HTTP+JSON`, `JSON-RPC`, `gRPC`), схемы авторизации (Bearer, Mutual TLS), навыки (skills) и ограничения.
* **Task (Задача):** Единица распределенной работы с уникальным жизненным циклом. Содержит метаданные, статус, историю сообщений, сгенерированные артефакты (файлы, диффы, логи).
* **Context (`context_id`):** Глобальный идентификатор связности диалога/проекта. Позволяет агентам сохранять контекст, долгосрочную память и сессию выполнения на протяжении сотен обращений.
* **Message & Parts:** Структурированное сообщение. Включает роли (`ROLE_USER`, `ROLE_AGENT`), идентификаторы и массив `parts` (текст, бинарные данные, вызовы инструментов, ссылки на артефакты).
* **Artifacts:** Результаты выполнения задачи (созданные/измененные файлы, отчеты, бинарные сборки).

### 1.3. Конечный автомат задачи (Task State Machine)
Жизненный цикл задачи в A2A строго формализован:

* `TASK_STATE_SUBMITTED` — задача принята к исполнению диспетчером.
* `TASK_STATE_WORKING` — агент активно выполняет шаги, запускает инструменты или компилирует код.
* `TASK_STATE_INPUT_REQUIRED` — агент приостановил выполнение и ожидает решения от вызывающего агента (подтверждение опасной операции, ответ на уточняющий вопрос).
* `TASK_STATE_COMPLETED` — финальное успешное состояние, сформированы артефакты.
* `TASK_STATE_FAILED` — фатальная ошибка выполнения (таймаут, падение компилятора, сетевой сбой).
* `TASK_STATE_CANCELED` — задача принудительно остановлена клиентом (`CancelTask`).

### 1.4. Модели транспорта и стриминга (Transports & SSE)
1. **REST / HTTP+JSON:**
   - `POST /message:send` — синхронная отправка сообщения с блокирующим ожиданием завершения.
   - `POST /message:stream` — Server-Sent Events (SSE) поток чанков и прогресса в реальном времени.
   - `GET /tasks/{id}` — асинхронный поллинг статуса и артефактов задачи.
   - `GET /tasks/{id}:subscribe` — SSE-подписка на события уже запущенной задачи.
   - `POST /tasks/{id}:cancel` — отправка сигнала отмены.
2. **JSON-RPC 2.0:**
   - Методы: `tasks/send`, `tasks/sendStreaming`, `tasks/get`, `tasks/cancel`.
3. **gRPC / Protocol Buffers:**
   - Бинарный транспорт для высоконагруженных enterprise-инсталляций с двунаправленным стримингом.

---

## 2. Архитектура интеграции OpenCode + OMO через A2A

### 2.1. Трехуровневый стек исполнения
```
Пользователь / Внешние события (Telegram / CLI)
  ↓
Hermes Agent (Top-level Orchestrator, Port 9900)
  ↓ [A2A Protocol: Bearer Token, context_id]
opencode-a2a Adapter (Gateway Proxy, Port 8000)
  ↓ [OpenCode REST & SSE APIs]
opencode serve (Headless Coding Runtime, Port 4096)
  ↓ [Plugin Architecture]
Oh-My-OpenAgent (OMO Multi-Agent Harness)
  ├─ Sisyphus (Ultraworker & Task Orchestrator)
  ├─ Hephaestus (Deep Coding & Rust/TS Implementation)
  ├─ Oracle & Momus (Architecture Advisory & Code Review)
  └─ LSP Daemon & MCP Servers (AST-Grep, Rust Analyzer, TS Server)
```

### 2.2. Механика сессий и Session Continuity (`context_id`)
* При первом вызове с уникальным `context_id` (например, `proj-vholume-arena-m2`), A2A-адаптер создает новую сессию в OpenCode через `POST http://127.0.0.1:4096/session?directory=/path`.
* Внутренняя связка `context_id ↔ opencode_session_id` сохраняется в локальной SQLite базе `~/.local/share/opencode-a2a/opencode-a2a.db`.
* При повторных вызовах с тем же `context_id` адаптер автоматически направляет запрос в существующую сессию `POST /session/{id}/message`, сохраняя непрерывную историю рассуждений и контекст проекта без повторной передачи всех исходников.

### 2.3. Поведение OMO (Oh-My-OpenAgent) в режиме `serve`
* OMO инициализируется как нативный плагин OpenCode (`~/.config/opencode/opencode.json` и `~/.omo/omo.jsonc`).
* В режиме `opencode serve` OMO работает идентично CLI-режиму: регистрирует всех sub-agents (`Sisyphus`, `Hephaestus`, `Explore`, `Compaction`), запускает LSP-демон (`lsp-daemon/dist/cli.js`) и использует умную маршрутизацию моделей через локальный OmniRoute шлюз.
* **Prompt Cache Locality:** За счет сохранения сессий в OpenCode upstream-кэш контекста Gemini (Antigravity/OmniRoute) переиспользуется на 85–95%, что снижает задержки и экономит токенные лимиты.

---

## 3. Детальный разбор внутренней реализации `opencode-a2a`

### 3.1. Клиентский модуль (`opencode_upstream_client.py`)
* Построен на базе асинхронного `httpx.AsyncClient`.
* Управляет жизненным циклом сессий, проверкой доступности (`GET /project`), передачей оверрайдов рабочих директорий (`directory` query param) и разбором SSE-потока OpenCode (`GET /event`).
* Преобразует внутренние ошибки OpenCode в структурированные A2A Error Codes (`UpstreamTimeoutError`, `UpstreamContractError`).

### 3.2. Координатор и исполнитель (`execution/coordinator.py`, `executor.py`)
* **Coordinator:** Разрешает привязку сессий, проверяет наличие активных блокировок, выбирает режим выполнения (streaming vs blocking non-streaming).
* **Executor:** Отвечает за трансляцию A2A-сообщений в формат `parts` OpenCode, выполнение шагов, перехват `tool_calls` и формирование итогового артефакта `OpencodeMessage`.
* **Interrupt Engine (`jsonrpc/handlers/interrupt_*`):** Обрабатывает интерактивные запросы (подтверждение прав доступа `replyPermission` и ответы на вопросы `replyQuestion`).

### 3.3. Таймауты и критические узкие места (Bottlenecks)
1. **Синхронный HTTP-таймаут (120 секунд):**
   - *Проблема:* По умолчанию `OPENCODE_TIMEOUT` составлял 120.0 с. При выполнении сложных задач Sisyphus с компиляцией Rust/WASM или тяжелыми тестами A2A адаптер преждевременно обрывал соединение со статусом `TASK_STATE_FAILED: OpenCode request timed out`.
   - *Решение:* Параметр `OPENCODE_TIMEOUT=1800.0` (30 минут) и `OPENCODE_TIMEOUT_STREAM=1800.0` задан в `/home/ayos/.config/opencode-a2a/env`.
2. **Idle Stream Timeout:**
   - *Проблема:* Если агент долго молчит (например, идет сборка крейта `cargo build --release`), SSE-стрим мог закрыться по неактивности.
   - *Решение:* `A2A_STREAM_IDLE_TIMEOUT_SECONDS=1800.0` и `A2A_STREAM_MAX_DURATION_SECONDS=7200.0`.
3. **Отслеживание прогресса:**
   - Для длительных задач клиенту рекомендуется использовать `POST /message:stream` (SSE) либо фоновый поллинг `GET /tasks/{task_id}`.

---

## 4. Рекомендации по эксплуатации

1. **Для быстрых задач (<2 минут):** Использовать синхронный метод `call_opencode(...)` с увеличенным таймаутом.
2. **Для крупных вех и рефакторинга (>3 минут):** Использовать стриминговый вызов `stream_opencode(...)` или асинхронный запуск с поллингом статуса задачи по `task_id`.
3. **Безопасность и изоляция:**
   - Сервисы привязаны к локальному интерфейсу `127.0.0.1`.
   - Внешние туннели отключены.
   - Межагентная авторизация защищена статическим токеном `Bearer`.
