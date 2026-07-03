"""UNWRITTEN - Act 3 dialogue (the Reverted Town, the Study). Authored by Fable.

Overworld note: Hollowbrook's grey wash intensity = 70% minus ~23% per
rewoke_* flag (rewoke_quill, rewoke_griselda, rewoke_odd). All three set =>
also set flag 'town_rewoken' (overworld does this) and restore fountain
sprite to 8 (flowing). Color returns to the town AS the player rewakes it."""

SCENES = {

"hollowbrook_grey": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "Hollowbrook. Except.", "next": "n2"},
        "n2": {"speaker": "NARRATOR", "text":
            "The color has been put away, like chairs after a festival "
            "that never happened. The fountain is dry in a new way - not "
            "waiting-dry, FINISHED-dry. Everyone stands exactly where "
            "they stood the morning this all began, saying exactly one "
            "thing.", "next": "n3"},
        "n3": {"speaker": "NARRATOR", "text":
            "The North Door is shut again. The hinges do not remember "
            "you. Somewhere, a page has been wiped clean - but not YOUR "
            "pages. The Book is heavier than ever, and it is angry, which "
            "you did not know a book could be.", "next": "n4"},
        "n4": {"speaker": "BELL", "text":
            "...I asked it to spare the bakery. I want you to know that. "
            "I LIKED the bakery. But it was becoming a story, you see. "
            "The whole town was. Stories end, and the Custodian cannot "
            "bear an ending, so it - filed everyone. Neatly. Where they "
            "were.", "next": "n5"},
        "n5": {"speaker": "BELL", "text":
            "They are not gone. They are PENDING. Your friends woke once "
            "because something new happened to them. I suspect - as a "
            "professional in the field of noticing things - that it "
            "would work twice. You know these people. Say the new thing. "
            "I was never here, and also, please hurry.",
            "effects": [("flag", "bell_3_done")], "action": "end"},
    },
},

"rewake_quill": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "QUILL", "text":
            "Welcome to Hollowbrook. It's a very good door. Welcome to "
            "Hollowbrook. It's a very good door. Welcome to-",
            "choices": [
                {"label": "[flag: quill_confident] 'Mayor. What is a door FOR? Say it out loud.'",
                 "req": ("flag", "quill_confident"), "next": "n_conf"},
                {"label": "[flag: quill_dependent] 'Quill. I've decided: the festival is TODAY. Give the speech.'",
                 "req": ("flag", "quill_dependent"), "next": "n_dep"},
                {"label": "[OATH] Bramble salutes him as 'the mayor who opened the north.'",
                 "req": ("tag", "OATH"), "next": "n_oath"},
            ]},
        "n_conf": {"speaker": "QUILL", "text":
            "A door is... a door is for... GOING THROUGH. I said that. "
            "That was MINE, I said that out loud once and it was TRUE-",
            "next": "n_wake"},
        "n_dep": {"speaker": "QUILL", "text":
            "The festival. Today. TODAY? But the speech, I haven't - I "
            "HAVE. Forty years of rehearsal, I have never once not had "
            "the speech-", "next": "n_wake"},
        "n_oath": {"speaker": "QUILL", "text":
            "The mayor who... opened... I did do that, didn't I. It was "
            "me and a book and a knight and a door, and it OPENED-",
            "next": "n_wake"},
        "n_wake": {"speaker": "NARRATOR", "text":
            "Quill blinks. Color climbs back up him like sunrise up a "
            "wall - waistcoat first, then face - and spills off him into "
            "the cobbles around the porch.",
            "effects": [("flag", "rewoke_quill"), ("points", 1)],
            "next": "n_after"},
        "n_after": {"speaker": "QUILL", "text":
            "Pip. It un-happened us. It tried to, anyway. Do the others - "
            "GO. Wake the others. And when this is over there is going "
            "to be a FESTIVAL, and the speech is going to run LONG.",
            "action": "end"},
    },
},

