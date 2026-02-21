"""Unit tests for shade_sprite.factions and shade_sprite.assets modules."""
import mcrfpy
import sys
import os

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shade_sprite.assets import AssetLibrary, LayerFile, _parse_species_from_skin
from shade_sprite.factions import (
    FactionRecipe, FactionGenerator, RoleDefinition,
    Biome, Element, Aesthetic, RoleType,
    _AESTHETIC_ROLE_POOLS,
)
from shade_sprite.assembler import CharacterAssembler, TextureCache
from shade_sprite.formats import PUNY_29

errors = []


def test(name, condition, msg=""):
    if not condition:
        errors.append(f"FAIL: {name} - {msg}")
        print(f"  FAIL: {name} {msg}")
    else:
        print(f"  PASS: {name}")


# ===================================================================
# AssetLibrary tests
# ===================================================================
print("=== AssetLibrary ===")

lib = AssetLibrary()
has_assets = lib.available

test("AssetLibrary instantiates", lib is not None)
test("AssetLibrary repr", "AssetLibrary" in repr(lib))

if has_assets:
    print("  (Paid asset pack detected - running full asset tests)")

    test("has species", len(lib.species) > 0, f"got {lib.species}")
    test("Human in species", "Human" in lib.species,
         f"species: {lib.species}")
    test("Orc in species", "Orc" in lib.species)

    # Skins
    human_skins = lib.skins_for("Human")
    test("skins_for Human returns files", len(human_skins) > 0,
         f"got {len(human_skins)}")
    test("skin is LayerFile", isinstance(human_skins[0], LayerFile))
    test("skin has path", os.path.isfile(human_skins[0].path))
    test("skin category is skins", human_skins[0].category == "skins")

    # No skins for nonexistent species
    test("no skins for Alien", len(lib.skins_for("Alien")) == 0)

    # Categories
    cats = lib.categories
    test("has categories", len(cats) >= 5,
         f"got {len(cats)}: {cats}")
    test("skins in categories", "skins" in cats)
    test("clothes in categories", "clothes" in cats)

    # Clothes
    clothes = lib.clothes
    test("has clothes", len(clothes) > 0, f"got {len(clothes)}")

    # Subcategories
    clothes_subs = lib.subcategories("clothes")
    test("clothes has subcategories", len(clothes_subs) > 0,
         f"got {clothes_subs}")

    # clothes_by_style
    armour = lib.clothes_by_style("armour")
    test("armour clothes found", len(armour) > 0, f"got {len(armour)}")
    test("armour subcategory", "Armour" in armour[0].subcategory)

    # Headgears
    melee_hg = lib.headgears_for_class("melee")
    test("melee headgears found", len(melee_hg) > 0)
    mage_hg = lib.headgears_for_class("mage")
    test("mage headgears found", len(mage_hg) > 0)

    # Add-ons
    orc_addons = lib.addons_for("Orc")
    test("Orc add-ons found", len(orc_addons) > 0)
    elf_addons = lib.addons_for("Elf")
    test("Elf add-ons found", len(elf_addons) > 0)

    # Summary
    summary = lib.summary()
    test("summary has entries", len(summary) > 0)
    test("summary values are ints", all(isinstance(v, int) for v in summary.values()))

    # Shoes, gloves, etc.
    test("has shoes", len(lib.shoes) > 0)
    test("has gloves", len(lib.gloves) > 0)
    test("has hairstyles", len(lib.hairstyles) > 0)
    test("has eyes", len(lib.eyes) > 0)
    test("has headgears", len(lib.headgears) > 0)
    test("has addons", len(lib.addons) > 0)
else:
    print("  (No paid asset pack - running minimal tests)")
    test("unavailable lib has no species", len(lib.species) == 0)
    test("unavailable lib layers empty", len(lib.layers("skins")) == 0)
    test("unavailable lib summary empty", len(lib.summary()) == 0)


# ---- Species parsing ----
print("\n=== Species Parsing ===")

