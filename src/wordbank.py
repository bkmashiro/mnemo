"""Word bank for mnemonic encoding.

Each part-of-speech category has exactly 256 words, allowing
each word to encode exactly one byte. Words are chosen for:
- Distinctiveness (no near-homophones within a category)
- Memorability (concrete, vivid, imageable)
- Pronounceability (common English phonotactics)

Categories are built in priority order (noun, verb, adjective, determiner)
to ensure complete disjointness — no word appears in more than one category.

The seed numbers 8695 8355 1302 1106 5381 6271 1115 5648 1645 847
2312 4910 5017 3354 7805 2032 are used to derive the shuffled
ordering via a deterministic PRNG, ensuring reproducible mappings.
"""

from __future__ import annotations
import hashlib
import struct
from typing import Dict, List, Tuple


# Seed numbers from the project specification
SEEDS = [8695, 8355, 1302, 1106, 5381, 6271, 1115, 5648,
         1645, 847, 2312, 4910, 5017, 3354, 7805, 2032]


def _seed_shuffle(words: List[str], category_salt: str) -> List[str]:
    """Deterministically shuffle a word list using seed numbers.

    Uses the seed numbers to create a reproducible permutation
    via a keyed hash chain.
    """
    seed_bytes = b"".join(struct.pack(">H", s) for s in SEEDS)
    key = hashlib.sha256(seed_bytes + category_salt.encode()).digest()

    decorated = []
    for i, word in enumerate(words):
        h = hashlib.sha256(key + struct.pack(">I", i)).digest()
        decorated.append((h, word))
    decorated.sort(key=lambda x: x[0])
    return [w for _, w in decorated]


# --- Raw word pools ---
# Each pool has well over 256 entries. During build, words are claimed
# by categories in priority order (noun > verb > adjective > determiner)
# so overlapping words go to the highest-priority category.

_RAW_NOUNS = [
    # Animals
    "fox", "owl", "bear", "deer", "wolf", "hawk", "lynx", "crow",
    "frog", "moth", "crab", "swan", "dove", "hare", "mole", "newt",
    "pike", "wren", "lark", "bass", "colt", "duck", "goat", "lamb",
    "mare", "pony", "seal", "wasp", "yak", "ape", "bat", "bee",
    "cat", "cod", "cow", "dog", "eel", "elk", "fly", "gnu",
    "hen", "hog", "jay", "koi", "ant", "ray", "ram", "rat",
    # Plants
    "oak", "elm", "fir", "yew", "bay", "fig", "hop",
    "ivy", "nut", "pea", "rue", "rye", "sage", "vine", "reed",
    # Nature
    "moon", "star", "rain", "snow", "wind", "dawn", "dusk", "mist",
    "lake", "cave", "hill", "vale", "glen", "peak", "ford", "cove",
    # Instruments
    "drum", "harp", "horn", "bell", "gong", "lute", "pipe", "fife",
    # Objects
    "bolt", "gear", "coil", "disc", "knob", "lens", "vent", "tube",
    "arch", "dome", "gate", "wall", "moat", "maze", "path", "road",
    "coin", "ring", "crown", "card", "dice", "mask", "robe", "cape",
    "book", "page", "knot", "rope", "flag", "lamp",
    "orb", "gem", "opal", "gold",
    # Materials
    "flame", "spark", "coal", "dust", "sand", "clay", "moss",
    "root", "stem", "leaf", "bark", "thorn", "seed", "bloom", "petal",
    "wave", "tide", "reef", "crest", "foam", "shell", "kelp", "pearl",
    "cloud", "haze", "frost", "gale", "hail", "sleet", "fog",
    # Fantasy/Abstract
    "cairn", "rune", "glyph", "sigil", "ward", "tome", "wand", "staff",
    "forge", "anvil", "blade", "helm", "spur", "chain", "latch", "hinge",
    "prism", "node", "mesh", "grid", "axis", "loop", "arc",
    "pulse", "chord", "scale", "tone", "beat", "rest", "note", "hymn",
    "quest", "trial", "pledge", "vow", "rite", "creed", "oath", "pact",
    "ridge", "cliff", "gorge", "marsh", "dune", "mesa", "bluff", "dell",
    "spire", "vault", "nave", "crypt", "tower", "keep", "hall", "court",
    "mill", "well", "dock", "barn", "shed", "kiln", "loom", "press",
    "brine", "mead", "broth", "whey", "balm", "salve", "paste", "glaze",
    "plume", "claw", "fang", "mane", "tusk", "fin", "tail",
    "shard", "flint", "quartz", "slate", "chalk", "pumice", "basalt", "shale",
    "atlas", "chart", "ledger", "scroll", "cipher", "index", "proof", "draft",
    "pixel", "byte", "frame", "cache", "stack", "queue", "heap",
    # Extra
    "ash", "jade", "onyx", "ruby", "zinc", "quill",
    "acre", "aisle", "badge", "bench", "braid", "canoe", "cloak", "crate",
    "depot", "ditch", "easel", "flute", "gulch", "ivory", "jetty", "notch",
]

