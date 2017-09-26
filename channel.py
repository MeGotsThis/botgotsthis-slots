﻿import asyncio
import random
from datetime import datetime, timedelta  # noqa: F401
from typing import Dict, Optional, List, cast  # noqa: F401

from bot import utils
from lib import database
from lib.data import ChatCommandArgs
from lib.helper.chat import cooldown, feature
from . import library


@feature('slots')
async def commandSlots(args: ChatCommandArgs) -> bool:
    if 'slotsLock' not in args.chat.sessionData:
        args.chat.sessionData['slotsLock'] = asyncio.Lock()
    lock: asyncio.Lock = args.chat.sessionData['slotsLock']

    if lock.locked():
        utils.whisper(args.nick, f'Channel cooldown (3.0 seconds)')
        return True

    with await lock:
        isBot: bool = await library.isSlotBots(
            args.database, args.chat.channel, args.nick,
            args.timestamp - library.unbotCooldown)
        lastAttempt: datetime = await library.getLastTwitchSlotsUser(
            args.database, args.chat.channel, args.nick)
        if await library.in_cooldown(args.database, args.chat.channel,
                                     args.nick, args.timestamp, lastAttempt,
                                     isBot):
            return False

        lastAttempts: List[datetime]
        lastAttempts = await library.getLastTwitchSlotsAttempts(
            args.database, args.chat.channel, args.nick,
            args.timestamp - library.logBotAttempts)
        markedBot: Optional[bool] = await library.process_bot(
            args.database, args.chat.channel, args.nick, args.timestamp,
            lastAttempt, isBot, lastAttempts)

        emotes: Optional[Dict[int, str]] = library.generate_twitch_pool()
        length: int = 3
        emoteIds: List[int] = list(emotes.keys())
        selected: List[int] = [random.choice(emoteIds) for _ in range(length)]

        matchEmoteId: int = selected[0]
        numMatching: int = 0
        emoteId: int
        for emoteId in selected:
            if emoteId == matchEmoteId:
                numMatching += 1
        allMatching: bool = numMatching == 3

        selectedEmotes: str = ' | '.join(emotes[i] for i in selected)
        msg: str = f'{args.nick} -> {selectedEmotes}'
        args.chat.send(msg)
        if allMatching:
            args.chat.send(f'{args.nick} has won !slots')
            if matchEmoteId == 25 and args.permissions.chatModerator:
                args.chat.send(f'.timeout {args.nick} 1')
                args.chat.send('Thanks for winning the Kappa!')
                db_: database.Database
                async with database.get_database(
                        database.Schema.Timeout) as db_:
                    db: database.DatabaseTimeout = cast(
                        database.DatabaseTimeout, db_)
                    await db.recordTimeout(
                        args.chat.channel, args.nick, None, 'slots', None, 1,
                        str(args.message), msg)
        if markedBot is True:
            args.chat.send(f'''\
{args.nick} is now considered as a bot. His cooldown is increased to 20 \
minutes.''')
        if markedBot is False:
            args.chat.send(f'''\
{args.nick} is now considered not as a bot. His cooldown is back to 2 \
minutes.''')

        await library.recordTwitchSlots(args.database, args.chat.channel,
                                        args.nick, emotes, selected)
        return True


@feature('slots')
@cooldown(timedelta(seconds=15), 'slots', 'moderator')
async def commandSlotWinners(args: ChatCommandArgs) -> bool:
    args.chat.send(f'''\
Slots Winners: \
http://megotsthis.com/botgotsthis/t/{args.chat.channel}/twitch-slots''')
    return True


