from telegram import Update
from telegram.ext import CommandHandler, CallbackContext


class BaseCommandHandler(CommandHandler):
    COMMAND_NAME = None

    def __init__(self, *args, **kwargs):
        if self.COMMAND_NAME is None:
            raise NotImplementedError("'COMMAND_NAME' has wrong value.")
        super().__init__(self.COMMAND_NAME, self.process, *args, **kwargs)

    async def process(self, update: Update, context: CallbackContext):
        raise NotImplementedError("'process' method is not implemented!")
