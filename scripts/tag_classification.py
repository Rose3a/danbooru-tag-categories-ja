"""Classify Danbooru tags for prompt-oriented Japanese groups.

The source CSV's ``category_jp`` is a broad, historical label.  This module
keeps the classifier deliberately conservative: a tag is moved to 髪, 目, or
肌 only when its subject is clear.  Expression, accessory, action, effect,
and body-hair tags keep their semantic group instead of being swallowed by a
name-based rule.
"""

from __future__ import annotations

import re
from typing import Final

MIXED_APPEARANCE_CATEGORY: Final = "髪・目・肌"
HAIR_CATEGORY: Final = "髪"
EYE_CATEGORY: Final = "目"
SKIN_CATEGORY: Final = "肌"
EXPRESSION_CATEGORY: Final = "表情・感情"

# These describe eye posture, emotion, or a facial reaction rather than the
# character's stable eye design.  In particular, Danbooru's wink-like tags
# are represented by one_eye_closed; the literal tag "wink" is included here
# for future API updates even when it has no posts.
EXPRESSION_TAGS: Final = frozenset(
    {
        "wink",
        "winking",
        ";d",
        ";)",
        ";o",
        ";p",
        "one_eye_closed",
        "closed_eyes",
        "half-closed_eyes",
        "half-closed_eye",
        "squinting",
        "rolling_eyes",
        "averting_eyes",
        "narrowed_eyes",
        "upturned_eyes",
        "downcast_eyes",
        "downturned_eyes",
        "wide-eyed",
        "unusually_open_eyes",
        "opening_eyes",
        "blinking_inside_eyes",
        "eye_twitch",
        "shady_eyes",
        "evil_eyes",
        "pleading_eyes",
        "crazy_eyes",
        "creepy_eyes",
        "empty_eyes",
        "blank_eyes",
        "jitome",
        "hollow_eyes",
        "sparkling_eyes",
        "v-shaped_eyebrows",
        "raised_eyebrows",
        "raised_eyebrow",
        "cocked_eyebrow",
        "wavy_eyebrows",
        "heart-shaped_eyebrows",
        "eyebrow_twitching",
        "dropping_eyebrows",
    }
)

# Head-hair terms that are not head-hair descriptions.  The exclusions are
# checked before the positive style terms below.
NON_HEAD_HAIR_TERMS: Final = (
    "pubic",
    "facial_hair",
    "body_hair",
    "chest_hair",
    "armpit_hair",
    "leg_hair",
    "arm_hair",
    "ass_hair",
    "stomach_hair",
    "knuckle_hair",
    "nipple_hair",
    "anal_hair",
    "foot_hair",
    "nose_hair",
    "navel_hair",
    "testicle_hair",
    "hair_on_penis",
    "hair_bikini",
    "animal_with_hair",
)

HAIR_ACCESSORY_OR_TOOL_TERMS: Final = (
    "hair_ornament",
    "hair_ribbon",
    "hair_bow",
    "hairband",
    "hairclip",
    "hair_flower",
    "hair_bobbles",
    "hair_scrunchie",
    "hair_rings",
    "hairpin",
    "hair_tie",
    "hair_bell",
    "hair_stick",
    "hair_jewelry",
    "hair_beads",
    "hair_net",
    "hair_spray",
    "hair_brush",
    "hair_dryer",
    "hair_straightener",
    "hair_iron",
    "hair_salon",
    "hair_oil",
    "hair_chart",
    "hair_tattoo",
    "hair_censor",
    "hair_belt",
    "hair_weapon",
    "hair_bondage",
    "no_hair_ornament",
)

HAIR_ACTION_TERMS: Final = (
    "brushing",
    "braiding",
    "grabbing",
    "holding",
    "pulling",
    "cutting",
    "drying",
    "tying",
    "playing",
    "adjusting",
    "smelling",
    "eating",
    "kissing",
    "biting",
    "washing",
    "rubbing",
    "lifting",
    "tucking",
    "ruffling",
    "twirling",
    "untying",
    "stroking",
    "wringing",
    "curling",
    "whipping",
    "licking",
    "strangling",
    "sitting_on",
    "lying_on",
    "wrapped_in",
    "removing",
    "hands_in_",
    "hand_in_",
    "hand_over_",
    "another's",
    "own_hair",
)

HEAD_HAIR_TERMS: Final = (
    "hair",
    "bangs",
    "ponytail",
    "twintail",
    "braid",
    "braids",
    "bun",
    "sidelock",
    "sidelocks",
    "hairstyle",
    "bob",
    "updo",
    "mohawk",
    "afro",
    "dreadlock",
    "mullet",
    "wig",
    "ringlet",
    "ringlets",
    "dreadlocks",
    "twintails",
    "twin_drills",
    "quad_drills",
    "side_drill",
    "cowlick",
    "ahoge",
    "hime_cut",
    "sidecut",
    "wolf_cut",
    "topknot",
    "pompadour",
    "undercut",
    "bald",
    "buzz_cut",
    "crew_cut",
    "pageboy",
    "pixie_cut",
    "fluffy_hair",
)

