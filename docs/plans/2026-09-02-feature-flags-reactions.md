# Feature Flags para Reacciones

**Goal:** Permitir desactivar reacciones concretas (o todas) del bot por chat de Telegram, gestionadas en runtime por administradores con el comando `/reactions` y persistentes entre reinicios.

**Architecture:** Un `FeatureFlagStore` (dataclass picklable) vive en `application.bot_data` y se persiste con la `PicklePersistence` nativa de python-telegram-bot 22.5. El catálogo de flags se deriva del `ReactionRegistry` (los códigos de las reacciones son los nombres de los flags) más un flag extra `lo_que_escribis` para el aviso de estadísticas. Cada punto de emisión consulta el store antes de enviar.

**Infra:** El pickle se escribe en `PERSISTENCE_PATH` (por defecto `/data/bot_state.pickle`); `make run` / `run_detached` montan el volumen con nombre `comanditabot_data:/data`. El `docker run` de producción necesita el mismo volumen o el estado se pierde al recrear el contenedor.

## Flags

| Flag | Emisor | Descripción |
|---|---|---|
| `rajoy` | `RajoyReaction` | Frases de Rajoy ante "brey", "rajoy", "mariano" |
| `zapatero` | `ZapateroReaction` | Frases de Zapatero ante "zapatero", "zp" |
| `kids_alert` | `KidsAlertReaction` | Kids Alert! ante menciones de niños |
| `broken_group` | `BrokenGroupReaction` | "El grupo está roto" ante "estuve en", "fui a" |
| `digi` | `DigiReaction` | "Woof! Woof!" ante "digi" |
| `mimimi` | `MiMiMiReaction` | Traduce el mensaje a mimimi (1%) |
| `punishment` | `PunishmentReaction` | Sentencia ante URLs (10%) |
| `lo_que_escribis` | `ChatStatisticsMessageHandlerFactory` | Aviso de estadísticas al alcanzar el umbral diario |
| `all` | — | Kill switch: cubre todos los anteriores |

## Comando `/reactions`

- `/reactions` — estado del chat (abierto a todos)
- `/reactions list` — catálogo de códigos con descripciones (abierto a todos)
- `/reactions off|on <código>...` — toggle de códigos (solo admins; en privado, el propietario)
- `/reactions off|on all` — kill switch (solo admins); `on all` resetea también la disable-list

## Decisiones de diseño

1. **Los códigos del registry son la fuente de verdad**: cada nueva reacción registrada con `@ReactionRegistry.register(...)` aparece automáticamente como flag en `/reactions`. La descripción se declara como atributo de clase `description` en la propia reacción.
2. **Disable-list por chat**: por defecto todo activo; por chat se guardan los códigos deshabilitados + un kill switch `all_disabled`.
3. **`lo_que_escribis` no es una reacción**: vive en el catálogo con sección "Otros mensajes del bot". Al estar bloqueado se sigue contando mensajes (los datos de `/stats` no se corrompen); solo se salta el envío. El comando `/stats` nunca se ve afectado.
4. **Enforcement**:
   - `ReactionHandlerFactory.process` corta con el kill switch y pasa los códigos deshabilitados a `ReactionRegistry.process_message`, que salta esos registries antes de evaluar `trigger()`.
   - `ChatStatisticsMessageHandlerFactory.process` consulta `is_blocked(chat_id, "lo_que_escribis")`.
5. **Persistencia**: `PicklePersistence` con `update_interval=30`; el store se instancia de forma perezosa en `bot_data["feature_flags"]` vía `FeatureFlagStore.from_bot_data`.
6. **Guard de admin solo en escritura**: `ensure_chat_admin` compara el usuario contra `get_chat_administrators`; en chats privados se permite al propietario.

## Tests

`tests/test_feature_flags.py` cubre: store (disable/enable/kill switch/reset, `from_bot_data`), catálogo (códigos = registry + `lo_que_escribis`, descripciones), comando (status, list, guard de admin, toggles, kill switch, códigos desconocidos, usage), enforcement en reacciones y en el aviso de estadísticas.
