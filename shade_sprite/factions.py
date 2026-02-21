"""Faction generation system for procedural army/group creation.

A Faction is a top-level group with a species, biome, element, and aesthetic.
Each faction contains several Roles -- visually and mechanically distinct unit
types with unique appearances built from the faction's species layers.

Key design: clothes, hair, and skin hues are per-ROLE, not per-faction.
The faction defines species and aesthetic; roles define visual specifics.

Usage:
    from shade_sprite.factions import FactionGenerator
    from shade_sprite.assets import AssetLibrary
    from shade_sprite.assembler import CharacterAssembler

    lib = AssetLibrary()
    gen = FactionGenerator(seed=42, library=lib)
    recipe = gen.generate()

    assembler = CharacterAssembler()
    textures = recipe.build_role_textures(assembler)
    # textures["melee_fighter"] -> mcrfpy.Texture
"""
import random
from dataclasses import dataclass, field
from enum import Enum

from .assets import AssetLibrary


# ---------------------------------------------------------------------------
# Domain enums
# ---------------------------------------------------------------------------

class Biome(Enum):
    ICE = "ice"
    SWAMP = "swamp"
    GRASSLAND = "grassland"
    SCRUBLAND = "scrubland"
    FOREST = "forest"


class Element(Enum):
    FIRE = "fire"
    WATER = "water"
    STONE = "stone"
    AIR = "air"


class Aesthetic(Enum):
    SLAVERY = "slavery"
    MILITARISTIC = "militaristic"
    COWARDLY = "cowardly"
    FANATICAL = "fanatical"


class RoleType(Enum):
    MELEE_FIGHTER = "melee_fighter"
    RANGED_FIGHTER = "ranged_fighter"
    SPELLCASTER = "spellcaster"
    HEALER = "healer"
    PET_RUSHER = "pet_rusher"
    PET_FLANKER = "pet_flanker"


# ---------------------------------------------------------------------------
# Aesthetic -> role generation templates
# ---------------------------------------------------------------------------

# Each aesthetic defines which roles are generated and their relative counts.
# The generator picks from these to produce 3-5 roles per faction.
_AESTHETIC_ROLE_POOLS = {
    Aesthetic.MILITARISTIC: [
        RoleType.MELEE_FIGHTER,
        RoleType.MELEE_FIGHTER,
        RoleType.RANGED_FIGHTER,
        RoleType.RANGED_FIGHTER,
        RoleType.HEALER,
    ],
    Aesthetic.FANATICAL: [
        RoleType.SPELLCASTER,
        RoleType.SPELLCASTER,
        RoleType.MELEE_FIGHTER,
        RoleType.HEALER,
        RoleType.PET_RUSHER,
    ],
    Aesthetic.COWARDLY: [
        RoleType.RANGED_FIGHTER,
        RoleType.PET_RUSHER,
        RoleType.PET_FLANKER,
        RoleType.PET_FLANKER,
        RoleType.HEALER,
    ],
    Aesthetic.SLAVERY: [
        RoleType.MELEE_FIGHTER,
        RoleType.RANGED_FIGHTER,
        RoleType.SPELLCASTER,
        RoleType.PET_RUSHER,
        RoleType.PET_FLANKER,
    ],
}

# Headgear class mapping for roles
_ROLE_HEADGEAR_CLASS = {
    RoleType.MELEE_FIGHTER: "melee",
    RoleType.RANGED_FIGHTER: "range",
    RoleType.SPELLCASTER: "mage",
    RoleType.HEALER: "mage",
    RoleType.PET_RUSHER: None,   # pets/allies don't get headgear
    RoleType.PET_FLANKER: None,
}