# Eye tags whose subject is an action, overlay, composition, makeup, effect,
# or a non-facial body feature.  They must not be reclassified as stable eye
# appearance merely because the English name contains "eye".
EYE_EXPRESSION_OR_EFFECT_TERMS: Final = (
    "eye_contact",
    "eye_focus",
    "eyes_out_of_frame",
    "eye_level",
    "eye_to_eye",
    "eye_line",
    "eye_makeup",
    "eyeshadow",
    "eyeliner",
    "eye_black",
    "eye_patch",
    "eye_mask",
    "eye_cover",
    "eye_ornament",
    "eye_tattoo",
    "eye_print",
    "eye_of_",
    "eye_symbol",
    "eyes_of_",
    "eyes_on_",
    "eye_beam",
    "eye_trail",
    "eye_glow",
    "glowing_eye",
    "glowing_eyes",
    "flaming_eye",
    "flaming_eyes",
    "eyes_in_shadow",
    "tears",
    "crying",
    "blush",
    "bruised",
    "scar",
    "blood",
    "bandage",
    "gauze",
    "mask_over",
    "bandages_over",
    "veil_over",
    "hat_over",
    "helmet_over",
    "penis_over",
    "testicles_over",
    "covering_",
    "covered_by",
    "hidden_by",
    "shading_",
    "averting_",
    "gazing_",
    "looking_",
    "rolling_",
    "opening_",
    "closing_",
    "squint",
    "narrowed_",
    "upturned_",
    "downturned_",
    "pleading_",
    "evil_eyes",
    "creepy_eyes",
    "crazy_eyes",
    "mystic_eyes",
    "mature_eyes",
    "empty_eyes",
    "blank_eyes",
    "hollow_eyes",
    "sparkling_eyes",
    "very_big_eyes",
    "eye_pop",
    "eye_socket",
    "finger_to_eye",
    "hand_eye",
    "ok_sign_over_eye",
    "eye_in_",
    "eye_on_",
)

EYE_BODY_FEATURE_TERMS: Final = (
    "too_many_eyes",
    "third_eye",
    "chest_eye",
    "disembodied_",
    "artificial_eye",
    "mechanical_eye",
    "single_mechanical_eye",
    "mechanical_eyes",
    "missing_eye",
    "arm_eye",
    "eye_in_",
    "eye_on_",
)

EYE_DECORATION_TERMS: Final = (
    "flower_over_eye",
    "butterfly_over_eye",
    "w_over_eye",
    "v_over_eye",
    "eye_brooch",
    "eye_piercing",
    "goggles_on_eyes",
    "eyebrow_piercing",
    "eyelash_ornament",
    "jewel_under_eye",
)

SKIN_EXCLUSION_TERMS: Final = (
    "skin_suit",
    "skin-tight",
    "skin_tight",
    "skinny",
    "skin_fang",
    "skin_fangs",
    "skin-covered_horns",
    "skindentation",
    "shirt_tan",
    "accessory_tan",
    "legwear_tan",
    "pasties_tan",
    "self-harm_scar",
)

SKIN_STATE_TERMS: Final = (
    "no_skin",
    "flayed_skin",
    "torn_skin",
    "damaged_skin",
    "decaying_skin",
    "removing_skin",
    "shedding_skin",
)

SKIN_TERMS: Final = (
    "skin",
    "freckle",
    "freckles",
    "suntan",
    "tan",
    "tanlines",
    "mole",
    "moles",
    "skinned",
    "scar",
    "scars",
    "dimples_of_venus",
    "median_furrow",
    "scratches",
    "hickey",
    "stitched_face",
    "stitched_mouth",
    "stitched_arm",
    "stitched_torso",
    "stitched_leg",
    "slap_mark",
    "aegyo_sal",
    "birthmark",
    "red_hands",
    "black_hands",
    "red_nose",
)

SKIN_MARK_TERMS: Final = (
    "mole_under_eye",
    "mole_above_eye",
    "mole_beside_eye",
    "mark_under_eye",
    "mark_under_both_eyes",
    "multiple_moles_under_one_eye",
    "bags_under_eyes",
)

