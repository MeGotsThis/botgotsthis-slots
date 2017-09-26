from typing import Mapping, Optional


def features() -> Mapping[str, Optional[str]]:
    if not hasattr(features, 'features'):
        setattr(features, 'features', {
            'slots': 'Emoticon Slots',
            'ffzslots': 'FrankerFaceZ Emoticon Slots',
            'bttvslots': 'Better Twitch.TV Emoticon Slots',
            })
    return getattr(features, 'features')