_RAW_VERBS = [
    "chase", "guard", "build", "carve", "climb", "dance", "drive",
    "fetch", "float", "grasp", "greet", "guide", "haunt", "heave",
    "honor", "judge", "kneel", "launch", "learn", "march", "mend", "mount",
    "nudge", "paint", "parse", "patch", "place", "plant", "pluck", "pound",
    "prove", "purge", "quote", "raise", "reach", "reign", "roast",
    "scout", "shape", "share", "shift", "shine", "shout", "shove", "slash",
    "slide", "solve", "spend", "split", "spray", "stage",
    "stain", "stalk", "steal", "steer", "sting", "stitch", "store", "storm",
    "strain", "strip", "strum", "study", "sweep", "swing", "teach", "thank",
    "think", "throw", "touch", "trace", "track", "trade", "train", "trap",
    "treat", "trust", "twist", "unite", "visit", "voice", "waste",
    "watch", "weave", "wield", "wound", "write", "yield", "adopt", "align",
    "amend", "apply", "avoid", "award", "blend", "block", "boost", "brace",
    "brand", "break", "breed", "bring", "brush", "burst", "catch", "cause",
    "check", "churn", "claim", "clasp", "clean", "clear", "click",
    "close", "coach", "count", "cover", "crack", "craft", "crash", "crawl",
    "crush", "cycle", "debug", "delay", "delve", "drain", "dream",
    "dress", "drift", "drill", "drink", "embed", "erase", "evade", "exalt",
    "feast", "fight", "fling", "flood", "flush", "focus", "force", "found",
    "graft", "grant", "grind", "group", "growl",
    "guess", "hatch", "hoist", "house", "hurry",
    "imply", "input", "layer", "leach", "light",
    "lodge", "lower", "merge", "model", "morph", "nurse", "offer",
    "order", "outdo", "phase", "pitch", "pivot", "plead", "plumb", "point",
    "poach", "power", "prank", "price", "prime", "print", "probe",
    "prune", "query", "rally", "range", "react", "relax",
    "renew", "rival", "route", "savor", "scald", "scour", "seize", "sense",
    "serve", "sever", "shade", "siege", "singe", "skate", "skulk", "slant",
    "sleek", "sling", "smelt", "snare", "sober", "spawn", "spear",
    "spell", "spill", "spoke", "squat", "stamp", "start", "steam", "steep",
    "stoke", "stoop", "stow", "surge", "swear", "taint", "tempt", "thaw",
    "toast", "topple", "tread", "trim", "tryst", "tutor", "usher", "value",
    "venom", "vigor", "vouch", "wager", "weigh", "whisk", "wring",
    "yearn", "yodel", "allot", "annex", "atone",
    # Extra
    "abide", "clamp", "cling", "covet", "deter", "dwell", "ensue", "flail",
    "glean", "gouge", "grope", "hover", "infer", "joust", "knead", "lunge",
    "mourn", "ogle", "plod", "quash", "rouse", "saute", "scoff", "seeth",
    "shrug", "skulk", "snarl", "spurn", "stake", "sulk", "usurp", "wince",
]