# Explicit resolutions for ambiguous rows that were already present in the
# mixed category.  Keeping this list visible makes future rule changes easy
# to review instead of hiding them in a broad regular expression.
EXPLICIT_CATEGORY_OVERRIDES: Final = {
    "ahoge": HAIR_CATEGORY,
    "ahoge_wag": "ポーズ・動作",
    "two_side_up": HAIR_CATEGORY,
    "one_side_up": HAIR_CATEGORY,
    "blunt_ends": HAIR_CATEGORY,
    "undercut": HAIR_CATEGORY,
    "bald": HAIR_CATEGORY,
    "colored_tips": HAIR_CATEGORY,
    "huge_ahoge": HAIR_CATEGORY,
    "heart_ahoge": HAIR_CATEGORY,
    "extra_eyes": EYE_CATEGORY,
    "no_eyes": EYE_CATEGORY,
    "artificial_eye": EYE_CATEGORY,
    "mechanical_eye": EYE_CATEGORY,
    "disembodied_eye": EYE_CATEGORY,
    "missing_eye": EYE_CATEGORY,
    "dilated_pupils": "状態・状況",
    "drawn_eyes": "効果・演出",
    "cyberpsychosis_eyes": "効果・演出",
    "moon_phases_over_eye": "顔・メイク",
    "topknot": HAIR_CATEGORY,
    "pompadour": HAIR_CATEGORY,
    "buzz_cut": HAIR_CATEGORY,
    "bowl_cut": HAIR_CATEGORY,
    "blunt_tresses": HAIR_CATEGORY,
    "sidecut": HAIR_CATEGORY,
    "wolf_cut": HAIR_CATEGORY,
    "side_ahoge": HAIR_CATEGORY,
    "side_part": HAIR_CATEGORY,
    "widow's_peak": HAIR_CATEGORY,
    "tsurime": EYE_CATEGORY,
    "tareme": EYE_CATEGORY,
    "covered_eyes": "状態・様子",
    "hidden_eyes": "状態・様子",
    "one_eye_covered": "状態・様子",
    "covered_collarbone": "状態・様子",
    "armpit_peek": "状態・様子",
    "sweaty_armpits": "状態・状況",
    "dirty_feet": "状態・状況",
    "stomach_growling": "状態・状況",
    "hairstyle_switch": "状態・状況",
    "gauze_on_cheek": "状態・状況",
    "runny_nose": "状態・状況",
    "single_tear": "状態・状況",
    "flying_teardrops": "状態・状況",
    "head_steam": "効果・演出",
    "fiery_tail": "効果・演出",
    "fiery_wings": "効果・演出",
    "flaming_hand": "効果・演出",
    "drawn_whiskers": "効果・演出",
    "aroused_nosebleed": "状態・状況",
    "spread_wings": "ポーズ・動作",
    "fangs_out": "表情・感情",
    "tail_between_legs": "ポーズ・動作",
    "tail_raised": "ポーズ・動作",
    "tail_around_own_leg": "ポーズ・動作",
    "glowing_hair": "効果・演出",
    "glowing_wings": "効果・演出",
    "glowing_tattoo": "効果・演出",
    "shiny_eyes": "効果・演出",
    "glowing_pupils": "効果・演出",
    "eye_glitter": "効果・演出",
    "melting_eyes": "効果・演出",
    "portal_(object)": "効果・演出",
    "drawn_ears": "効果・演出",
    "brown_feathers": "自然物",
    "glowing_skin": "効果・演出",
    "hair_color_connection": "作品関係",
    "eye_color_connection": "作品関係",
    "skin_color_connection": "作品関係",
    "hairstyle_connection": "作品関係",
    "borrowed_hairstyle": "作品関係",
    "matching_hairstyle": "作品関係",
    "ribbon_in_braid": "アクセサリー",
    "bloodshot_eyes": "状態・状況",
    "lazy_eye": "視線・構図",
    "cross-eyed": "視線・構図",
    "eye_reflection": "効果・演出",
    "hikimayu": EYE_CATEGORY,
    "gazing_eye": "視線・構図",
    "hair_in_own_mouth": "ポーズ・動作",
    "shading_eyes": "効果・演出",
    "eyes_in_shadow": "効果・演出",
    "no_hair_ornament": "アクセサリー",
    "grape_hair_ornament": "アクセサリー",
    "facial_hair": "身体特徴",
    "body_hair": "身体特徴",
    "sparse_chest_hair": "身体特徴",
    "thick_chest_hair": "身体特徴",
    "sideburns": "身体特徴",
    "long_sideburns": "身体特徴",
    "sideburns_stubble": "身体特徴",
    "full_beard": "身体特徴",
    "goatee_stubble": "身体特徴",
    "mustache_stubble": "身体特徴",
    "thick_mustache": "身体特徴",
    "long_beard": "身体特徴",
    "thick_beard": "身体特徴",
    "alternate_facial_hair": "身体特徴",
    "mutton_chops": "身体特徴",
}

