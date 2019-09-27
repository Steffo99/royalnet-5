from .debug_error import DebugErrorCommand
from .debug_keyboard import DebugKeyboardCommand
from .debug_invoking import DebugInvokingCommand


commands = [
    DebugErrorCommand,
    DebugKeyboardCommand,
    DebugInvokingCommand,
]


__all__ = [command.__name__ for command in commands]