_RAW_ADJECTIVES = [
    "quick", "brave", "calm", "eager", "fair", "gentle", "happy",
    "idle", "just", "keen", "lame", "meek", "neat", "odd",
    "quiet", "rare", "safe", "tall", "ugly", "young",
    "zesty", "able", "dull", "evil", "fast", "glad",
    "icy", "kind", "lazy", "nice",
    "used", "vain", "weak", "wise",
    "aged", "blue", "fine", "good",
    "joint", "known", "main", "new", "open",
    "real", "tiny", "valid",
    "acute", "bleak", "crisp", "elite", "grand",
    "jolly", "moist", "noble",
    "proud", "royal", "weird",
    "youthful", "zealous", "brisk",
    "dizzy", "empty", "fluid", "grim", "heavy", "jumpy",
    "khaki", "loose", "magic", "nasal", "oaken", "plump", "quaint",
    "rigid", "solid", "tense", "vital",
    "yearly", "zippy", "alien", "glossy", "hilly", "inert", "juicy", "livid",
    "muddy", "nerdy", "pasty", "roomy", "sandy",
    "tidal", "uncut", "vinyl", "xeric", "yummy", "zonal",
    "burnt", "cubic", "elfin", "fiery", "gaudy",
    "husky", "ionic", "jazzy", "leafy", "nutty",
    "optic", "peach", "toxic",
    "vocal", "windy", "eerie", "flaky", "grimy", "humid", "irate",
    "jaded", "lilac", "maize", "ochre",
    "regal", "snowy", "totem", "unlit", "vegan", "woven",
    "agate", "hazel", "lemon",
    "tiger", "yacht",
    "gleam", "honey",
    "mossy", "nylon", "radar",
    "wired", "rapid", "molten", "lucid", "giant", "dwarf",
    "blunt", "avian", "plush", "modal",
    "lumpy", "feral",
    "gauze", "blaze", "murky", "tangy", "balmy", "lanky",
    "peppy", "rowdy", "soggy", "wacky", "bushy", "curly",
    "dainty", "edgy", "funky", "giddy", "hasty", "itchy",
    "jerky", "lousy", "moody", "noisy", "perky", "raspy",
    "shaky", "tacky", "uptight", "vivid", "whiny", "zappy",
    "beady", "cagey", "dopey", "fizzy", "goofy", "hefty",
    "jumbo", "kinky", "mangy", "nippy", "pouty", "rustic",
    "sappy", "tubby", "woozy", "yucky", "buggy", "chunky",
    "dinky", "fussy", "gusty", "huffy", "jiffy", "knobby",
    "loopy", "messy", "nifty", "picky", "quirky", "ratty",
    "stuffy", "teeny", "wonky", "puffy", "dorky", "corny",
    "bumpy", "dusty", "foggy", "leaky", "silky", "rusty",
    "amber", "coral", "olive", "ivory", "scarlet", "violet",
    "crimson", "maroon", "indigo", "tawny", "khaki", "beige",
    "ashen", "ruddy", "sallow", "florid", "pallid", "dusky",
    "steamy", "breezy", "stormy", "frosty", "misty", "sunny",
    "starry", "tropic", "arctic", "boreal",
    "clammy", "cranky", "dreary", "feisty", "frilly", "grumpy",
    "hoarse", "minty", "mousy", "ornate", "plucky", "prissy",
    "scrawny", "snappy", "spooky", "swanky", "thorny", "twisty",
    "whimsy", "woolly", "frothy", "grainy",
]

_RAW_DETERMINERS = [
    "the", "one", "two", "six", "ten", "few", "all", "any",
    "each", "half", "both", "some", "many", "most", "more", "much",
    "last", "next", "past", "same", "such", "this", "that", "what",
    "pure", "full", "null", "void", "dual", "sole", "mere", "true",
    "first", "third", "fifth", "ninth", "every", "other", "whole", "extra",
    "prior", "final", "chief",
    "front", "back", "left", "right", "near", "far",
    "high", "low", "top", "mid", "base", "core", "edge",
    "north", "south", "east", "west", "noon", "late",
    "dark", "bright", "soft", "hard", "raw", "dry", "wet", "hot",
    "cold", "warm", "cool", "mild", "deep", "wide", "long", "short",
    "big", "small", "large", "vast", "slim", "broad", "narrow",
    "thick", "thin", "dense", "sparse", "flat", "curved", "sharp",
    "smooth", "rough", "matte", "sheer", "stark", "plain", "blank",
    "faint", "bold", "pale", "rich", "poor", "cheap", "dear",
    "sweet", "sour", "salt", "fresh", "stale", "ripe", "crude",
    "oily", "waxy", "fuzzy", "grainy", "gritty",
    "hazy", "smoky", "ebony",
    "brass", "copper", "silver", "golden", "bronze", "chrome", "pewter", "iron", "lead",
    "cedar", "birch", "maple", "pine", "teak",
    "linen", "cotton", "velvet", "satin", "denim", "suede", "tweed", "hemp",
    "neon", "laser", "sonic", "solar", "astral", "cosmic",
    "alpine", "marine", "delta", "sigma", "omega", "gamma", "theta", "kappa",
    "micro", "macro", "hyper", "ultra", "proto", "quasi", "semi", "meta",
    "retro", "neo", "post", "anti", "over", "under", "cross", "inter",
    "super", "sub", "non", "pan", "poly", "mono", "bi", "tri",
    "quad", "hex", "octa", "deca", "giga", "mega", "kilo", "nano",
    "pico", "tera", "zeta", "beta", "eta", "iota", "mu", "nu",
    "phi", "psi", "chi", "rho", "tau", "xi", "pi", "omicron",
    "apex", "flux", "lux", "vex",
    "crux", "nexus", "zenith", "nadir", "epoch", "cusp", "brink",
    "verge", "fringe", "trough", "ebb",
    # Extra
    "above", "below", "inner", "outer", "upper",
    "minor", "major", "focal", "basal", "distal", "dorsal", "ventral",
    "primal", "maxim", "minim", "total", "gross", "petit",
    "local", "modal", "nodal", "tonal", "zonal", "axial",
    "aural", "nasal", "renal", "vital", "vocal", "rural",
    "urban", "civic", "toxic", "lucid", "tepid", "fetid",
    "rabid", "acrid", "vapid", "livid", "vivid", "timid",
    "rigid", "valid", "molar", "solar", "lunar",
    "polar", "legal", "regal", "royal", "loyal",
    "final", "fatal", "natal", "canal",
]


