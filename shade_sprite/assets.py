"""AssetLibrary - scan and enumerate Puny Characters layer assets by category.

Scans the paid Puny Characters v2.1 "Individual Spritesheets" directory tree
and builds an inventory of available layers organized by category. The
FactionGenerator uses this to know what's actually on disk rather than
hardcoding filenames.

Directory structure (paid pack):
    PUNY CHARACTERS/Individual Spritesheets/
        Layer 0 - Skins/          -> species skins (Human1, Orc1, etc.)
        Layer 1 - Shoes/          -> shoe layers
        Layer 2 - Clothes/        -> clothing by style subfolder
        Layer 3 - Gloves/         -> glove layers
        Layer 4 - Hairstyle/      -> hair by gender + facial hair
        Layer 5 - Eyes/           -> eye color + eyelashes
        Layer 6 - Headgears/      -> helmets/hats by class/culture
        Layer 7 - Add-ons/        -> species-specific add-ons (ears, horns, etc.)
        Tools/                    -> deleter/overlay tools (not used for characters)
"""
import os
import re
from dataclasses import dataclass, field


# Layer directory names inside "Individual Spritesheets"
_LAYER_DIRS = {
    "skins":     "Layer 0 - Skins",
    "shoes":     "Layer 1 - Shoes",
    "clothes":   "Layer 2 - Clothes",
    "gloves":    "Layer 3 - Gloves",
    "hairstyle": "Layer 4 - Hairstyle",
    "eyes":      "Layer 5 - Eyes",
    "headgears": "Layer 6 - Headgears",
    "addons":    "Layer 7 - Add-ons",
}

# Known search paths for the paid pack's Individual Spritesheets directory
_PAID_PACK_SEARCH_PATHS = [
    os.path.expanduser(
        "~/Development/7DRL2026_Liber_Noster_jmccardle/"
        "assets_sources/PUNY_CHARACTERS_v2.1/"
        "PUNY CHARACTERS/Individual Spritesheets"
    ),
    "assets/PUNY_CHARACTERS/Individual Spritesheets",
    "../assets/PUNY_CHARACTERS/Individual Spritesheets",
]


@dataclass
class LayerFile:
    """A single layer PNG file with parsed metadata."""
    path: str           # Full path to the PNG
    filename: str       # Just the filename (e.g. "Human1.png")
    name: str           # Name without extension (e.g. "Human1")
    category: str       # Category key (e.g. "skins", "clothes")
    subcategory: str    # Subfolder within category (e.g. "Armour Body", "")


def _parse_species_from_skin(name):
    """Extract species name from a skin filename like 'Human1' -> 'Human'."""
    match = re.match(r'^([A-Za-z]+?)(\d*)$', name)
    if match:
        return match.group(1)
    return name


