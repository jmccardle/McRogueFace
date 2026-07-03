"""UNWRITTEN - Act 1 dialogue. Authored by Fable. Text is canon: fix syntax,
never rewrite content. Schema: design/ARCHITECTURE.md section 3."""

SCENES = {

# ------------------------------------------------------------------ opening
"intro": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "The Maker finished the vale on a Tuesday. Every gear meshed. "
            "Every door hung true. The sun ran on rails.", "next": "n2"},
        "n2": {"speaker": "NARRATOR", "text":
            "Then the Maker sat down to write what should happen here, "
            "and could not think of a single thing.", "next": "n3"},
        "n3": {"speaker": "NARRATOR", "text":
            "That was three hundred years ago. The vale has been waiting "
            "ever since. It is very good at it now.", "next": "n4"},
        "n4": {"speaker": "NARRATOR", "text":
            "This morning, someone in Hollowbrook wakes up holding a book "
            "that was not there yesterday. The pages are blank. The cover "
            "is warm, like a windowsill.", "next": "n5"},
        "n5": {"speaker": "PIP", "text":
            "...That's new.", "next": "n6"},
        "n6": {"speaker": "NARRATOR", "text":
            "Nothing in Hollowbrook has been new for three hundred years. "
            "Pip decides to ask the mayor about it. And that word - "
            "DECIDES - hums through the book like a struck string.",
            "next": "n7"},
        "n7": {"speaker": "NARRATOR", "text":
            "Walk with the arrow keys or WASD. Talk by walking into people. "
            "The Book will keep track of what you choose. It has been "
            "waiting the longest of all.", "action": "end"},
    },
},

"plinth_look": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "An empty plinth beside the fountain. There is a smooth patch "
            "where a name would go. No statue was ever chosen.",
            "choices": [
                {"label": "Touch the smooth patch.", "next": "n2"},
                {"label": "Leave it be.", "next": "n3"},
            ]},
        "n2": {"speaker": "NARRATOR", "text":
            "Cold. Waiting. For half a heartbeat you are sure something "
            "stands there - thin, patient, almost-shaped. Then it is a "
            "plinth again. The Book hums, softly, like an apology.",
            "effects": [("flag", "touched_plinth")], "action": "end"},
        "n3": {"speaker": "NARRATOR", "text":
            "You leave it be. It is used to that.", "action": "end"},
    },
},

# ------------------------------------------------------------ Mayor Quill
"quill_first": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "QUILL", "text":
            "Oh! A visitor. Well - a resident. Well - Pip. You walked over "
            "here. On purpose, by the look of it. Nobody walks anywhere on "
            "purpose. Are you ill?", "next": "n2"},
        "n2": {"speaker": "PIP", "text":
            "I woke up holding this book. It was not there yesterday. And "
            "I keep... deciding things. It's making a sound when I do.",
            "next": "n3"},
        "n3": {"speaker": "QUILL", "text":
            "Deciding. DECIDING. Goodness. I have been rehearsing a speech "
            "for the Founding Festival for forty years, you know. Never "
            "given it. Nobody ever DECIDED on a date.", "next": "n4"},
        "n4": {"speaker": "QUILL", "text":
            "If the book wants decisions, there is really only one place in "
            "Hollowbrook that has ever needed one. The North Door.",
            "next": "n5"},
        "n5": {"speaker": "QUILL", "text":
            "It's a very good door. Best in the vale. We are all very proud "
            "of it, and nobody has ever once been through it. It isn't "
            "locked. There has simply never been a reason.",
            "choices": [
                {"label": "Then we open it. Today. I've decided.",
                 "next": "n6",
                 "effects": [("flag", "quill_dependent"), ("points", 1)]},
                {"label": "What do YOU think we should do, Mayor?",
                 "next": "n7",
                 "effects": [("flag", "quill_confident"), ("points", 1)]},
            ]},
        "n6": {"speaker": "QUILL", "text":
            "You've - yes. Yes! Marvelous. Someone else deciding. That is "
            "my very favorite kind of decision. Ser Bramble guards the "
            "door. Guarding is all he has, poor fellow. Be kind about it.",
            "next": "n9"},
        "n7": {"speaker": "QUILL", "text":
            "What do I - me? I... hm. I think... I think a door is for "
            "going through. I have thought so for forty years and never "
            "said it out loud. Is that allowed? Saying it out loud?",
            "next": "n8"},
        "n8": {"speaker": "PIP", "text":
            "You just did. It sounded like a mayor.", "next": "n9"},
        "n9": {"speaker": "QUILL", "text":
            "Ser Bramble guards it. Forty years at his post. Someone wrote "
            "GUARD on his orders once and nothing since. Talk to him - and "
            "Pip. Thank you. Whatever this turns out to be.",
            "choices": [
                {"label": "One more thing. Did everyone wake up like me?",
                 "next": "n10"},
                {"label": "[leave] I'll see about the door.",
                 "next": "n_end"},
            ]},
        "n10": {"speaker": "QUILL", "text":
            "Like you? No. No, and here is the strange part - some never "
            "woke at all. There are corners of this town where you feel "
            "someone OUGHT to be standing, and no one ever is. The plinth "
            "by the fountain. The empty chair at the dock. The Maker "
            "sketched more people than were ever finished, I think.",
            "effects": [("flag", "asked_unwoken"), ("points", 1)],
            "next": "n11"},
        "n11": {"speaker": "QUILL", "text":
            "Don't stare at the empty spots too long. It isn't rude. It "
            "just aches.", "next": "n_end"},
        "n_end": {"speaker": "QUILL", "text":
            "The door, then. North end of town. You can't miss it - it's "
            "the one thing here that ever looked like it was for "
            "something.",
            "effects": [("flag", "quest_door")], "action": "end"},
    },
},