test("parse Human1 -> Human", _parse_species_from_skin("Human1") == "Human")
test("parse Human10 -> Human", _parse_species_from_skin("Human10") == "Human")
test("parse Orc2 -> Orc", _parse_species_from_skin("Orc2") == "Orc")
test("parse NightElf1 -> NightElf", _parse_species_from_skin("NightElf1") == "NightElf")
test("parse Cyclops1 -> Cyclops", _parse_species_from_skin("Cyclops1") == "Cyclops")
test("parse bare name -> itself", _parse_species_from_skin("Demon") == "Demon")


# ===================================================================
# FactionGenerator determinism tests
# ===================================================================
print("\n=== FactionGenerator Determinism ===")

gen1 = FactionGenerator(seed=42, library=lib)
recipe1 = gen1.generate()

gen2 = FactionGenerator(seed=42, library=lib)
recipe2 = gen2.generate()

test("same seed -> same name", recipe1.name == recipe2.name,
     f"'{recipe1.name}' vs '{recipe2.name}'")
test("same seed -> same biome", recipe1.biome == recipe2.biome)
test("same seed -> same species", recipe1.species == recipe2.species)
test("same seed -> same element", recipe1.element == recipe2.element)
test("same seed -> same aesthetic", recipe1.aesthetic == recipe2.aesthetic)
test("same seed -> same ally count", len(recipe1.ally_species) == len(recipe2.ally_species))
test("same seed -> same role count", len(recipe1.roles) == len(recipe2.roles))

# Check each role matches
for i, (r1, r2) in enumerate(zip(recipe1.roles, recipe2.roles)):
    test(f"role {i} same type", r1.role_type == r2.role_type)
    test(f"role {i} same species", r1.species == r2.species)
    test(f"role {i} same skin hue", abs(r1.skin_hue - r2.skin_hue) < 0.001,
         f"{r1.skin_hue} vs {r2.skin_hue}")

# Different seeds -> different results
gen3 = FactionGenerator(seed=99, library=lib)
recipe3 = gen3.generate()
# Not guaranteed to be different in every field, but extremely likely
# Check at least one attribute differs
differs = (recipe1.name != recipe3.name or
           recipe1.biome != recipe3.biome or
           recipe1.species != recipe3.species or
           recipe1.element != recipe3.element or
           recipe1.aesthetic != recipe3.aesthetic)
test("different seed -> likely different recipe", differs)


# ===================================================================
# FactionRecipe structure tests
# ===================================================================
print("\n=== FactionRecipe Structure ===")

test("recipe has name", isinstance(recipe1.name, str) and len(recipe1.name) > 0)
test("recipe has biome", isinstance(recipe1.biome, Biome))
test("recipe has element", isinstance(recipe1.element, Element))
test("recipe has aesthetic", isinstance(recipe1.aesthetic, Aesthetic))
test("recipe has species", isinstance(recipe1.species, str))
test("recipe has seed", recipe1.seed == 42)
test("recipe has 3-5 roles", 3 <= len(recipe1.roles) <= 5,
     f"got {len(recipe1.roles)}")


# ===================================================================
# Role generation counts by aesthetic
# ===================================================================
print("\n=== Role Counts by Aesthetic ===")

# Generate many factions to verify aesthetic influence on role pools
role_type_counts = {aesthetic: {} for aesthetic in Aesthetic}
for seed in range(100):
    gen = FactionGenerator(seed=seed, library=lib)
    recipe = gen.generate()
    aes = recipe.aesthetic
    for role in recipe.roles:
        rt = role.role_type
        role_type_counts[aes][rt] = role_type_counts[aes].get(rt, 0) + 1

# Militaristic should have more melee/ranged
mil = role_type_counts[Aesthetic.MILITARISTIC]
test("militaristic has melee fighters",
     mil.get(RoleType.MELEE_FIGHTER, 0) > 0)
test("militaristic has ranged fighters",
     mil.get(RoleType.RANGED_FIGHTER, 0) > 0)

# Fanatical should have spellcasters
fan = role_type_counts[Aesthetic.FANATICAL]
test("fanatical has spellcasters",
     fan.get(RoleType.SPELLCASTER, 0) > 0)

# Cowardly should have pets/flankers
cow = role_type_counts[Aesthetic.COWARDLY]
test("cowardly has pet flankers",
     cow.get(RoleType.PET_FLANKER, 0) > 0)

