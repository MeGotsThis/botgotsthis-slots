import asyncio
import random
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple  # noqa: F401

import aioodbc.cursor  # noqa: F401

from bot import data, utils  # noqa: F401
from lib.cache import CacheStore
from lib.database import DatabaseMain


basicEmotes: Set[str] = {
    ':)', ':(', ':D', '>(', ':z', 'o_O', 'B)', ':o', '<3', ':\\', ';)', ':P',
    ';P', 'R)',
    }
extraKappaEmotes: Set[str] = {'Keepo', 'MiniK'}
catEmotes: Set[str] = {
    'BionicBunion', 'Kippa', 'Keepo', 'RitzMitz', 'mcaT', 'CoolCat'
    }
dogEmotes: Set[str] = {'FrankerZ', 'RalpherZ', 'CorgiDerp', 'OhMyDog'}

channelCooldown: timedelta = timedelta(seconds=3)
attemptCooldown: timedelta = timedelta(seconds=120)
botCooldown: timedelta = timedelta(minutes=20)
unbotCooldown: timedelta = timedelta(hours=1)
logBotAttempts: timedelta = timedelta(hours=2)


async def isSlotBots(
        database: DatabaseMain,
        broadcaster: str,
        user: str,
        timestamp: datetime) -> bool:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
SELECT 1 FROM slot_bots WHERE broadcaster=? AND bot=? AND marked>=?
'''
        await cursor.execute(query, (broadcaster, user, timestamp))
        return bool(await cursor.fetchone())


async def markSlotBots(
        database: DatabaseMain,
        broadcaster: str,
        user: str,
        timestamp: datetime) -> bool:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str
        params: Tuple[Any, ...]
        if database.isSqlite:
            query = '''
REPLACE INTO slot_bots (broadcaster, bot, marked) VALUES (?, ?, ?)
'''
            params = broadcaster, user, timestamp
        else:
            query = '''
INSERT INTO slot_bots (broadcaster, bot, marked) VALUES (?, ?, ?)
    ON CONFLICT ON CONSTRAINT slot_bots_pkey
    DO UPDATE SET marked=?
        '''
            params = broadcaster, user, timestamp, timestamp, timestamp
        await cursor.execute(query, params)
        return cursor.rowcount != 0


async def getLastSlots(database: DatabaseMain, broadcaster: str) -> datetime:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str
        if database.isSqlite:
            query = '''
SELECT MAX(attemptTime) AS "[timestamp]"
    FROM (
        SELECT MAX(attemptTime) AS attemptTime
            FROM slot_attempts
            WHERE broadcaster=?
        UNION
        SELECT MAX(attemptTime) FROM ffz_slot_attempts WHERE broadcaster=?
        UNION
        SELECT MAX(attemptTime) FROM bttv_slot_attempts WHERE broadcaster=?)
'''
        else:
            query = '''
SELECT MAX(attemptTime)
    FROM (
        SELECT MAX(attemptTime) AS attemptTime
            FROM slot_attempts
            WHERE broadcaster=?
        UNION
        SELECT MAX(attemptTime) FROM ffz_slot_attempts WHERE broadcaster=?
        UNION
        SELECT MAX(attemptTime) FROM bttv_slot_attempts WHERE broadcaster=?
        ) AS a