"door_shut": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "The North Door. Oak, iron, faintly smug. It is not locked. "
            "It has simply never been opened, and the hinges know it.",
            "action": "end"},
    },
},

# ------------------------------------------------------------- Ser Bramble
"bramble_door": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "BRAMBLE", "text":
            "Halt. This door is guarded.", "next": "n2"},
        "n2": {"speaker": "PIP", "text":
            "From what?", "next": "n3"},
        "n3": {"speaker": "BRAMBLE", "text":
            "...From going unguarded. My orders say GUARD. One word. Forty "
            "years I have held this post and no one has ever tried the "
            "door, which means - I have never failed. Do not take my "
            "record from me, citizen.",
            "choices": [
                {"label": "[OATH] Then take a new oath: guard the PEOPLE who walk through it.",
                 "req": None, "next": "n4",
                 "effects": [("flag", "bramble_new_oath")]},
                {"label": "The mayor says the door is for going through.",
                 "next": "n5"},
                {"label": "I'm opening it. You can guard me or fight me.",
                 "next": "n6", "effects": [("flag", "bramble_grumbles")]},
            ]},
        "n4": {"speaker": "BRAMBLE", "text":
            "Guard the... people. Through the door. So the post MOVES. "
            "The post has legs. I - forty years and it never once occurred "
            "to me that the post could have LEGS. Citizen, that is the "
            "finest order I have ever been given. I accept.", "next": "n7"},
        "n5": {"speaker": "BRAMBLE", "text":
            "The mayor SAID something? Decisively? ...Then the world really "
            "is ending. Or starting. Hard to tell the difference from "
            "inside a helmet. Very well - but if that door opens, whatever "
            "is beyond it becomes MY watch. I'm coming with you.",
            "next": "n7"},
        "n6": {"speaker": "BRAMBLE", "text":
            "Fight you? I have a better idea. I will GUARD you. "
            "Aggressively. At close range. Wherever you go. That will show "
            "you.", "next": "n7"},
        "n7": {"speaker": "NARRATOR", "text":
            "SER BRAMBLE joins the party! His armor sounds like a kitchen "
            "falling downstairs, but slower.",
            "effects": [("flag", "bramble_joined"), ("points", 1)],
            "action": "recruit:BRAMBLE:1", "next": "n8"},
        "n8": {"speaker": "BRAMBLE", "text":
            "Right. The door.", "next": "n9"},
        "n9": {"speaker": "NARRATOR", "text":
            "Bramble sets one gauntlet on the oak and pushes. Three hundred "
            "years of hinges think about it, and then - with a sound like "
            "the whole vale exhaling - the North Door opens onto the dock, "
            "the canal, and everything else.",
            "effects": [("flag", "door_open"), ("points", 1)],
            "action": "end"},
    },
},

# ------------------------------------------------- Griselda / Vera dispute
"griselda_shop": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "GRISELDA", "text":
            "Forty years I've sharpened this axe. You want to know what "
            "it's cut? Time, mostly. What'll it be?",
            "choices": [
                {"label": "Let's see your wares.", "next": "n_shop"},
                {"label": "Just passing through.", "next": "n_bye"},
            ]},
        "n_shop": {"speaker": "GRISELDA", "text":
            "Everything's priced. Everything works. Unlike SOME people's "
            "stock I could mention.", "action": "shop"},
        "n_bye": {"speaker": "GRISELDA", "text":
            "That's what the last three hundred years said too.",
            "action": "end"},
    },
},

