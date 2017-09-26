from typing import Iterable, Mapping, Optional

from lib.data import ChatCommand

from .. import channel


def filterMessage() -> Iterable[ChatCommand]:
    return []


def commands() -> Mapping[str, Optional[ChatCommand]]:
    if not hasattr(commands, 'commands'):
        setattr(commands, 'commands', {
            '!slots': channel.commandSlots,
            '!slotswinners': channel.commandSlotWinners,
            '!ffzslots': channel.commandFfzSlots,
            '!ffzslotswinners': channel.commandFfzSlotWinners,
            '!bttvslots': channel.commandBttvSlots,
            '!bttvslotswinners': channel.commandBttvSlotWinners,
            }
        )
    return getattr(commands, 'commands')


def commandsStartWith() -> Mapping[str, Optional[ChatCommand]]:
    return {}


def processNoCommand() -> Iterable[ChatCommand]:
    return []