'''
        await cursor.execute(query, (broadcaster,) * 3)
        return (await cursor.fetchone() or [None])[0] or datetime.min


async def in_cooldown(
        database: DatabaseMain,
        channel: str,
        nick: str,
        timestamp: datetime,
        lastAttempt: datetime,
        isBot: bool) -> bool:
    since: timedelta = timestamp - await getLastSlots(database, channel)
    cooldownLeft: float
    if since < channelCooldown:
        cooldownLeft = round((channelCooldown - since).total_seconds(), 1)
        utils.whisper(nick, f'Channel cooldown ({cooldownLeft:.1f} seconds)')
        return True

    cooldown: timedelta = attemptCooldown if not isBot else botCooldown
    since = timestamp - lastAttempt
    if since < cooldown:
        if not isBot:
            cooldownLeft = round((cooldown - since).total_seconds(), 1)
            utils.whisper(nick, f'Slots Cooldown ({cooldownLeft:.1f} seconds)')
        return True
    return False


async def process_bot(
        database: DatabaseMain,
        channel: str,
        nick: str,
        timestamp: datetime,
        lastAttempt: datetime,
        isBot: bool,
        attempts: List[datetime]) -> Optional[bool]:
    """
    Returns True if marked as bot, return False if unmarked, None otherwise
    """
    toMark: bool = False
    if timestamp - lastAttempt >= unbotCooldown:
        return False if isBot else None
    else:
        s: List[int] = []
        for i in range(1, len(attempts)):
            s.append(int((attempts[i] - attempts[i - 1]).total_seconds()))
        # < 2 seconds of variations
        if len(s) >= 5 and statistics.stdev(s) < 1:
            toMark = True
        # < 2 seconds of variations on the last 5
        if len(s) >= 5 and statistics.stdev(s[-5:]) < 1:
            toMark = True
        # < 10 seconds
        if len(s) >= 10 and statistics.stdev(s) < 3.5:
            toMark = True
        # < 30 seconds
        if len(s) >= 15 and statistics.stdev(s) < 10:
            toMark = True
    if toMark and not isBot:
        await markSlotBots(database, channel, nick, timestamp)
    return True if toMark else None


async def generate_twitch_pool(dataCache: CacheStore
                               ) -> Optional[Dict[int, str]]:
    emoteSets: Optional[Set[int]] = await dataCache.twitch_get_bot_emote_set()
    if emoteSets is None:
        return None
    if not await dataCache.twitch_load_emotes(emoteSets):
        return None
    emotes: Dict[int, str] = await dataCache.twitch_get_emotes()
    if len(emotes) < 8:
        return None
    if len(emotes) > 16:
        if 25 in emotes:
            del emotes[25]
        emotes = dict(random.sample(emotes.items(), 15))
        emotes[25] = 'Kappa'
    return emotes


async def getLastTwitchSlotsUser(
        database: DatabaseMain,
        broadcaster: str,
        user: str) -> datetime:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str
        if database.isSqlite:
            query = '''
SELECT MAX(attemptTime) AS "[timestamp]"
    FROM slot_attempts
    WHERE broadcaster=? AND twitchUser=?
'''
        else:
            query = '''
SELECT MAX(attemptTime)
    FROM slot_attempts
    WHERE broadcaster=? AND twitchUser=?
'''
        await cursor.execute(query, (broadcaster, user))
        return (await cursor.fetchone() or [None])[0] or datetime.min


async def getLastTwitchSlotsAttempts(
        database: DatabaseMain,
        broadcaster: str,
        user: str,
        timestamp: datetime) -> List[datetime]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
SELECT attemptTime
    FROM slot_attempts
    WHERE broadcaster=? AND twitchUser=? AND attemptTime>=?
    ORDER BY attemptTime ASC
'''
        return [attempt async for attempt,
                in await cursor.execute(query, (broadcaster, user, timestamp))]