"enter_shop": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "Griselda's smithy-and-sundries. The shelves are immaculate. "
            "Every item sits exactly where it sat last century.",
            "action": "shop"},
    },
},

"shop_dispute": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "VERA", "text":
            "- all I am SAYING, Griselda, is that a possibility tonic "
            "cannot be expected to work in a town with no possibilities. "
            "That is not fraud. That is inventory ahead of its time.",
            "next": "n2"},
        "n2": {"speaker": "GRISELDA", "text":
            "You've sold four hundred bottles of nothing-yet, Vera. My "
            "anvil is embarrassed for you. And now this one walks up in "
            "the middle of it - you. Book-holder. Word is you DECIDE "
            "things now. So decide this.", "next": "n3"},
        "n3": {"speaker": "VERA", "text":
            "Oh, splendid, yes. A ruling. Is my work a lie, or is it "
            "simply... early?",
            "choices": [
                {"label": "Early. And today the possibilities arrive. Come with me and prove it.",
                 "next": "n_vera",
                 "effects": [("flag", "vera_joined_early"),
                             ("flag", "griselda_grudge"), ("points", 1)]},
                {"label": "Griselda's right. A shop should sell things that work.",
                 "next": "n_gris",
                 "effects": [("flag", "vera_grudge"),
                             ("flag", "griselda_friend"), ("points", 1)]},
                {"label": "[ALCHEMY] Ask Vera what is actually IN the tonics.",
                 "req": ("tag", "ALCHEMY"), "next": "n_alch"},
            ]},
        "n_alch": {"speaker": "VERA", "text":
            "In them? River water, crushed waxwing shell, and one (1) "
            "genuine unresolved hope. Which has kept perfectly, thank you, "
            "because nothing in this vale ever resolves.", "next": "n3b"},
        "n3b": {"speaker": "GRISELDA", "text":
            "...That's the most honest ingredient list I've ever heard. "
            "Doesn't make it medicine.", "next": "n3c"},
        "n3c": {"speaker": "NARRATOR", "text": "Decide it, then.",
            "choices": [
                {"label": "Early. Come with me, Vera - let's resolve a hope.",
                 "next": "n_vera",
                 "effects": [("flag", "vera_joined_early"),
                             ("flag", "griselda_grudge"), ("points", 1)]},
                {"label": "Side with Griselda.",
                 "next": "n_gris",
                 "effects": [("flag", "vera_grudge"),
                             ("flag", "griselda_friend"), ("points", 1)]},
            ]},
        "n_vera": {"speaker": "VERA", "text":
            "HA! You hear that, Griselda? Inventory ahead of its time - "
            "and time just caught up. I'll get my satchel.", "next": "n_v2"},
        "n_v2": {"speaker": "GRISELDA", "text":
            "Fine. FINE. But book-holder - my prices just went up for "
            "people who encourage her. Ask me if I'm joking.", "next": "n_v3"},
        "n_v3": {"speaker": "NARRATOR", "text":
            "VERA joins the party! Griselda's prices did, in fact, go up.",
            "action": "recruit:VERA:2", "next": "n_end"},
        "n_gris": {"speaker": "GRISELDA", "text":
            "Hm. Sense. Didn't expect sense in the same week as all this "
            "deciding.", "next": "n_g2"},
        "n_g2": {"speaker": "VERA", "text":
            "...I see. Well. When something is finally POSSIBLE around "
            "here, you will both owe me an apology, and I intend to "
            "collect it with interest.", "next": "n_g3"},
        "n_g3": {"speaker": "NARRATOR", "text":
            "Vera snaps her stall shut and marches off toward the dock. "
            "Griselda watches her go, and for just a moment the axe stops "
            "moving on the whetstone.", "next": "n_end"},
        "n_end": {"speaker": "NARRATOR", "text":
            "The Book hums. First real decision with two faces on it. "
            "They both go in.", "action": "end"},
    },
},