# Slavery should have pets (as enslaved allies)
slv = role_type_counts[Aesthetic.SLAVERY]
test("slavery has pet roles",
     slv.get(RoleType.PET_RUSHER, 0) + slv.get(RoleType.PET_FLANKER, 0) > 0)


# ===================================================================
# RoleDefinition skin hue variation
# ===================================================================
print("\n=== Skin Hue Variation ===")

# Within a single faction, main-species roles should have close but distinct hues
gen_hue = FactionGenerator(seed=7, library=lib)
recipe_hue = gen_hue.generate()

main_roles = [r for r in recipe_hue.roles if r.species == recipe_hue.species]
if len(main_roles) >= 2:
    hues = [r.skin_hue for r in main_roles]
    # Check that hues are distinct (not identical)
    unique_hues = len(set(round(h, 2) for h in hues))
    test("main species roles have distinct hues",
         unique_hues == len(hues),
         f"hues: {[f'{h:.1f}' for h in hues]}")

    # Check that hues are within reasonable range of each other (within 30 degrees)
    # The generator uses +/-15 degree variation from a base
    base_hue = sum(hues) / len(hues)
    all_close = all(
        min(abs(h - base_hue), 360 - abs(h - base_hue)) < 30
        for h in hues
    )
    test("main species hues are close (within 30 degrees of mean)",
         all_close, f"hues: {[f'{h:.1f}' for h in hues]}, mean: {base_hue:.1f}")
else:
    print(f"  SKIP: only {len(main_roles)} main-species roles (need >= 2 for hue test)")

# RoleDefinition label
test("role has label",
     "(" in recipe1.roles[0].label and ")" in recipe1.roles[0].label)


# ===================================================================
# RoleDefinition layer assignments (if assets available)
# ===================================================================
if has_assets:
    print("\n=== Layer Assignments ===")

    # Generate a faction and check that roles have actual file paths
    gen_layers = FactionGenerator(seed=55, library=lib)
    recipe_layers = gen_layers.generate()

    for i, role in enumerate(recipe_layers.roles):
        has_skin = role._skin_path is not None
        test(f"role {i} ({role.role_type.value}) has skin path", has_skin)
        if has_skin:
            test(f"role {i} skin file exists", os.path.isfile(role._skin_path))

        # Non-pet roles should generally have clothing
        if role.role_type not in (RoleType.PET_RUSHER, RoleType.PET_FLANKER):
            # Check at least one of clothing/headgear/shoes is assigned
            has_any = (len(role.clothing_layers) > 0 or
                       role.headgear_layer is not None or
                       role.shoe_layer is not None)
            # Not guaranteed for slavery aesthetic allies, but main species should have gear
            if not role.is_ally:
                test(f"role {i} ({role.role_type.value}) has equipment",
                     has_any)


# ===================================================================
# TextureCache tests
# ===================================================================
print("\n=== TextureCache ===")

cache = TextureCache()
test("cache starts empty", len(cache) == 0)

# Create a test texture via from_bytes
tex_data = bytes([100, 150, 200, 255] * (928 * 256))
test_tex_path = None  # Can't test file loading without real files

# Test cache contains
test("cache doesn't contain missing key",
     ("nonexistent.png", 0.0, 0.0, 0.0) not in cache)

cache.clear()
test("cache clear works", len(cache) == 0)


# ===================================================================
# Enum coverage
# ===================================================================
print("\n=== Enum Coverage ===")

test("Biome has 5 values", len(Biome) == 5)
test("Element has 4 values", len(Element) == 4)
test("Aesthetic has 4 values", len(Aesthetic) == 4)
test("RoleType has 6 values", len(RoleType) == 6)

# All aesthetics have role pools
for aes in Aesthetic:
    pool = _AESTHETIC_ROLE_POOLS[aes]
    test(f"{aes.value} has role pool", len(pool) >= 3,
         f"got {len(pool)}")


# ===================================================================
# Summary
# ===================================================================
print()
if errors:
    print(f"FAILED: {len(errors)} tests failed")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("All tests passed!")
    sys.exit(0)