@feature('ffzslots')
async def commandFfzSlots(args: ChatCommandArgs) -> bool:
    if 'slotsLock' not in args.chat.sessionData:
        args.chat.sessionData['slotsLock'] = asyncio.Lock()
    lock: asyncio.Lock = args.chat.sessionData['slotsLock']

    if lock.locked():
        utils.whisper(args.nick, f'Channel cooldown (3.0 seconds)')
        return True

    with await lock:
        isBot: bool = await library.isSlotBots(
            args.database, args.chat.channel, args.nick,
            args.timestamp - library.unbotCooldown)
        lastAttempt: datetime = await library.getLastFfzSlotsUser(
            args.database, args.chat.channel, args.nick)
        if await library.in_cooldown(args.database, args.chat.channel,
                                     args.nick, args.timestamp, lastAttempt,
                                     isBot):
            return False

        lastAttempts: List[datetime]
        lastAttempts = await library.getLastFfzSlotsAttempts(
            args.database, args.chat.channel, args.nick,
            args.timestamp - library.logBotAttempts)
        markedBot: Optional[bool] = await library.process_bot(
            args.database, args.chat.channel, args.nick, args.timestamp,
            lastAttempt, isBot, lastAttempts)

        emotes: Dict[int, str] = library.generate_ffz_pool(args.chat)
        length: int = 3
        emoteIds: List[int] = list(emotes.keys())
        selected: List[int] = [random.choice(emoteIds) for _ in range(length)]

        numMatching: int = 0
        emoteId: int
        for emoteId in selected:
            if emoteId == selected[0]:
                numMatching += 1
        allMatching: bool = numMatching == 3

        selectedEmotes = ' | '.join(emotes[i] for i in selected)
        args.chat.send(f'{args.nick} -> {selectedEmotes}')
        if allMatching:
            args.chat.send(f'{args.nick} has won !ffzslots')
        if markedBot is True:
            args.chat.send(f'''\
{args.nick} is now considered as a bot. His cooldown is increased to 20 \
minutes.''')
        if markedBot is False:
            args.chat.send(f'''\
{args.nick} is now considered not as a bot. His \cooldown is back to 2 \
minutes.''')

        await library.recordFfzSlots(args.database, args.chat.channel,
                                     args.nick, emotes, selected)
        return True


@feature('ffzslots')
@cooldown(timedelta(seconds=15), 'slots', 'moderator')
async def commandFfzSlotWinners(args: ChatCommandArgs) -> bool:
    args.chat.send(f'''\
FFZ Slots Winners: \
http://megotsthis.com/botgotsthis/t/{args.chat.channel}/ffz-slots''')
    return True


@feature('bttvslots')
async def commandBttvSlots(args: ChatCommandArgs) -> bool:
    if 'slotsLock' not in args.chat.sessionData:
        args.chat.sessionData['slotsLock'] = asyncio.Lock()
    lock: asyncio.Lock = args.chat.sessionData['slotsLock']

    if lock.locked():
        utils.whisper(args.nick, f'Channel cooldown (3.0 seconds)')
        return True

    with await lock:
        isBot: bool = await library.isSlotBots(
            args.database, args.chat.channel, args.nick,
            args.timestamp - library.unbotCooldown)
        lastAttempt = await library.getLastBttvSlotsUser(
            args.database, args.chat.channel, args.nick)
        if await library.in_cooldown(args.database, args.chat.channel,
                                     args.nick, args.timestamp, lastAttempt,
                                     isBot):
            return False

        lastAttempts: List[datetime]
        lastAttempts = await library.getLastBttvSlotsAttempts(
            args.database, args.chat.channel, args.nick,
            args.timestamp - library.logBotAttempts)
        markedBot: Optional[bool] = await library.process_bot(
            args.database, args.chat.channel, args.nick, args.timestamp,
            lastAttempt, isBot, lastAttempts)

        emotes: Dict[str, str] = library.generate_bttv_pool(args.chat)
        length: int = 3
        emoteIds: List[str] = list(emotes.keys())
        selected: List[str] = [random.choice(emoteIds) for _ in range(length)]

        numMatching: int = 0
        emoteId: str
        for emoteId in selected:
            if emoteId == selected[0]:
                numMatching += 1
        allMatching: bool = numMatching == 3

        selectedEmotes: str = ' | '.join(emotes[i] for i in selected)
        args.chat.send(f'{args.nick} -> {selectedEmotes}')
        if allMatching:
            args.chat.send(f'{args.nick} has won !bttvlots')
        if markedBot is True:
            args.chat.send(f'''\
{args.nick} is now considered as a bot. His cooldown is increased to 20 \
minutes.''')
        if markedBot is False:
            args.chat.send(f'''\
{args.nick} is now considered not as a bot. His cooldown is back to 2 \
minutes.''')

        await library.recordBttvSlots(args.database, args.chat.channel,
                                      args.nick, emotes, selected)
        return True


@feature('bttvslots')
@cooldown(timedelta(seconds=15), 'slots', 'moderator')
async def commandBttvSlotWinners(args: ChatCommandArgs) -> bool:
    args.chat.send(f'''\
Slot Winners: \
http://megotsthis.com/botgotsthis/t/{args.chat.channel}/bttv-slots''')
    return True