# ------------------------------------------------------------ Ferryman Odd
"odd_ferry_1": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "ODD", "text":
            "One route. There and back. You'd think the water would get "
            "bored. Water doesn't. I checked.",
            "choices": [
                {"label": "Take the ferry to the Gearwood.", "next": "n2",
                 "req": ("flag", "door_open")},
                {"label": "Not yet.", "next": "n_no"},
            ]},
        "n_no": {"speaker": "ODD", "text":
            "Suit yourself. The barge and I will be here. That's the one "
            "thing we're really good at.", "action": "end"},
        "n2": {"speaker": "ODD", "text":
            "Gearwood, then. Hop on. Mind the planks - they're blank on "
            "purpose.", "next": "n3"},
        "n3": {"speaker": "NARRATOR", "text":
            "The barge slides out. Hollowbrook shrinks behind you. Odd "
            "poles in silence for a while, then, without turning around:",
            "next": "n4"},
        "n4": {"speaker": "ODD", "text":
            "The door. Forty years of shut, and you're the one who made it "
            "a going-through door again. Why'd you do it - for the town, "
            "or because you wanted to see the other side?",
            "choices": [
                {"label": "For the town. They've waited long enough.",
                 "next": "n5a", "effects": [("flag", "odd_answer_town")]},
                {"label": "For me. I wanted to see.",
                 "next": "n5b", "effects": [("flag", "odd_answer_self")]},
            ]},
        "n5a": {"speaker": "ODD", "text":
            "Hm. Generous.", "next": "n6"},
        "n5b": {"speaker": "ODD", "text":
            "Hm. Honest.", "next": "n6"},
        "n6": {"speaker": "NARRATOR", "text":
            "He pulls a stub of charcoal from his coat and writes one small "
            "word on one blank plank, among hundreds of blank planks. You "
            "cannot see which word. The barge bumps the Gearwood dock.",
            "action": "goto_area:gearwood:from_ferry"},
    },
},

"odd_ferry_back": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "ODD", "text":
            "Back across?",
            "choices": [
                {"label": "To Hollowbrook.", "next": "n2"},
                {"label": "Stay a while longer.", "next": "n_no"},
            ]},
        "n_no": {"speaker": "ODD", "text":
            "The wood keeps. Take your time.", "action": "end"},
        "n2": {"speaker": "NARRATOR", "text":
            "The water knows the way. Odd barely poles at all.",
            "action": "goto_area:hollowbrook:from_ferry"},
    },
},

# ------------------------------------------------------------ the Gearwood
"gearwood_bell_1": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "In the clearing stands a small red figure, hands folded, "
            "immaculate among the moss. It was not there a moment ago. "
            "Standing is somehow the politest thing you have ever seen "
            "done.", "next": "n2"},
        "n2": {"speaker": "BELL", "text":
            "Good morning. Please don't be alarmed. Alarm is untidy.",
            "next": "n3"},
        "n3": {"speaker": "BELL", "text":
            "I am called Bell. I serve the Custodian, who keeps the vale "
            "complete, clean, and pending. You are the... decision that "
            "has been happening. It is my duty to observe you.",
            "choices": [
                {"label": "Pending? The vale is ASLEEP.", "next": "n4"},
                {"label": "Observe away. We're not stopping.", "next": "n5"},
            ]},
        "n4": {"speaker": "BELL", "text":
            "Asleep is such a heavy word. We prefer 'pending.' A pending "
            "thing is perfect, you see. It has not had the chance to go "
            "wrong yet. Every story that starts, starts to end.",
            "next": "n6"},
        "n5": {"speaker": "BELL", "text":
            "No. I don't suppose you are. How interesting. I have never "
            "observed anything interesting before. I will need to sit "
            "down afterward.", "next": "n6"},
        "n6": {"speaker": "BELL", "text":
            "Do enjoy the wood. The moss is maintained to a very high "
            "standard. And - a personal remark, if permitted: whatever "
            "you are doing to the vale... it is being noticed. Tidiness "
            "has a custodian. Now so does mess.", "next": "n7"},
        "n7": {"speaker": "NARRATOR", "text":
            "Bell bows, precisely, and is not there anymore. The moss "
            "where it stood is very slightly neater.",
            "effects": [("flag", "bell_1_done")], "action": "end"},
    },
},

