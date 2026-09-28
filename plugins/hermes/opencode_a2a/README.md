# Hermes ↔ OpenCode A2A Bridge

Двунаправленная интеграция между **Hermes Agent** (Nous Research) и **OpenCode + Oh-My-OpenAgent (OMO)** по официальному протоколу **Agent-to-Agent (A2A)** от Linux Foundation & Google.

---

## Архитектура

```
                       Пользователь (Telegram / CLI / Desktop)
                                         ↓
                                    Hermes Agent
                      (Оркестратор, Deep Research, Mem0/Qdrant)
                                   Port :9900
                                  ↗          ↘
           (ask-hermes A2A call) ↗            ↘ (opencode_delegate A2A call)
                                ↗              ↘
                        OpenCode A2A Adapter (:8000)
                                       ↓
                           OpenCode Server (:4096)
                                       ↓
                          Oh-My-OpenAgent (OMO Harness)
                      (Sisyphus → Hephaestus, Oracle, Momus)
```

---

## Возможности

1. **Hermes → OpenCode (`opencode_delegate`):**
   - Нативное делегирование многофайлового кодинга, рефакторинга и сборок.
   - Изоляция сессий по вехам (`context_id`).
   - Расширенный таймаут (1800 с) и SSE-стриминг событий.

2. **OpenCode → Hermes (`ask-hermes` skill):**
   - Доступ агентов OMO (Sisyphus, Hephaestus, Oracle) к внешнему поиску в интернете, документации библиотек, постоянной памяти Mem0 и эскалации вопросов пользователю.

---

## Установка и запуск

### 1. Сервисы OpenCode
- `opencode serve --port 4096`
- `opencode-a2a serve --port 8000`

### 2. Подключение плагина к Hermes
Плагин помещается в `~/.hermes/plugins/opencode_a2a/`.

### 3. Подключение скилла к OpenCode
Скилл помещается в `~/.config/opencode/skills/ask-hermes/`.