async def recordTwitchSlots(
        database: DatabaseMain,
        dataCache: CacheStore,
        channel: str,
        nick: str,
        emotes: Dict[int, str],
        selectedIds: List[int]) -> None:
    emoteSets: Dict[int, int]
    maybeSets: Optional[Dict[int, int]]
    maybeSets = await dataCache.twitch_get_emote_sets()
    if maybeSets is not None:
        emoteSets = maybeSets
    else:
        emoteSets = {i: i for i in selectedIds}
    matchEmoteId: int = selectedIds[0]
    matchEmoteSetId: int = emoteSets[matchEmoteId]
    numMatching: int = 0
    numBasic: int = 0
    numKappa: int = 0
    numCat: int = 0
    numDog: int = 0
    numSub: int = 0
    emoteId: int
    for emoteId in selectedIds:
        if emoteId == matchEmoteId:
            numMatching += 1
        if emotes[emoteId] in basicEmotes:
            numBasic += 1
        if (emotes[emoteId] in extraKappaEmotes
                or 'kappa' in emotes[emoteId].lower()
                or 'klappa' in emotes[emoteId].lower()):
            numKappa += 1
        if emotes[emoteId] in catEmotes:
            numCat += 1
        if emotes[emoteId] in dogEmotes:
            numDog += 1
        if emoteSets[emoteId] == matchEmoteSetId:
            numSub += 1
    allMatching: bool = numMatching == 3
    allBasic: bool = numBasic == 3
    allKappa: bool = numKappa == 3
    allCat: bool = numCat == 3
    allDog: bool = numDog == 3
    allSub: bool = numSub == 3 and matchEmoteSetId != 0

    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str
        params: Tuple[Any, ...]
        query = '''
INSERT INTO slot_attempts
        (broadcaster, attemptTime, twitchUser, numMatching, isWin, emoticon1,
        emoticon2, emoticon3, emoticonId1, emoticonId2, emoticonId3,
        isBasicMatch, isKappaMatch, isCatMatch, isDogMatch, isSubscriberMatch)
    VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
'''
        params = (channel, nick, numMatching, allMatching,
                  emotes[selectedIds[0]], emotes[selectedIds[1]],
                  emotes[selectedIds[2]],
                  selectedIds[0], selectedIds[1], selectedIds[2],
                  allBasic, allKappa, allCat, allDog, allSub,)
        await cursor.execute(query, params)

        if allMatching:
            query = '''
INSERT INTO slot_winners
        (broadcaster, winningTime, winner, winningEmote, winningEmoteId)
    VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)
'''
            params = channel, nick, emotes[selectedIds[0]], selectedIds[0],
            await cursor.execute(query, params)

        await database.commit()


async def generate_ffz_pool(chat: 'data.Channel',
                            dataCache: CacheStore
                            ) -> Optional[Dict[int, str]]:
    async def getGlobal() -> Optional[Dict[int, str]]:
        if not await dataCache.ffz_load_global_emotes():
            return None
        return await dataCache.ffz_get_global_emotes()

    async def getBroadcaster() -> Optional[Dict[int, str]]:
        if not await dataCache.ffz_load_broadcaster_emotes(chat.channel):
            return None
        return await dataCache.ffz_get_broadcaster_emotes(chat.channel)

    globalEmotes: Optional[Dict[int, str]]
    chanEmotes: Optional[Dict[int, str]]
    globalEmotes, chanEmotes = await asyncio.gather(
        getGlobal(), getBroadcaster()
    )
    if globalEmotes is None or chanEmotes is None:
        return None
    emotes: Dict[int, str]
    emotes = dict(list(globalEmotes.items()) + list(chanEmotes.items()))
    if len(emotes) > 16:
        emotes = dict(random.sample(emotes.items(), 16))
    return emotes


async def getLastFfzSlotsUser(
        database: DatabaseMain,
        broadcaster: str,
        user: str) -> datetime:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str
        if database.isSqlite:
            query = '''
SELECT MAX(attemptTime) AS "[timestamp]"
    FROM ffz_slot_attempts
    WHERE broadcaster=? AND twitchUser=?
'''
        else:
            query = '''
SELECT MAX(attemptTime)
    FROM ffz_slot_attempts
    WHERE broadcaster=? AND twitchUser=?
'''
        await cursor.execute(query, (broadcaster, user))
        return (await cursor.fetchone() or [None])[0] or datetime.min


async def getLastFfzSlotsAttempts(
        database: DatabaseMain,
        broadcaster: str,
        user: str,
        timestamp: datetime) -> List[datetime]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
SELECT attemptTime
    FROM ffz_slot_attempts
    WHERE broadcaster=? AND twitchUser=? AND attemptTime>=?
    ORDER BY attemptTime ASC
'''
        return [attempt async for attempt,
                in await cursor.execute(query, (broadcaster, user, timestamp))]


async def recordFfzSlots(
        database: DatabaseMain,
        channel: str,
        nick: str,
        emotes: Dict[int, str],
        selectedIds: List[int]) -> None:
    numMatching: int = 0
    emoteId: int
    for emoteId in selectedIds:
        if emoteId == selectedIds[0]:
            numMatching += 1
    allMatching: bool = numMatching == 3

    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str
        params: Tuple[Any, ...]
        query = '''
