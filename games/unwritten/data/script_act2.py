"""UNWRITTEN - Act 2 dialogue (the Undercroft). Authored by Fable."""

SCENES = {

"vera_reconcile": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "VERA", "text":
            "Oh. It's the ruling committee. Yes, I followed you across the "
            "water - a merchant goes where the possibilities are, and "
            "apparently they all go where YOU go. I'm not speaking to you, "
            "incidentally. This is market research.",
            "choices": [
                {"label": "[ALCHEMY] Offer her a Bomb Flask: 'Your field needs a colleague.'",
                 "req": ("item", "bomb_flask"), "next": "n_bomb",
                 "effects": [("item", "bomb_flask", -1)]},
                {"label": "[NIMBLE] Return the ledger page you lifted from Griselda's counter.",
                 "req": ("tag", "NIMBLE"), "next": "n_ledger"},
                {"label": "We were wrong about your shop. I'm sorry.", "next": "n_flat"},
            ]},
        "n_bomb": {"speaker": "VERA", "text":
            "A bomb flask. Waxwing shell, river water and - is that an "
            "UNRESOLVED HOPE in suspension? You made one. You made one of "
            "MINE, except yours goes off.", "next": "n_join"},
        "n_ledger": {"speaker": "VERA", "text":
            "...This is from Griselda's ledger. Forty years of stock, "
            "nothing sold, and she wrote my name in the suppliers column "
            "anyway. The old anvil PLANNED to stock my tonics. When they "
            "worked. She was waiting too.", "next": "n_join"},
        "n_flat": {"speaker": "VERA", "text":
            "Hm. An apology with no garnish. In this economy. ...Accepted, "
            "obviously. Do you know how long I have waited for someone to "
            "be WRONG about something? It means things are happening.",
            "next": "n_join"},
        "n_join": {"speaker": "NARRATOR", "text":
            "VERA joins the party! She immediately relabels three of your "
            "tonics 'artisanal.'",
            "effects": [("flag", "vera_reconciled"), ("points", 1)],
            "action": "recruit:VERA:3"},
    },
},

"nyx_sketch": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "Charcoal on the wall, older than dust: a figure, half-drawn. "
            "Thin. Patient. The face was never filled in. Underneath, in "
            "the Maker's hand, one word: LATER.",
            "choices": [
                {"label": "Trace the unfinished line with a finger.", "next": "n2"},
                {"label": "Move on.", "next": "n_no"},
            ]},
        "n2": {"speaker": "NARRATOR", "text":
            "The charcoal is cold. Somewhere behind you - exactly where "
            "no one is standing - the air feels briefly grateful. The "
            "Book hums, low.",
            "effects": [("flag", "touched_sketch")], "action": "end"},
        "n_no": {"speaker": "NARRATOR", "text":
            "LATER, says the wall, to no one, for three hundred years.",
            "action": "end"},
    },
},

"cantor_wake": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "The Chord Hall. Pipes rise into the dark like a bronze "
            "forest. At its center kneels a golem, fists on knees, head "
            "bowed - dust-caped, patient, enormous. Its chest is an organ "
            "of stopped reeds. A brass plaque reads: FOR THE FANFARE, "
            "WHEN IT BEGINS.", "next": "n2"},
        "n2": {"speaker": "NARRATOR", "text":
            "It has been holding the first note of a song for three "
            "hundred years. The Book grows warm in your hands - then hot "
            "- then it opens ITSELF, to the first page, and waits. It has "
            "never done that before. It wants a name.",
            "choices": [
                {"label": "Write CANTOR.", "next": "n_cantor",
                 "effects": [("points", 1)]},
                {"label": "Write its serial: CH-0RD.", "next": "n_serial",
                 "effects": [("points", 1)]},
                {"label": "Write nothing. Lay a hand on the plaque instead.",
                 "next": "n_quiet",
                 "effects": [("flag", "cantor_quiet"), ("points", 1)]},
            ]},
        "n_cantor": {"speaker": "NARRATOR", "text":
            "CANTOR, says the page, in your handwriting, which has never "
            "looked like that before. The reeds shiver. Dust pours off "
            "shoulders like a curtain falling.", "next": "n_wake"},
        "n_serial": {"speaker": "NARRATOR", "text":
            "CH-0RD, says the page. Somewhere in the golem's chest a reed "
            "sounds a small, amused note - the mechanical equivalent of a "
            "raised eyebrow - and accepts it. Names are what you answer "
            "to. It will answer.", "next": "n_wake"},
        "n_quiet": {"speaker": "NARRATOR", "text":
            "You write nothing. You put your hand on the plaque, over the "
            "word BEGINS. The golem's head lifts anyway. Some things wake "
            "for a name. Some wake for a knock at the door.", "next": "n_wake"},
        "n_wake": {"speaker": "CANTOR", "text":
            "...The note. I was holding the first note. Is it - is it "
            "TIME? Has it begun?", "next": "n3"},
        "n3": {"speaker": "PIP", "text":
            "It's begun. It began a few days ago, actually. You're not "
            "late - you're the fanfare. Fanfares come in the middle "
            "sometimes.", "next": "n4"},
        "n4": {"speaker": "CANTOR", "text":
            "The middle. Yes. A strong place for brass.", "next": "n5"},
        "n5": {"speaker": "NARRATOR", "text":
            "CANTOR joins the party! When he walks, the Undercroft hums "
            "faintly in sympathy, like a struck tuning fork the size of a "
            "county.",
            "effects": [("flag", "cantor_joined"), ("points", 1)],
            "action": "recruit:CANTOR:4"},
    },
},