# Only these historical groups are candidates for appearance refinement.  In
# particular, identity, work/title, accessory, action, effect, object, food,
# background, state, and sensitive groups must not be moved by a substring
# match such as "iris", "hair", or "tan".
CLASSIFIABLE_SOURCE_CATEGORIES: Final = frozenset(
    {
        "一般",
        "髪",
        "髪型",
        "目",
        "肌",
        "身体特徴",
        "顔・メイク",
        "表情・感情",
        MIXED_APPEARANCE_CATEGORY,
    }
)


_API_TAG_RE = re.compile(r"^[a-z0-9][a-z0-9_:/&!?'().-]*$", re.IGNORECASE)


def is_usable_api_tag(tag: str) -> bool:
    """Return whether a fetched name looks like one canonical tag.

    Danbooru can contain user-created names that are pasted prompt strings.
    The update workflow intentionally rejects whitespace, plus-joined prompts,
    control characters, and unboundedly long names before translation review.
    """

    if not isinstance(tag, str):
        return False
    name = tag.strip()
    return bool(name) and len(name) <= 80 and "+" not in name and bool(_API_TAG_RE.fullmatch(name))


def _has_any(tag: str, terms: tuple[str, ...]) -> bool:
    for term in terms:
        escaped = re.escape(term)
        if term.endswith("_"):
            pattern = rf"(?<![a-z0-9]){escaped}"
        else:
            pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
        if re.search(pattern, tag, re.IGNORECASE):
            return True
    return False


def is_head_hair_tag(tag: str) -> bool:
    """Return whether *tag* describes head hair rather than an action/accessory."""

    name = tag.lower()
    if _has_any(name, NON_HEAD_HAIR_TERMS):
        return False
    if _has_any(name, HAIR_ACCESSORY_OR_TOOL_TERMS):
        return False
    if _has_any(name, HAIR_ACTION_TERMS):
        return False
    return _has_any(name, HEAD_HAIR_TERMS)


def is_skin_tag(tag: str) -> bool:
    """Return whether *tag* describes skin color, texture, freckles, or tan."""

    name = tag.lower()
    if _has_any(name, SKIN_EXCLUSION_TERMS) or name in SKIN_STATE_TERMS:
        return False
    return name in SKIN_MARK_TERMS or _has_any(name, SKIN_TERMS)


def is_eye_appearance_tag(tag: str) -> bool:
    """Return whether *tag* describes stable eye-area appearance."""

    name = tag.lower()
    if name in EXPRESSION_TAGS:
        return False
    if is_head_hair_tag(name) or is_skin_tag(name):
        return False
    if _has_any(name, EYE_EXPRESSION_OR_EFFECT_TERMS):
        return False
    if _has_any(name, EYE_BODY_FEATURE_TERMS):
        return False
    if _has_any(name, EYE_DECORATION_TERMS):
        return False
    return _has_any(
        name,
        (
            "eye",
            "eyes",
            "pupil",
            "pupils",
            "sclera",
            "iris",
            "eyelash",
            "eyelashes",
            "eyebrow",
            "eyebrows",
            "heterochromia",
            "sanpaku",
        ),
    )


def classify_category(tag: str, current_category: str) -> str:
    """Return the refined Japanese category for one tag.

    Existing broad categories are preserved unless the row belongs to a
    known appearance source group and the tag is unambiguously a head-hair,
    eye-appearance, skin, expression, accessory, or effect entry.
    Every remaining row from the old mixed category receives a non-mixed
    fallback (身体特徴), so the old combined label disappears from the main
    index after refinement.
    """

    name = (tag or "").lower()
    current = current_category or ""

    if name in EXPLICIT_CATEGORY_OVERRIDES:
        return EXPLICIT_CATEGORY_OVERRIDES[name]
    if current not in CLASSIFIABLE_SOURCE_CATEGORIES:
        return current
    if name in EXPRESSION_TAGS:
        return EXPRESSION_CATEGORY
    if is_head_hair_tag(name):
        return HAIR_CATEGORY
    if is_skin_tag(name):
        return SKIN_CATEGORY
    if name in {"glowing_eye", "glowing_eyes", "flaming_eye", "flaming_eyes", "eyes_in_shadow"}:
        return "効果・演出" if current == MIXED_APPEARANCE_CATEGORY else current
    if name in EYE_DECORATION_TERMS:
        return "アクセサリー" if current == MIXED_APPEARANCE_CATEGORY else current
    if is_eye_appearance_tag(name):
        return EYE_CATEGORY
    if current == "髪型":
        return HAIR_CATEGORY
    if current == MIXED_APPEARANCE_CATEGORY:
        return "身体特徴"
    return current