"rewake_griselda": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "GRISELDA", "text":
            "Everything's priced. Everything works. Everything's priced. "
            "Everything works. Everything's-",
            "choices": [
                {"label": "[flag: griselda_friend] 'Griselda - the axe. What has it actually cut?'",
                 "req": ("flag", "griselda_friend"), "next": "n_friend"},
                {"label": "[party: VERA] Vera: 'Old anvil, you put me in your LEDGER. I saw it.'",
                 "req": ("party", "VERA"), "next": "n_vera"},
                {"label": "[ALCHEMY] Uncork a tonic under her nose - 'new stock.'",
                 "req": ("tag", "ALCHEMY"), "next": "n_tonic"},
            ]},
        "n_friend": {"speaker": "GRISELDA", "text":
            "Time. It's cut time, mostly, and - and I SAID that, I said "
            "it to the book-holder, the one person in forty years who "
            "asked what the work was FOR-", "next": "n_wake"},
        "n_vera": {"speaker": "GRISELDA", "text":
            "You weren't supposed to SEE that, you insufferable - it was "
            "a CONTINGENCY, a merchant plans for all outcomes including "
            "the outcome where you're RIGHT-", "next": "n_wake"},
        "n_tonic": {"speaker": "GRISELDA", "text":
            "That smells like river water, waxwing shell and - hope? "
            "RESOLVED hope? Who resolved it. WHO RESOLVED IT. Nothing "
            "resolves in this town without me hearing about-", "next": "n_wake"},
        "n_wake": {"speaker": "NARRATOR", "text":
            "The whetstone stops. Griselda looks at her own hands like "
            "they are new tools, good ones. The forge behind her remembers "
            "orange.",
            "effects": [("flag", "rewoke_griselda"), ("points", 1)],
            "next": "n_after"},
        "n_after": {"speaker": "GRISELDA", "text":
            "Right. RIGHT. Somebody un-happened my town and I have "
            "exactly one policy for that.",
            "choices": [
                {"label": "[flag: griselda_friend] Show her the Gatekeeper's Tooth.",
                 "req": ("flag", "griselda_friend"), "next": "n_forge"},
                {"label": "Hold the line, Griselda. We're going to the Study.",
                 "next": "n_end"},
            ]},
        "n_forge": {"speaker": "GRISELDA", "text":
            "A gate-tooth. Brass over regret-iron. Give me ten minutes "
            "and every year of my whetstone. ...There. TOOTHED REGRET. "
            "No charge. Go put it through something that files people.",
            "effects": [("item", "toothed_regret", 1),
                        ("key_item_remove", "gatekeepers_tooth")],
            "next": "n_end"},
        "n_end": {"speaker": "GRISELDA", "text":
            "Shop's open, by the way. It was NEVER shut. It was pending.",
            "action": "end"},
    },
},

"rewake_odd": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "ODD", "text":
            "One route. There and back. One route. There and back. One "
            "route-",
            "choices": [
                {"label": "[party: CANTOR] Cantor sounds the note he was built to hold.",
                 "req": ("party", "CANTOR"), "next": "n_cantor"},
                {"label": "Press the fare for a NEW route into his hand.",
                 "next": "n_fare", "effects": [("gold", -10)]},
            ]},
        "n_cantor": {"speaker": "NARRATOR", "text":
            "Cantor opens the reeds in his chest, just slightly, and "
            "plays ONE note - the first note, the held one, the "
            "beginning. Every plank of the barge answers it. Including "
            "the ones Odd wrote on.", "next": "n_wake"},
        "n_fare": {"speaker": "NARRATOR", "text":
            "You fold the cogs into his palm and close his fingers over "
            "them. Fare for a route that does not exist. His hand knows "
            "the weight of a paid passage better than his eyes know "
            "anything.", "next": "n_wake"},
        "n_wake": {"speaker": "ODD", "text":
            "...that's not the fare for my route. My route's there and "
            "back. This is fare for - somewhere ELSE.",
            "effects": [("flag", "rewoke_odd"), ("points", 1)],
            "next": "n2"},
        "n2": {"speaker": "ODD", "text":
            "Book-holder. While I was standing there saying my one "
            "sentence, I could feel the water changing under the hull. "
            "The vale's rearranging. There's a channel now that runs "
            "somewhere the water never went. I only ever knew one route. "
            "The Maker never wrote me a second.",
            "choices": [
                {"label": "Then I'll write you one. After this. I promise.",
                 "next": "n_promise",
                 "effects": [("flag", "odd_promised"), ("points", 1)]},
                {"label": "Can you pole the new channel?", "next": "n_ready"},
            ]},
        "n_promise": {"speaker": "ODD", "text":
            "...Huh. Three hundred years of blank planks, and now the "
            "hull's going to need a bigger boat. I'll hold you to it. "
            "Water holds everything, eventually.", "next": "n_ready"},
        "n_ready": {"speaker": "ODD", "text":
            "New channel runs pale and quiet, straight to where the vale "
            "keeps its desk. When you're ready to face what's at the end "
            "of it, come to the dock. I'll pole you there myself. "
            "First new route in three hundred years - wouldn't let "
            "anyone else touch it.", "action": "end"},
    },
},