INSERT INTO ffz_slot_attempts
        (broadcaster, attemptTime, twitchUser, numMatching, isWin, emoticon1,
        emoticon2, emoticon3, emoticonId1, emoticonId2, emoticonId3)
    VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        params = (channel, nick, numMatching, allMatching,
                  emotes[selectedIds[0]], emotes[selectedIds[1]],
                  emotes[selectedIds[2]], selectedIds[0], selectedIds[1],
                  selectedIds[2],)
        await cursor.execute(query, params)

        if allMatching:
            query = '''
INSERT INTO ffz_slot_winners
    (broadcaster, winningTime, winner, winningEmote, winningEmoteId)
    VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)'''
            params = channel, nick, emotes[selectedIds[0]], selectedIds[0],
            await cursor.execute(query, params)

        await database.commit()


async def generate_bttv_pool(chat: 'data.Channel',
                             dataCache: CacheStore
                             ) -> Optional[Dict[str, str]]:
    async def getGlobal() -> Optional[Dict[str, str]]:
        if not await dataCache.bttv_load_global_emotes():
            return None
        return await dataCache.bttv_get_global_emotes()

    async def getBroadcaster() -> Optional[Dict[str, str]]:
        if not await dataCache.bttv_load_broadcaster_emotes(chat.channel):
            return None
        return await dataCache.bttv_get_broadcaster_emotes(chat.channel)

    globalEmotes: Optional[Dict[str, str]]
    chanEmotes: Optional[Dict[str, str]]
    globalEmotes, chanEmotes = await asyncio.gather(
        getGlobal(), getBroadcaster()
    )
    if globalEmotes is None or chanEmotes is None:
        return None
    emotes: Dict[str, str]
    emotes = dict(list(globalEmotes.items()) + list(chanEmotes.items()))
    if len(emotes) > 16:
        emotes = dict(random.sample(emotes.items(), 16))
    return emotes


async def getLastBttvSlotsUser(
        database: DatabaseMain,
        broadcaster: str,
        user: str) -> datetime:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str
        if database.isSqlite:
            query = '''
SELECT MAX(attemptTime) AS "[timestamp]"
    FROM bttv_slot_attempts
    WHERE broadcaster=? AND twitchUser=?
'''
        else:
            query = '''
SELECT MAX(attemptTime)
    FROM bttv_slot_attempts
    WHERE broadcaster=? AND twitchUser=?
'''
        await cursor.execute(query, (broadcaster, user))
        return (await cursor.fetchone() or [None])[0] or datetime.min


async def getLastBttvSlotsAttempts(
        database: DatabaseMain,
        broadcaster: str,
        user: str,
        timestamp: datetime) -> List[datetime]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
SELECT attemptTime
    FROM bttv_slot_attempts
    WHERE broadcaster=? AND twitchUser=? AND attemptTime>=?
    ORDER BY attemptTime ASC
'''
        return [attempt async for attempt,
                in await cursor.execute(query, (broadcaster, user, timestamp))]


async def recordBttvSlots(
        database: DatabaseMain,
        channel: str,
        nick: str,
        emotes: Dict[str, str],
        selectedIds: List[str]) -> None:
    numMatching: int = 0
    emoteId: str
    for emoteId in selectedIds:
        if emoteId == selectedIds[0]:
            numMatching += 1
    allMatching: bool = numMatching == 3

    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str
        params: Tuple[Any, ...]
        query = '''
INSERT INTO bttv_slot_attempts
        (broadcaster, attemptTime, twitchUser, numMatching, isWin, emoticon1,
        emoticon2, emoticon3, emoticonId1, emoticonId2, emoticonId3)
    VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        params = (channel, nick, numMatching, allMatching,
                  emotes[selectedIds[0]], emotes[selectedIds[1]],
                  emotes[selectedIds[2]], selectedIds[0], selectedIds[1],
                  selectedIds[2],)
        await cursor.execute(query, params)

        if allMatching:
            query = '''
INSERT INTO bttv_slot_winners
    (broadcaster, winningTime, winner, winningEmote, winningEmoteId)
    VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)'''
            params = channel, nick, emotes[selectedIds[0]], selectedIds[0],
            await cursor.execute(query, params)

        await database.commit()
