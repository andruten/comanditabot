from telegram import Update
from telegram.ext import CallbackContext

from commands.base import BaseCommandHandler

from .admin import ensure_chat_admin
from .catalog import SECTION_MESSAGES, SECTION_REACTIONS, flag_catalog
from .store import FeatureFlagStore

USAGE_TEXT = (
    "Uso:\n"
    "/reactions — estado de las reacciones en este chat\n"
    "/reactions list — códigos disponibles\n"
    "/reactions off <código>... — desactivar en este chat\n"
    "/reactions on <código>... — activar en este chat\n"
    "/reactions off all — desactivar todo en este chat\n"
    "/reactions on all — reactivar todo en este chat"
)

NOT_ADMIN_TEXT = "Solo los administradores del chat pueden cambiar esto."

UNKNOWN_CODES_TEXT = (
    "Código desconocido: {codes}. Usa /reactions list para ver los disponibles."
)

ALL_CODES = "all"

SECTION_TITLES = {
    SECTION_REACTIONS: "Reacciones:",
    SECTION_MESSAGES: "Otros mensajes del bot:",
}

KILL_SWITCH_OFF_TEXT = (
    "🚫 Todas las reacciones y avisos del bot están desactivados en este chat."
)
KILL_SWITCH_ON_TEXT = "✅ Reacciones y avisos del bot reactivados en este chat."

SECTIONS = (SECTION_REACTIONS, SECTION_MESSAGES)


class ReactionsFlagCommandHandler(BaseCommandHandler):
    COMMAND_NAME = "reactions"

    async def process(self, update: Update, context: CallbackContext):
        args = context.args or []
        if not args:
            await self._reply(
                update, self._render_status(context, update.effective_chat.id)
            )
        elif args[0] == "list":
            await self._reply(update, self._render_catalog())
        elif args[0] in ("on", "off"):
            await self._toggle(update, context, enable=args[0] == "on", codes=args[1:])
        else:
            await self._reply(update, USAGE_TEXT)

    async def _toggle(
        self,
        update: Update,
        context: CallbackContext,
        *,
        enable: bool,
        codes: list[str],
    ) -> None:
        if not codes:
            await self._reply(update, USAGE_TEXT)
            return
        if not await ensure_chat_admin(update, context):
            await self._reply(update, NOT_ADMIN_TEXT)
            return
        store = FeatureFlagStore.from_bot_data(context)
        chat_id = update.effective_chat.id
        if ALL_CODES in codes:
            if len(codes) > 1:
                await self._reply(update, USAGE_TEXT)
                return
            if enable:
                store.enable_all(chat_id)
                await self._reply(update, KILL_SWITCH_ON_TEXT)
            else:
                store.disable_all(chat_id)
                await self._reply(update, KILL_SWITCH_OFF_TEXT)
            return
        known_codes = {flag.code for flag in flag_catalog()}
        unknown_codes = sorted(set(codes) - known_codes)
        if unknown_codes:
            await self._reply(
                update,
                UNKNOWN_CODES_TEXT.format(codes=", ".join(unknown_codes)),
            )
            return
        if enable:
            store.enable(chat_id, set(codes))
        else:
            store.disable(chat_id, set(codes))
        await self._reply(update, self._render_status(context, chat_id))

    def _render_status(self, context: CallbackContext, chat_id: int) -> str:
        store = FeatureFlagStore.from_bot_data(context)
        lines = []
        if store.all_disabled(chat_id):
            lines.append(
                "🚫 Kill switch activo: todo desactivado (usa /reactions on "
                "all para reactivar)."
            )
        for section in SECTIONS:
            lines.append(SECTION_TITLES[section])
            for flag in flag_catalog():
                if flag.section != section:
                    continue
                mark = "❌" if store.is_blocked(chat_id, flag.code) else "✅"
                lines.append(f"{mark} {flag.code} — {flag.description}")
        return "\n".join(lines)

    def _render_catalog(self) -> str:
        lines = ["Códigos disponibles (usa /reactions on|off <código>):"]
        for section in SECTIONS:
            lines.append(SECTION_TITLES[section])
            for flag in flag_catalog():
                if flag.section == section:
                    lines.append(f"{flag.code} — {flag.description}")
        return "\n".join(lines)

    async def _reply(self, update: Update, text: str) -> None:
        await update.effective_message.reply_text(text)