"chest_a": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "A chest, banded and patient. Inside: supplies laid down by "
            "someone who believed, eventually, in company.",
            "effects": [("item", "red_tonic", 2), ("item", "blue_draught", 1),
                        ("gold", 25), ("flag", "chest_a_open")],
            "action": "end"},
    },
},

"chest_b": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "This chest holds a weapon wrapped in waxed cloth, and a note: "
            "'FOR WHOEVER FINALLY NEEDS IT.' You need it.",
            "effects": [("item", "twin_axe", 1), ("item", "bomb_flask", 1),
                        ("flag", "chest_b_open")],
            "action": "end"},
    },
},

"mimic_chest": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "A chest sits alone in the alcove, very slightly too pleased "
            "with itself.",
            "choices": [
                {"label": "Open it.", "next": "n_fight"},
                {"label": "[SHADOW] Circle it first.", "req": ("tag", "SHADOW"),
                 "next": "n_shadow"},
                {"label": "Leave it.", "next": "n_no"},
            ]},
        "n_shadow": {"speaker": "NYX", "text":
            "It's breathing. Chests don't breathe. I say we open it "
            "anyway - it's been waiting three hundred years to bite "
            "someone, and honestly? Same.", "next": "n_fight"},
        "n_no": {"speaker": "NARRATOR", "text":
            "The chest does its best impression of furniture as you go.",
            "action": "end"},
        "n_fight": {"speaker": "NARRATOR", "text":
            "The chest has TEETH -", "action": "battle:uc_mimic"},
    },
},

"mimic_post": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "The mimic subsides into honest lumber. Inside its... "
            "everything... you find a trinket of quietly absurd quality.",
            "effects": [("flag", "mimic_slain"), ("item", "second_trinket", 1)],
            "action": "end"},
    },
},

# --------------------------------------------------------- Gatekeeper boss
"gatekeeper_pre": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "The deep gate. And waiting before it, hands folded, "
            "immaculate in the fog: Bell.", "next": "n2"},
        "n2": {"speaker": "BELL", "text":
            "Hello again. I am here in an official capacity, which I "
            "regret. Beyond this gate the vale keeps its deepest pending "
            "things. The Custodian asks - and it does ASK, we are not "
            "savages - that you stop here.",
            "choices": [
                {"label": "We're going through, Bell.", "next": "n3"},
                {"label": "What's the Custodian afraid of?", "next": "n2b"},
            ]},
        "n2b": {"speaker": "BELL", "text":
            "Afraid? Nothing. The Custodian does not fear stories. It "
            "TIDIES them. It is very good at its work and I have never "
            "once heard it wonder whether the work is good. That "
            "distinction has been keeping me up at night. Custodians "
            "don't sleep, so I have had a great deal of night.",
            "next": "n3"},
        "n3": {"speaker": "BELL", "text":
            "Then I will observe. For the record: I was courteous, you "
            "were determined, and the moss was excellent. The Gatekeeper "
            "will see you now.", "next": "n4"},
        "n4": {"speaker": "NARRATOR", "text":
            "The gate's stone face grinds open its eyes. It looks at your "
            "party the way a librarian looks at a dog in the atlas "
            "section.", "next": "n5"},
        "n5": {"speaker": "GATEKEEPER", "text":
            "UNSCHEDULED. ALL OF THIS IS UNSCHEDULED. I HAVE KEPT THE "
            "DEEP VALE PENDING FOR THREE CENTURIES AND I WILL NOT BE "
            "FILED INCORRECTLY BY A WALKING PAPERWORK ERROR.",
            "next": "n6"},
        "n6": {"speaker": "NARRATOR", "text":
            "The Gatekeeper inhales.", "action": "battle:boss_gatekeeper"},
    },
},

"gatekeeper_post": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "The stone face settles, cracked, strangely peaceful. Its "
            "jaws relax for the first time in three hundred years, and "
            "one tooth - a long brass wedge - drops politely at your "
            "feet.", "effects": [("flag", "gatekeeper_slain"),
                                 ("item", "gatekeepers_tooth", 1)],
            "next": "n2"},
        "n2": {"speaker": "GATEKEEPER", "text":
            "...off schedule. everything off schedule. how... "
            "restful...", "next": "n3"},
        "n3": {"speaker": "NARRATOR", "text":
            "Then, from everywhere at once - from the stone, the fog, the "
            "brass forest above - a sound like the whole vale being "
            "SMOOTHED. Bell has gone pale, which for Bell means neat.",
            "next": "n4"},
        "n4": {"speaker": "BELL", "text":
            "That was the Custodian. It has... responded. You should go "
            "home, book-holder. Quickly. And I am sorry - I want that "
            "noted somewhere that doesn't get swept. I am SORRY.",
            "next": "n5"},
        "n5": {"speaker": "NARRATOR", "text":
            "The way back up is short. It shouldn't be. The vale is "
            "rearranging itself to hurry you along - or to get you out of "
            "the way.",
            "effects": [("act", 3)],
            "action": "goto_area:hollowbrook:from_ferry"},
    },
},

}
