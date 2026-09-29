# Сводный отчет Deep Research: Диагностика, Архитектура и План устранения проблем A2A-моста (Hermes ↔ OpenCode / OMO)

## 1. Сквозная архитектура
Взаимодействие построено на двух встречных A2A v1.0 каналах:
- **Прямой канал (Hermes ➔ OpenCode / OMO):**
  `Hermes Agent (Builder)` ➔ `plugin: opencode_delegate` ➔ `HTTP A2A Gateway (:8000)` ➔ `OpenCode Server (:4096)` ➔ `OMO Sisyphus/Hephaestus` ➔ `OmniRoute (:20128)`.
- **Обратный канал (OMO ➔ Hermes):**
  `OMO Agent` ➔ `skill: ask-hermes (ask_hermes.py)` ➔ `JSON-RPC A2A (:9900)` ➔ `Hermes Top-Level Router` ➔ `Mem0 / User Telegram`.

---

## 2. Полный каталог выявленных багов и технических недостатков

### Группа A: Прямой клиент `client.py` (`opencode_delegate`)
1. **Отсутствие передачи директории через протокол:**
   - *Было:* Передавалось только текстом `In /path: ...`.
   - *Дефект:* OpenCode оставался в дефолтной директории адаптера (`/home/ayos`).
   - *Решение:* Передавать `metadata.opencode.directory` с обязательным заголовком `A2A-Extensions: urn:opencode-a2a:extension:session-binding:v1`.
2. **Блокирующий вызов без возможности отмены:**
   - *Было:* `urlopen()` блокировался на 1800 с. При обрыве/таймауте `task_id` терялся, OpenCode продолжал работать вхолостую.
   - *Решение:* Запрашивать `configuration={"returnImmediately": True}`, немедленно фиксировать `task_id`, опрашивать `GET /tasks/{id}` с заголовком `A2A-Version: 1.0` и адаптивным интервалом (1–3 с). При таймауте посылать `POST /tasks/{id}:cancel`.
3. **Потеря деталей ошибок и прерываний (`interrupts`):**
   - *Было:* При HTTPError брался только `str(e)` (например, `HTTP Error 400`), тело ответа с реальной причиной отбрасывалось. Все не-`COMPLETED` статусы схлопывались в `success: False`.
   - *Решение:* Читать `e.read().decode("utf-8")`, парсить JSON-ошибку (`message`, `details`), извлекать `status.message`, распознавать `TASK_STATE_INPUT_REQUIRED` и `TASK_STATE_FAILED`.
4. **Засорение контекста сырыми данными (`raw`):**
   - *Было:* `raw: data` возвращался в результат инструмента Hermes.
   - *Решение:* Исключить `raw` из ответа инструмента, возвращать только лаконичные поля (`success`, `state`, `task_id`, `context_id`, `output`, `error`).
5. **Заголовки версии A2A:**
   - *Было:* Заголовки `A2A-Version: 1.0` отсутствовали, из-за чего поллинг падал с ошибкой `A2A version '0.3' is not supported`.
   - *Решение:* Передавать `A2A-Version: 1.0` во всех HTTP-запросах к адаптеру.

---

### Группа B: Обратный клиент `ask_hermes.py` (`ask-hermes`)
1. **Устаревший формат диалекта A2A 0.3:**
   - *Было:* `role: "user"`, `parts: [{"type": "text", "text": ...}]`.
   - *Решение:* Привести к стандарту A2A v1.0 (`role: "ROLE_USER"`, `parts: [{"text": ...}]`), совпадающему со спецификацией сервера Hermes `:9900`.
2. **Некорректная обработка ошибок (код выхода 0):**
   - *Было:* Ошибки сети и парсинга писались в `stdout`, а скрипт завершался с exit code `0`. OMO принимал текст ошибки за ответ от Hermes.
   - *Решение:* Писать ошибки в `sys.stderr` и завершать процесс с кодом `sys.exit(1)`.
3. **Неподходящий таймаут для Telegram-эскалаций:**
   - *Было:* Жесткий таймаут 180 с.
   - *Решение:* Конфигурируемый таймаут через `HERMES_A2A_TIMEOUT` (дефолт 300 с для памяти, до 1800 с для вопросов человеку), разделение сетевой недоступности (`ECONNREFUSED`) и ожидания ответа.
4. **Конфигурация через окружение и безопасность:**
   - *Было:* Захардкоженный URL без токена.
   - *Решение:* Чтение `HERMES_A2A_URL` и `HERMES_A2A_TOKEN` из `os.environ`, экранирование недоверенного вывода от OMO.

---

### Группа C: Документация и Навыки (`SKILL.md`, `README.md`)
1. **Неточность роли Momus в `SKILL.md`:**
   - *Было:* Указан в списке исполнителей кода («Тяжелое написание кода...»).
   - *Решение:* Уточнить роль Momus как Adversarial Reviewer (рецензирование кода, проверка DoD и блокировка сдачи при ошибках).
2. **Правила надежности в `SKILL.md`:**
   - Добавить правило: «при ошибке или таймауте не гадать, а остановиться и зафиксировать это в отчете».
   - Добавить лимит обращений (максимум 3 вопроса к человеку за один контекст).
3. **Документация `README.md`:**
   - Задокументировать все переменные окружения: `OPENCODE_A2A_URL`, `OPENCODE_A2A_TOKEN`, `OPENCODE_A2A_TIMEOUT`, `HERMES_A2A_URL`, `HERMES_A2A_TOKEN`.
   - Привести схемы к A2A v1.0.

---

## 3. План реализации (Fix Plan)
1. **Шаг 1:** Обновить `plugins/hermes/opencode_a2a/client.py` (поддержка `metadata.opencode.directory`, `A2A-Version`, `A2A-Extensions`, `returnImmediately`, асинхронный поллинг, отмена по таймауту, парсинг тела HTTPError, очистка от `raw`).
2. **Шаг 2:** Обновить `skills/opencode/ask-hermes/scripts/ask_hermes.py` (формат A2A v1.0, вывод ошибок в stderr с exit code 1, поддержка `HERMES_A2A_URL` / `HERMES_A2A_TOKEN`, таймаут).
3. **Шаг 3:** Обновить `skills/opencode/ask-hermes/SKILL.md` и `skills/hermes/omo-agents-guide/SKILL.md` (роли агентов, запрет галлюцинаций, лимит вопросов, режим `ultrawork`).
4. **Шаг 4:** Обновить `README.md` в репозитории `hermes-opencode-a2a` (документация env-переменных, A2A v1.0, интерактивные прерывания).
5. **Шаг 5:** Написать юнит-тесты (`tests/test_client.py`, `tests/test_ask_hermes.py`) с моками и сквозными тестами.
6. **Шаг 6:** Синхронизировать рабочие файлы в `~/.hermes/plugins/opencode_a2a/` и `~/.config/opencode/skills/ask-hermes/`.
7. **Шаг 7:** Прогнать полный тестовый сьют и выполнить коммит/пуш в GitHub репозиторий.
