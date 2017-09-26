CREATE TABLE slot_bots (
    broadcaster VARCHAR NOT NULL,
    bot VARCHAR NOT NULL,
    marked TIMESTAMP NOT NULL,
    PRIMARY KEY (broadcaster, bot)
);

CREATE TABLE slot_winners (
    id SERIAL NOT NULL PRIMARY KEY,
    broadcaster VARCHAR NOT NULL,
    winningTime TIMESTAMP NOT NULL,
    winner VARCHAR NOT NULL,
    winningEmote VARCHAR NOT NULL,
    winningEmoteId INTEGER NOT NULL
);
CREATE INDEX slot_winners_broadcaster ON slot_winners (broadcaster);

CREATE TABLE slot_attempts (
    id SERIAL NOT NULL PRIMARY KEY,
    broadcaster VARCHAR NOT NULL,
    attemptTime TIMESTAMP NOT NULL,
    twitchUser VARCHAR NOT NULL,
    numMatching INTEGER NOT NULL,
    isWin BOOLEAN NOT NULL,
    emoticon1 VARCHAR NOT NULL,
    emoticon2 VARCHAR NOT NULL,
    emoticon3 VARCHAR NOT NULL,
    emoticonId1 INTEGER NOT NULL,
    emoticonId2 INTEGER NOT NULL,
    emoticonId3 INTEGER NOT NULL,
    isBasicMatch BOOLEAN NOT NULL,
    isKappaMatch BOOLEAN NOT NULL,
    isCatMatch BOOLEAN NOT NULL,
    isDogMatch BOOLEAN NOT NULL,
    isSubscriberMatch BOOLEAN NOT NULL
);
CREATE INDEX slot_attempts_broadcaster ON slot_attempts (broadcaster);

CREATE TABLE ffz_slot_winners (
    id SERIAL NOT NULL PRIMARY KEY,
    broadcaster VARCHAR NOT NULL,
    winningTime TIMESTAMP NOT NULL,
    winner VARCHAR NOT NULL,
    winningEmote VARCHAR NOT NULL,
    winningEmoteId INTEGER NOT NULL
);
CREATE INDEX ffz_slot_winners_broadcaster ON ffz_slot_winners (broadcaster);

CREATE TABLE ffz_slot_attempts (
    id SERIAL NOT NULL PRIMARY KEY,
    broadcaster VARCHAR NOT NULL,
    attemptTime TIMESTAMP NOT NULL,
    twitchUser VARCHAR NOT NULL,
    numMatching INTEGER NOT NULL,
    isWin BOOLEAN NOT NULL,
    emoticon1 VARCHAR NOT NULL,
    emoticon2 VARCHAR NOT NULL,
    emoticon3 VARCHAR NOT NULL,
    emoticonId1 INTEGER NOT NULL,
    emoticonId2 INTEGER NOT NULL,
    emoticonId3 INTEGER NOT NULL
);
CREATE INDEX ffz_slot_attempts_broadcaster ON ffz_slot_attempts (broadcaster);

CREATE TABLE bttv_slot_winners (
    id SERIAL NOT NULL PRIMARY KEY,
    broadcaster VARCHAR NOT NULL,
    winningTime TIMESTAMP NOT NULL,
    winner VARCHAR NOT NULL,
    winningEmote VARCHAR NOT NULL,
    winningEmoteId VARCHAR NOT NULL
);
CREATE INDEX bttv_slot_winners_broadcaster ON bttv_slot_winners (broadcaster);

CREATE TABLE bttv_slot_attempts (
    id SERIAL NOT NULL PRIMARY KEY,
    broadcaster VARCHAR NOT NULL,
    attemptTime TIMESTAMP NOT NULL,
    twitchUser VARCHAR NOT NULL,
    numMatching INTEGER NOT NULL,
    isWin BOOLEAN NOT NULL,
    emoticon1 VARCHAR NOT NULL,
    emoticon2 VARCHAR NOT NULL,
    emoticon3 VARCHAR NOT NULL,
    emoticonId1 VARCHAR NOT NULL,
    emoticonId2 VARCHAR NOT NULL,
    emoticonId3 VARCHAR NOT NULL
);
CREATE INDEX bttv_slot_attempts_broadcaster ON bttv_slot_attempts (broadcaster);
