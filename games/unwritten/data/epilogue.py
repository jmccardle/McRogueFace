"""UNWRITTEN - epilogue pages. Authored by Fable.

The epilogue is the Book read aloud. Full-screen INK panels, centered PARCH
text, GOLD page ornament, one keypress per page. PAGES is ordered; each entry
is (condition, text). condition: None = always shown, or a req tuple in the
dialogue schema (("flag", x) / ("flag_not", x) / ("points", n)). The renderer
shows every page whose condition passes. {light_name} is substituted from the
moth_light_name_* flag: dark -> "for the ones walking in the dark",
lost -> "for everything the vale lost waiting", small -> "for suppers, and
mending, and company"."""

PAGES = [
    (None,
     "This is the story of the vale,\nas it actually happened."),

    (None,
     "There was a door that was only ever a wall\nwith better manners. "
     "Someone decided\nit was for going through.\nSo it was."),

    (("flag", "quill_confident"),
     "The mayor of Hollowbrook said what a door was for,\nout loud, in his "
     "own words.\nHe has scheduled the Founding Festival.\nThe speech runs "
     "long. Nobody minds."),

    (("flag", "quill_dependent"),
     "The mayor of Hollowbrook waits, still,\nfor someone to say when. "
     "You say when.\nHe beams every time.\nThat is also a way to be a "
     "mayor,\nand the town loves him anyway."),

    (("flag", "vera_joined_early"),
     "A merchant sold possibility\nin a town that had none.\nShe was not "
     "wrong. She was early.\nThe difference was one believer."),

    (("flag", "vera_reconciled"),
     "Two shopkeepers quarreled for forty years\nabout whether hope keeps.\n"
     "It keeps. It kept.\nThe ledger had a column waiting all along."),

    (("flag", "vera_grudge"),
     "Somewhere a merchant still waits\nto collect an apology with "
     "interest.\nThe vale has time now. Real time,\nthe kind that goes "
     "somewhere.\nShe'll collect."),

    (("flag", "moth_joined"),
     "A brazier that waited three hundred years\nwas lit at last -\n"
     "{light_name}.\nIt has not gone out.\nIt is not going to."),

    (("flag", "cantor_joined"),
     "A fanfare built for the beginning\nplayed in the middle instead.\n"
     "The middle, it turns out,\nis a strong place for brass."),

    (("flag", "cantor_quiet"),
     "He was woken without a name,\nby a knock instead of a word.\nHe "
     "chose his own, later,\nand tells nobody.\nIt is a very good name."),

    (("flag", "gatekeeper_relieved"),
     "An old guard was formally relieved of duty\nby a knight who knew "
     "what the words cost.\nIt sleeps now, off schedule,\nand the deep "
     "vale breathes."),

    (("flag", "rewoke_quill"),
     "When the world was smoothed flat,\nthe people were woken\nnot by "
     "magic, but by particulars:\na thing only they had said,\na debt "
     "only they remembered,\na note only they were built to hold."),

    (("flag", "odd_promised"),
     "The ferryman has a second route now.\nIt is written on the hull\n"
     "in a hand that is not the Maker's,\nand the water - he reports -\n"
     "is showing signs of interest."),

    (("flag", "bell_defected"),
     "A herald spent three centuries\nannouncing silence,\nthen rang "
     "itself backward\nand chose a side.\nIt has SUCH a backlog."),

    (("flag", "nyx_joined"),
     "And there was someone\nwho was never anyone's later.\nShe stepped "
     "off the empty plinth\nand the plinth is empty on purpose now,\n"
     "which is a different thing entirely."),

    (("flag", "nyx_missed"),
     "There was someone else, almost.\nLook for her, next time.\nShe "
     "waits by the fountain,\nat the empty spot,\nand now you know to "
     "look."),

    (("flag", "book_read_custodian"),
     "The margin read the pages\nand chose to be a bookmark instead."),

    (None,
     "The Maker built the vale.\nYou were what happened."),
]

# Final card: the title UNWRITTEN, then the word UNWRITTEN gets struck
# through / replaced by WRITTEN stamped in GOLD. Hold on it. Roll nothing.
# There are no credits. The Book just closes.