class WordBank:
    """Manages the word-to-byte and byte-to-word mappings for each POS category."""

    CATEGORIES = ("adjective", "noun", "verb", "determiner")

    # Build order: nouns first (most concrete), then verbs, adjectives, determiners
    _BUILD_ORDER = ("noun", "verb", "adjective", "determiner")

    def __init__(self) -> None:
        self._word_to_byte: Dict[str, Dict[str, int]] = {}
        self._byte_to_word: Dict[str, Dict[int, str]] = {}
        self._build()

    def _build(self) -> None:
        raw_pools = {
            "adjective": _RAW_ADJECTIVES,
            "noun": _RAW_NOUNS,
            "verb": _RAW_VERBS,
            "determiner": _RAW_DETERMINERS,
        }

        # Track globally claimed words to ensure disjointness
        claimed: set = set()

        for category in self._BUILD_ORDER:
            raw = raw_pools[category]

            # Deduplicate within category, preserving order
            seen: set = set()
            unique = []
            for w in raw:
                w_lower = w.lower().strip()
                if w_lower not in seen and w_lower not in claimed:
                    seen.add(w_lower)
                    unique.append(w_lower)

            # Shuffle deterministically with seed
            shuffled = _seed_shuffle(unique, category)

            # Take exactly 256
            if len(shuffled) < 256:
                raise ValueError(
                    f"Category '{category}' has only {len(shuffled)} unique "
                    f"non-overlapping words, need 256"
                )
            words = shuffled[:256]

            # Claim these words
            claimed.update(words)

            self._byte_to_word[category] = {i: w for i, w in enumerate(words)}
            self._word_to_byte[category] = {w: i for i, w in enumerate(words)}

    def encode_byte(self, category: str, value: int) -> str:
        """Convert a byte value (0-255) to a word in the given category."""
        if category not in self._byte_to_word:
            raise ValueError(f"Unknown category: {category}")
        if not 0 <= value <= 255:
            raise ValueError(f"Byte value out of range: {value}")
        return self._byte_to_word[category][value]

    def decode_word(self, category: str, word: str) -> int:
        """Convert a word back to its byte value, validating it belongs to the category."""
        word = word.lower().strip()
        if category not in self._word_to_byte:
            raise ValueError(f"Unknown category: {category}")
        if word not in self._word_to_byte[category]:
            return -1  # Signal: word not in this category
        return self._word_to_byte[category][word]

    def identify_category(self, word: str) -> str | None:
        """Identify which POS category a word belongs to, or None if unknown."""
        word = word.lower().strip()
        for cat in self.CATEGORIES:
            if word in self._word_to_byte[cat]:
                return cat
        return None

    def words_for_category(self, category: str) -> List[str]:
        """Return all 256 words for a category in byte-order."""
        return [self._byte_to_word[category][i] for i in range(256)]

    def all_words(self) -> Dict[str, List[str]]:
        """Return all words grouped by category."""
        return {cat: self.words_for_category(cat) for cat in self.CATEGORIES}