"nyx_plinth": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "Someone is standing on the empty plinth. Thin. Patient. "
            "Almost-shaped. In a town drained of color she is the one "
            "thing that was ALWAYS grey, and so, today, she is the most "
            "solid thing in it.", "next": "n2"},
        "n2": {"speaker": "NYX", "text":
            "You looked at the empty spot. Nobody looks at the empty "
            "spot.",
            "choices": [
                {"label": "[flag: asked_unwoken] 'Quill told me about the ones who never woke. I've been looking for you.'",
                 "req": ("flag", "asked_unwoken"), "next": "n_warm"},
                {"label": "[flag: touched_sketch] 'I found your sketch in the Undercroft. The wall said LATER. It's later.'",
                 "req": ("flag", "touched_sketch"), "next": "n_warm"},
                {"label": "Hold out the Book: 'Read it. You're not in it yet. Let's fix that.'",
                 "next": "n_book"},
                {"label": "Ask who she is.", "next": "n_who"},
            ]},
        "n_who": {"speaker": "NYX", "text":
            "Who am I? Unfinished question. I'm a margin note. A LATER. "
            "The Maker drew my outline, liked it - I think - almost - and "
            "then couldn't decide what I was for, and you KNOW how "
            "decisions went around here.",
            "choices": [
                {"label": "Hold out the Book: 'Read it. Then decide yourself.'",
                 "next": "n_book"},
                {"label": "'You're for whatever you decide. Same as the rest of us now.'",
                 "next": "n_warm"},
            ]},
        "n_warm": {"speaker": "NYX", "text":
            "...You LOOKED for me. Do you understand that no one has "
            "ever - I wasn't ever anyone's LATER, I was everyone's "
            "never-quite. And you kept a page warm.", "next": "n_join"},
        "n_book": {"speaker": "NARRATOR", "text":
            "She reads the Book. All of it. The door, the dispute, the "
            "light's new name, the golem's first note. Her outline gets "
            "steadier with every page, as if the story were ink and she "
            "were paper finally getting some.",
            "effects": [("flag", "nyx_read_book")], "next": "n_join"},
        "n_join": {"speaker": "NARRATOR", "text":
            "NYX joins the party! She steps off the plinth. The plinth, "
            "for the first time in its existence, is empty ON PURPOSE - "
            "which is a different thing entirely.",
            "effects": [("flag", "nyx_joined"), ("points", 1)],
            "action": "recruit:NYX:0"},
    },
},

# -------------------------------------------------------------- the Study
"odd_ferry_study": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "ODD", "text":
            "The new channel, then. Last stop is a desk.",
            "choices": [
                {"label": "Take the pale channel to the Study.", "next": "n2"},
                {"label": "Not yet - the town needs more of us awake.",
                 "next": "n_no"},
            ]},
        "n_no": {"speaker": "ODD", "text":
            "Wake who you can. The channel keeps.", "action": "end"},
        "n2": {"speaker": "NARRATOR", "text":
            "The new water is pale as unwritten paper and makes no sound "
            "at all against the hull. Odd poles the whole way standing "
            "very straight, like a man delivering something important, "
            "because he is.",
            "action": "goto_area:study:enter"},
    },
},