"moth_shrine": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "A cold shrine. A brazier that has never been lit crouches "
            "over three centuries of ready kindling. Beside it kneels a "
            "figure in a lamplighter's hat, wick-pole across their knees.",
            "next": "n2"},
        "n2": {"speaker": "MOTH", "text":
            "Don't mind me. I'm on duty. Order of the Wick, third watch. "
            "We keep the lights ready for when someone names what they're "
            "for. Nobody ever has. It's steady work.", "next": "n3"},
        "n3": {"speaker": "PIP", "text":
            "You've waited your whole life to light THAT brazier?",
            "next": "n4"},
        "n4": {"speaker": "MOTH", "text":
            "My whole life, my predecessor's, and hers before that. The "
            "flame's easy. Any fool with a flint can make fire. The Order "
            "waits for the HARD part: a light has to be FOR something, or "
            "it's just... burning.",
            "choices": [
                {"label": "Then light it for the ones walking in the dark.",
                 "next": "n_dark",
                 "effects": [("flag", "moth_light_name_dark"), ("points", 1)]},
                {"label": "Light it for everything the vale has lost waiting.",
                 "next": "n_lost",
                 "effects": [("flag", "moth_light_name_lost"), ("points", 1)]},
                {"label": "Light it for small things. Suppers. Mending. Company.",
                 "next": "n_small",
                 "effects": [("flag", "moth_light_name_small"), ("points", 1)]},
            ]},
        "n_dark": {"speaker": "MOTH", "text":
            "...For the ones walking in the dark. Three hundred years and "
            "it was seven words. Stand back, please. This is a "
            "professional matter.", "next": "n5"},
        "n_lost": {"speaker": "MOTH", "text":
            "...For everything lost waiting. Oh, that one WEIGHS. Good. "
            "A light should weigh. Stand back, please.", "next": "n5"},
        "n_small": {"speaker": "MOTH", "text":
            "...Suppers. Mending. Company. My grandmother held this post "
            "sixty years hoping it would be something like that. Stand "
            "back, please.", "next": "n5"},
        "n5": {"speaker": "NARRATOR", "text":
            "Moth strikes the wick. The brazier takes the flame like a "
            "held breath let go - and for one moment every shadow in the "
            "Gearwood leans toward the shrine, as if to hear its name.",
            "next": "n6"},
        "n6": {"speaker": "MOTH", "text":
            "Well. That's my whole vocation complete before lunch. "
            "...Unless. You're the decider, aren't you? The vale's going "
            "to need more lights named. Take me with you. I'm a "
            "lamplighter with one lamp lit - I am EXACTLY the person this "
            "story needs.", "next": "n7"},
        "n7": {"speaker": "NARRATOR", "text":
            "MOTH joins the party! The shrine stays lit behind you. It "
            "will stay lit from now on. That is simply true, and the "
            "whole wood knows it.",
            "effects": [("flag", "moth_joined"), ("points", 1)],
            "action": "recruit:MOTH:2"},
    },
},

"shrine_chest": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "The shrine's offering chest. The waxwings guarded it on "
            "instinct - even instinct runs on schedule here. Inside: a "
            "brass key, cool and heavy, and a little travel money.",
            "effects": [("item", "brass_key", 1), ("gold", 35),
                        ("item", "red_tonic", 1),
                        ("flag", "shrine_chest_open")],
            "action": "end"},
    },
},

"gearwood_stair": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "A door in the hillside, iron-bound, with a brass lock kept "
            "polished by nobody. Cold air breathes up through the seam. "
            "Stairs go DOWN.",
            "choices": [
                {"label": "Unlock it with the brass key.", "next": "n2",
                 "req": ("flag", "shrine_chest_open")},
                {"label": "Leave it for now.", "next": "n_no"},
            ]},
        "n_no": {"speaker": "NARRATOR", "text":
            "The dark under the vale keeps. It's had practice.",
            "action": "end"},
        "n2": {"speaker": "NARRATOR", "text":
            "The key turns like it was oiled yesterday. Of course it was. "
            "Everything here is maintained. Nothing here is used. You "
            "descend into the Undercroft.",
            "effects": [("flag", "undercroft_open"), ("act", 2)],
            "action": "goto_area:undercroft:enter"},
    },
},

# ------------------------------------------------------------------- camps
"fountain_rest": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "NARRATOR", "text":
            "The fountain basin is dry, but the stone remembers water. "
            "The party rests. Wounds close. The Book sits open on the rim, "
            "sunning its blank pages.",
            "effects": [], "action": "heal_party", "next": "n2"},
        "n2": {"speaker": "NARRATOR", "text":
            "Rearrange the party?",
            "choices": [
                {"label": "Yes - choose who walks ahead.", "next": "n3"},
                {"label": "No, we're set.", "next": "n_end"},
            ]},
        "n3": {"speaker": "NARRATOR", "text": "", "action": "swap_menu",
               "next": "n_end"},
        "n_end": {"speaker": "NARRATOR", "text":
            "Ready.", "action": "end"},
    },
},

"shrine_rest": {
    "start": "n1",
    "nodes": {
        "n1": {"speaker": "MOTH", "text":
            "Rest by the light. That's what it's for. Among other things.",
            "action": "heal_party", "next": "n2"},
        "n2": {"speaker": "NARRATOR", "text":
            "Rearrange the party?",
            "choices": [
                {"label": "Yes.", "next": "n3"},
                {"label": "No.", "next": "n_end"},
            ]},
        "n3": {"speaker": "NARRATOR", "text": "", "action": "swap_menu",
               "next": "n_end"},
        "n_end": {"speaker": "NARRATOR", "text": "Ready.", "action": "end"},
    },
},

}