# Clothing style preferences per role
_ROLE_CLOTHING_STYLES = {
    RoleType.MELEE_FIGHTER: ["armour", "viking", "mongol"],
    RoleType.RANGED_FIGHTER: ["basic", "french", "japanese"],
    RoleType.SPELLCASTER: ["tunic", "basic"],
    RoleType.HEALER: ["tunic", "basic"],
    RoleType.PET_RUSHER: [],     # naked or minimal
    RoleType.PET_FLANKER: [],
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RoleDefinition:
    """A visually and mechanically distinct unit type within a faction.

    Attributes:
        role_type: The combat/function role
        species: Species name for this role (main or ally species)
        skin_hue: Hue shift for the skin layer (degrees)
        skin_sat: Saturation shift for the skin layer
        skin_lit: Lightness shift for the skin layer
        clothing_layers: List of (path, hue, sat, lit) tuples for clothing
        headgear_layer: Optional (path, hue, sat, lit) for headgear
        addon_layer: Optional (path, hue, sat, lit) for species add-ons
        hair_layer: Optional (path, hue, sat, lit) for hairstyle
        eye_layer: Optional (path, hue, sat, lit) for eyes
        shoe_layer: Optional (path, hue, sat, lit) for shoes
        glove_layer: Optional (path, hue, sat, lit) for gloves
        is_ally: True if this role uses an ally species (not the main species)
    """
    role_type: RoleType
    species: str
    skin_hue: float = 0.0
    skin_sat: float = 0.0
    skin_lit: float = 0.0
    clothing_layers: list = field(default_factory=list)
    headgear_layer: tuple = None
    addon_layer: tuple = None
    hair_layer: tuple = None
    eye_layer: tuple = None
    shoe_layer: tuple = None
    glove_layer: tuple = None
    is_ally: bool = False

    @property
    def label(self):
        """Human-readable label like 'melee_fighter (Human)'."""
        ally_tag = " [ally]" if self.is_ally else ""
        return f"{self.role_type.value} ({self.species}{ally_tag})"


@dataclass
class FactionRecipe:
    """A complete faction definition with species, aesthetic, and roles.

    Attributes:
        name: Display name for the faction
        biome: The biome this faction inhabits
        species: Main species name
        element: Elemental affinity
        aesthetic: Behavioral aesthetic
        ally_species: List of ally species names
        roles: List of RoleDefinitions
        seed: The seed used to generate this faction
    """
    name: str
    biome: Biome
    species: str
    element: Element
    aesthetic: Aesthetic
    ally_species: list = field(default_factory=list)
    roles: list = field(default_factory=list)
    seed: int = 0

    def build_role_textures(self, assembler):
        """Build one composite texture per role using CharacterAssembler.

        Args:
            assembler: A CharacterAssembler instance (format will be reused)
            library: An AssetLibrary to resolve species -> skin paths.
                     If None, skin layers must already be absolute paths in
                     the role's clothing_layers.

        Returns:
            dict[str, mcrfpy.Texture]: role label -> texture
        """
        import mcrfpy  # deferred import for headless testing without engine
        textures = {}
        for role in self.roles:
            assembler.clear()

            # Skin layer -- look up from library by species
            skin_path = role._skin_path
            if skin_path:
                assembler.add_layer(
                    skin_path, role.skin_hue, role.skin_sat, role.skin_lit)

            # Shoe layer
            if role.shoe_layer:
                path, h, s, l = role.shoe_layer
                assembler.add_layer(path, h, s, l)

            # Clothing layers
            for path, h, s, l in role.clothing_layers:
                assembler.add_layer(path, h, s, l)

            # Glove layer
            if role.glove_layer:
                path, h, s, l = role.glove_layer
                assembler.add_layer(path, h, s, l)

            # Add-on layer (species ears, horns, etc.)
            if role.addon_layer:
                path, h, s, l = role.addon_layer
                assembler.add_layer(path, h, s, l)

            # Hair layer
            if role.hair_layer:
                path, h, s, l = role.hair_layer
                assembler.add_layer(path, h, s, l)

            # Eye layer
            if role.eye_layer:
                path, h, s, l = role.eye_layer
                assembler.add_layer(path, h, s, l)

            # Headgear layer (on top)
            if role.headgear_layer:
                path, h, s, l = role.headgear_layer
                assembler.add_layer(path, h, s, l)

            tex_name = f"{self.name}_{role.label}".replace(" ", "_")
            textures[role.label] = assembler.build(tex_name)

        return textures


# ---------------------------------------------------------------------------
# Faction name generation
# ---------------------------------------------------------------------------

_FACTION_PREFIXES = [
    "Iron", "Shadow", "Dawn", "Ember", "Frost",
    "Vine", "Storm", "Ash", "Gold", "Crimson",
    "Azure", "Jade", "Silver", "Night", "Sun",
    "Bone", "Blood", "Thorn", "Dusk", "Star",
    "Stone", "Flame", "Void", "Moon", "Rust",
]

_FACTION_SUFFIXES = [
    "Guard", "Pact", "Order", "Clan", "Legion",
    "Court", "Band", "Wardens", "Company", "Oath",
    "Fleet", "Circle", "Hand", "Watch", "Speakers",
    "Reavers", "Chosen", "Vanguard", "Covenant", "Fang",
    "Spire", "Horde", "Shield", "Tide", "Crown",
]


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class FactionGenerator:
    """Deterministic faction generator driven by a seed and asset library.

    Args:
        seed: Integer seed for reproducible generation
        library: AssetLibrary instance (if None, creates one with auto-detection)
    """

    def __init__(self, seed, library=None):
        self.seed = seed
        self.library = library if library is not None else AssetLibrary()
        self._rng = random.Random(seed)

    def generate(self):
        """Produce a complete FactionRecipe with 3-5 roles.

        Returns:
            FactionRecipe with fully specified roles
        """
        rng = self._rng

        # Pick faction attributes
        biome = rng.choice(list(Biome))
        element = rng.choice(list(Element))
        aesthetic = rng.choice(list(Aesthetic))

        # Pick species
        available_species = self.library.species if self.library.available else [
            "Human", "Orc", "Demon", "Skeleton", "NightElf", "Cyclops"]
        species = rng.choice(available_species)

        # Pick 0-2 ally species (different from main)
        other_species = [s for s in available_species if s != species]
        n_allies = rng.randint(0, min(2, len(other_species)))
        ally_species = rng.sample(other_species, n_allies) if n_allies > 0 else []

        # Generate name
        name = rng.choice(_FACTION_PREFIXES) + " " + rng.choice(_FACTION_SUFFIXES)

        # Generate roles
        role_pool = list(_AESTHETIC_ROLE_POOLS[aesthetic])
        n_roles = rng.randint(3, min(5, len(role_pool)))
        chosen_role_types = rng.sample(role_pool, n_roles)

        # Base skin hue for the main species (random starting point)
        base_skin_hue = rng.uniform(0, 360)

        roles = []
        for i, role_type in enumerate(chosen_role_types):
            is_pet = role_type in (RoleType.PET_RUSHER, RoleType.PET_FLANKER)

            # Determine species for this role
            if is_pet and ally_species:
                role_species = rng.choice(ally_species)
                is_ally = True
            else:
                role_species = species
                is_ally = is_pet and not ally_species

            # Skin hue: small variation from base for same species
            if role_species == species:
                skin_hue = (base_skin_hue + rng.uniform(-15, 15)) % 360
            else:
                skin_hue = rng.uniform(0, 360)

            skin_sat = rng.uniform(-0.15, 0.15)
            skin_lit = rng.uniform(-0.1, 0.1)

            # For slavery aesthetic, allies get no clothes and dimmer skin
            naked = (aesthetic == Aesthetic.SLAVERY and is_ally)
            if naked:
                skin_lit = rng.uniform(-0.3, -0.1)

            role = RoleDefinition(
                role_type=role_type,
                species=role_species,
                skin_hue=skin_hue,
                skin_sat=skin_sat,
                skin_lit=skin_lit,
                is_ally=is_ally,
            )

            # Resolve actual layer files from the library
            self._assign_skin(role, role_species)
            if not naked:
                self._assign_clothing(role, role_type, rng)
                self._assign_headgear(role, role_type, rng)
                self._assign_hair(role, rng)
                self._assign_shoes(role, rng)
                self._assign_gloves(role, role_type, rng)
            self._assign_eyes(role, rng)
            self._assign_addons(role, role_species, rng)

            roles.append(role)

        return FactionRecipe(
            name=name,
            biome=biome,
            species=species,
            element=element,
            aesthetic=aesthetic,
            ally_species=ally_species,
            roles=roles,
            seed=self.seed,
        )

    # ---- Layer assignment helpers ----

    def _assign_skin(self, role, species):
        """Pick a skin layer file for the species."""
        skins = self.library.skins_for(species) if self.library.available else []
        if skins:
            chosen = self._rng.choice(skins)
            role._skin_path = chosen.path
        else:
            role._skin_path = None

    def _assign_clothing(self, role, role_type, rng):
        """Pick clothing appropriate to the role type."""
        if not self.library.available:
            return
        preferred_styles = _ROLE_CLOTHING_STYLES.get(role_type, [])
        candidates = []
        for style in preferred_styles:
            candidates.extend(self.library.clothes_by_style(style))
        if not candidates:
            candidates = self.library.clothes
        if not candidates:
            return

        chosen = rng.choice(candidates)
        clothing_hue = rng.uniform(0, 360)
        role.clothing_layers.append(
            (chosen.path, clothing_hue, 0.0, rng.uniform(-0.1, 0.05)))

    def _assign_headgear(self, role, role_type, rng):
        """Pick a headgear matching the role's combat class."""
        if not self.library.available:
            return
        hg_class = _ROLE_HEADGEAR_CLASS.get(role_type)
        if hg_class is None:
            return
        candidates = self.library.headgears_for_class(hg_class)
        if not candidates:
            candidates = self.library.headgears
        if not candidates:
            return

        chosen = rng.choice(candidates)
        role.headgear_layer = (chosen.path, 0.0, 0.0, 0.0)

    def _assign_hair(self, role, rng):
        """Pick a hairstyle (50% chance for humanoid roles)."""
        if not self.library.available:
            return
        if rng.random() < 0.5:
            return  # no hair / covered by headgear
        hairs = self.library.hairstyles
        if not hairs:
            return
        # Filter to just actual hairstyles (not facial), pick one
        head_hairs = [h for h in hairs if "Facial" not in h.subcategory]
        if not head_hairs:
            head_hairs = hairs
        chosen = rng.choice(head_hairs)
        role.hair_layer = (chosen.path, 0.0, 0.0, 0.0)

    def _assign_eyes(self, role, rng):
        """Pick an eye color (80% chance)."""
        if not self.library.available:
            return
        if rng.random() < 0.2:
            return
        eye_colors = self.library.layers_in("eyes", "Eye Color")
        if not eye_colors:
            return
        chosen = rng.choice(eye_colors)
        role.eye_layer = (chosen.path, 0.0, 0.0, 0.0)

    def _assign_shoes(self, role, rng):
        """Pick shoes (70% chance)."""
        if not self.library.available:
            return
        if rng.random() < 0.3:
            return
        shoes = self.library.shoes
        if not shoes:
            return
        chosen = rng.choice(shoes)
        role.shoe_layer = (chosen.path, 0.0, 0.0, 0.0)

    def _assign_gloves(self, role, role_type, rng):
        """Pick gloves for melee/ranged roles (40% chance)."""
        if not self.library.available:
            return
        if role_type not in (RoleType.MELEE_FIGHTER, RoleType.RANGED_FIGHTER):
            return
        if rng.random() < 0.6:
            return
        gloves = self.library.gloves
        if not gloves:
            return
        chosen = rng.choice(gloves)
        role.glove_layer = (chosen.path, 0.0, 0.0, 0.0)

    def _assign_addons(self, role, species, rng):
        """Pick species-specific add-ons if available."""
        if not self.library.available:
            return
        addons = self.library.addons_for(species)
        if not addons:
            return
        # 60% chance to add a species add-on
        if rng.random() < 0.4:
            return
        chosen = rng.choice(addons)
        role.addon_layer = (chosen.path, 0.0, 0.0, 0.0)
