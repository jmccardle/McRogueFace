"""UNWRITTEN - battle barks. Authored by Fable. One-liners shown in the
battle log. Keys: char id -> {event: [lines]}. Pick randomly, never twice in
a row. Events: skill_a, skill_b, hurt_low (under 30% HP), victory, ko."""

BARKS = {
    "PIP": {
        "skill_a": ["Two for flinching.", "Quick hands, quicker feet."],
        "skill_b": ["Yoink.", "Finders keepers is a LAW now. I decided."],
        "hurt_low": ["Ow. Noted. OW."],
        "victory": ["Put it in the Book."],
        "ko": ["...page... torn..."],
    },
    "BRAMBLE": {
        "skill_a": ["The post has legs. STAND BEHIND THE POST.",
                    "Shieldwall! As rehearsed! I rehearsed alone!"],
        "skill_b": ["Forty years of standing still, arriving all at once!"],
        "hurt_low": ["Merely denting the paperwork."],
        "victory": ["Watch concluded. Nothing got past me."],
        "ko": ["...post... unmanned..."],
    },
    "MOTH": {
        "skill_a": ["Light does mending too.", "Steady. The wick knows."],
        "skill_b": ["This one's named. DUCK."],
        "hurt_low": ["Guttering... not out."],
        "victory": ["All lamps accounted for."],
        "ko": ["...keep it... lit..."],
    },
    "VERA": {
        "skill_a": ["Artisanal!", "Shake well before throwing!"],
        "skill_b": ["Possibility, resolving NOW."],
        "hurt_low": ["I'm marking THIS down as a cost of business."],
        "victory": ["Invoice to follow."],
        "ko": ["...inventory... early again..."],
    },
    "CANTOR": {
        "skill_a": ["A note, held long enough, is a wall.",
                    "Tuning... found you."],
        "skill_b": ["THE FANFARE ARRIVES IN THE MIDDLE."],
        "hurt_low": ["Reeds cracked. Song intact."],
        "victory": ["Rest, everyone. That is also part of the music."],
        "ko": ["...the note... someone hold... the note..."],
    },
    "NYX": {
        "skill_a": ["Cold spot. You're standing in it.",
                    "The margin bites back."],
        "skill_b": ["Watch the empty spot. WATCH IT."],
        "hurt_low": ["Still here. STILL here."],
        "victory": ["Sketch that."],
        "ko": ["...later... always later..."],
    },
}