class AssetLibrary:
    """Scans and indexes Puny Characters layer assets by category.

    Args:
        base_path: Path to the "Individual Spritesheets" directory.
                   If None, searches known locations automatically.
    """

    def __init__(self, base_path=None):
        if base_path is None:
            base_path = self._find_base_path()
        self.base_path = base_path
        self._layers = {}  # category -> list[LayerFile]
        self._species_cache = None
        if self.base_path:
            self._scan()

    @staticmethod
    def _find_base_path():
        for p in _PAID_PACK_SEARCH_PATHS:
            if os.path.isdir(p):
                return p
        return None

    @property
    def available(self):
        """True if the asset directory was found and scanned."""
        return self.base_path is not None and len(self._layers) > 0

    def _scan(self):
        """Walk the layer directories and build the inventory."""
        for cat_key, dir_name in _LAYER_DIRS.items():
            cat_dir = os.path.join(self.base_path, dir_name)
            if not os.path.isdir(cat_dir):
                continue
            files = []
            for root, _dirs, filenames in os.walk(cat_dir):
                for fn in sorted(filenames):
                    if not fn.lower().endswith(".png"):
                        continue
                    full_path = os.path.join(root, fn)
                    # Subcategory = relative dir from the category root
                    rel = os.path.relpath(root, cat_dir)
                    subcat = "" if rel == "." else rel
                    name = fn[:-4]  # strip .png
                    files.append(LayerFile(
                        path=full_path,
                        filename=fn,
                        name=name,
                        category=cat_key,
                        subcategory=subcat,
                    ))
            self._layers[cat_key] = files

    # ---- Species (Skins) ----

    @property
    def species(self):
        """List of distinct species names derived from Skins/ filenames."""
        if self._species_cache is None:
            seen = {}
            for lf in self._layers.get("skins", []):
                sp = _parse_species_from_skin(lf.name)
                if sp not in seen:
                    seen[sp] = True
            self._species_cache = list(seen.keys())
        return list(self._species_cache)

    def skins_for(self, species):
        """Return LayerFile list for skins matching a species name.

        Args:
            species: Species name (e.g. "Human", "Orc", "Demon")

        Returns:
            list[LayerFile]: Matching skin layers
        """
        return [lf for lf in self._layers.get("skins", [])
                if _parse_species_from_skin(lf.name) == species]

    # ---- Generic category access ----

    def layers(self, category):
        """Return all LayerFiles for a category.

        Args:
            category: One of "skins", "shoes", "clothes", "gloves",
                      "hairstyle", "eyes", "headgears", "addons"

        Returns:
            list[LayerFile]
        """
        return list(self._layers.get(category, []))

    def subcategories(self, category):
        """Return distinct subcategory names within a category.

        Args:
            category: Category key

        Returns:
            list[str]: Sorted subcategory names (empty string for root files)
        """
        subs = set()
        for lf in self._layers.get(category, []):
            subs.add(lf.subcategory)
        return sorted(subs)

    def layers_in(self, category, subcategory):
        """Return LayerFiles within a specific subcategory.

        Args:
            category: Category key
            subcategory: Subcategory name (e.g. "Armour Body")

        Returns:
            list[LayerFile]
        """
        return [lf for lf in self._layers.get(category, [])
                if lf.subcategory == subcategory]

    # ---- Convenience shortcuts ----

    @property
    def clothes(self):
        """All clothing layer files."""
        return self.layers("clothes")

    @property
    def shoes(self):
        """All shoe layer files."""
        return self.layers("shoes")

    @property
    def gloves(self):
        """All glove layer files."""
        return self.layers("gloves")

    @property
    def hairstyles(self):
        """All hairstyle layer files (head hair + facial hair)."""
        return self.layers("hairstyle")

    @property
    def eyes(self):
        """All eye layer files (eye color + eyelashes)."""
        return self.layers("eyes")

    @property
    def headgears(self):
        """All headgear layer files."""
        return self.layers("headgears")

    @property
    def addons(self):
        """All add-on layer files (species-specific ears, horns, etc.)."""
        return self.layers("addons")

    def addons_for(self, species):
        """Return add-ons compatible with a species.

        Matches based on subcategory containing the species name
        (e.g. "Orc Add-ons" for species "Orc").

        Args:
            species: Species name

        Returns:
            list[LayerFile]
        """
        result = []
        for lf in self._layers.get("addons", []):
            # Match "Orc Add-ons" for "Orc", "Elf Add-ons" for "Elf", etc.
            if species.lower() in lf.subcategory.lower():
                result.append(lf)
        return result

    # ---- Headgear by class ----

    def headgears_for_class(self, class_name):
        """Return headgears matching a combat class.

        Args:
            class_name: One of "melee", "range", "mage", "assassin"
                        or a culture like "japanese", "viking", "mongol", "french"

        Returns:
            list[LayerFile]
        """
        # Map common names to subcategory prefixes
        lookup = class_name.lower()
        result = []
        for lf in self._layers.get("headgears", []):
            if lookup in lf.subcategory.lower():
                result.append(lf)
        return result

    # ---- Clothes by style ----

    def clothes_by_style(self, style):
        """Return clothing matching a style keyword.

        Args:
            style: Style keyword (e.g. "armour", "basic", "tunic", "viking")

        Returns:
            list[LayerFile]
        """
        lookup = style.lower()
        return [lf for lf in self._layers.get("clothes", [])
                if lookup in lf.subcategory.lower()]

    # ---- Summary ----

    @property
    def categories(self):
        """List of category keys that have at least one file."""
        return [k for k in _LAYER_DIRS if self._layers.get(k)]

    def summary(self):
        """Return a dict of category -> file count."""
        return {k: len(v) for k, v in self._layers.items() if v}

    def __repr__(self):
        if not self.available:
            return "AssetLibrary(unavailable)"
        total = sum(len(v) for v in self._layers.values())
        cats = len(self.categories)
        return f"AssetLibrary({total} files in {cats} categories)"