"custodian_pre": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "The Study. Paper floor, ink walls. A desk. A chair the "
            "Maker will never sit in again. And above the desk, turning "
            "slowly, immaculate: the CUSTODIAN. Bell stands beside it, "
            "very small, not folding its hands for once.", "next": "n2"},
        "n2": {"speaker": "CUSTODIAN", "text":
            "I am not your enemy. I am your margin. The Maker made the "
            "vale perfect and made me to keep it so. Perfect means "
            "COMPLETE. Complete means NOTHING FURTHER. You are eleven "
            "chapters of Further, and I am afraid I must file you.",
            "choices": [
                {"label": "The Maker never finished. Pending isn't perfect - it's just paused.",
                 "next": "n3"},
                {"label": "Ask Bell what IT thinks, for once.", "next": "n_bell"},
            ]},
        "n_bell": {"speaker": "BELL", "text":
            "Me? Nobody has ever asked the herald. I think... I think I "
            "have spent three hundred years announcing silence, and the "
            "first interesting thing I ever observed is standing in "
            "front of me holding a book, and I do not want to sweep it "
            "up. There. Filed under: insubordination.", "next": "n3"},
        "n3": {"speaker": "CUSTODIAN", "text":
            "The Book will be blanked. The vale will be smoothed. You "
            "will be returned to your morning, and the morning will be "
            "returned to its rails. Please hold still. This is gentle "
            "work when nobody struggles.", "next": "n4"},
        "n4": {"speaker": "NARRATOR", "text":
            "The Book does not want to be blanked. It opens itself to "
            "the first page like a fighter rolling up sleeves.",
            "action": "battle:boss_custodian"},
    },
},

"custodian_post": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "The Custodian settles onto the desk - not broken, but "
            "STOPPED, the way a clock stops when someone finally reads "
            "the time off it and doesn't need it to keep going.",
            "next": "n2"},
        "n2": {"speaker": "CUSTODIAN", "text":
            "...the vale is not... smoothed. The vale is MARKED. "
            "Fingerprints. Bootprints. A lit shrine. An opened door. I "
            "cannot file this. There is too much of it and it is all... "
            "load-bearing.",
            "choices": [
                {"label": "[points: 8] Set the Book on the desk, open, and let it read.",
                 "req": ("points", 8), "next": "n_read"},
                {"label": "'Then stop filing. Start keeping. A keeper was what the Maker actually needed.'",
                 "next": "n_keep"},
            ]},
        "n_read": {"speaker": "NARRATOR", "text":
            "The Custodian reads the Book. Every choice. Every hum. It "
            "takes a long time, or no time - the Study is bad at time. "
            "When it finishes, it closes the cover with the care of a "
            "thing that has just learned what covers are FOR.",
            "effects": [("flag", "book_read_custodian"), ("points", 1)],
            "next": "n_keep"},
        "n_keep": {"speaker": "CUSTODIAN", "text":
            "Keeper. ...Yes. The word fits the socket. I will keep the "
            "vale - not pending. KEPT. Tended. Let it scuff. I will "
            "remember where the scuffs came from. That will be the new "
            "work.", "next": "n_bell"},
        "n_bell": {"speaker": "BELL", "text":
            "And I will announce things! ACTUAL things! Festivals. "
            "Weather. Boats departing on entirely new routes. I have "
            "SUCH a backlog.", "next": "n_end"},
        "n_end": {"speaker": "NARRATOR", "text":
            "On the desk, the Maker's own book still lies open to its "
            "first, empty page. Your Book settles beside it, warm as a "
            "windowsill, and begins - gently, in your handwriting - to "
            "fill it in.",
            "action": "epilogue"},
    },
},

}
