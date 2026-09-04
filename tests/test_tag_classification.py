import csv
import unittest
from pathlib import Path

from scripts.tag_classification import classify_category, is_usable_api_tag


class TagClassificationTests(unittest.TestCase):
    def test_head_hair_is_separated_from_eyes_and_skin(self):
        self.assertEqual(classify_category("long_hair", "髪・目・肌"), "髪")
        self.assertEqual(classify_category("hair_between_eyes", "髪・目・肌"), "髪")
        self.assertEqual(classify_category("long_braid", "髪・目・肌"), "髪")

    def test_eye_appearance_is_separated(self):
        self.assertEqual(classify_category("blue_eyes", "髪・目・肌"), "目")
        self.assertEqual(classify_category("star-shaped_pupils", "髪・目・肌"), "目")
        self.assertEqual(classify_category("extra_eyes", "身体特徴"), "目")
        self.assertEqual(classify_category("no_eyes", "身体特徴"), "目")
        self.assertEqual(classify_category("artificial_eye", "身体特徴"), "目")
        self.assertEqual(classify_category("mechanical_eye", "身体特徴"), "目")
        self.assertEqual(classify_category("disembodied_eye", "身体特徴"), "目")
        self.assertEqual(classify_category("missing_eye", "身体特徴"), "目")
        self.assertEqual(classify_category("dilated_pupils", "目"), "状態・状況")
        self.assertEqual(classify_category("drawn_eyes", "目"), "効果・演出")
        self.assertEqual(classify_category("cyberpsychosis_eyes", "目"), "効果・演出")
        self.assertEqual(classify_category("moon_phases_over_eye", "目"), "顔・メイク")
        self.assertEqual(classify_category("tsurime", "表情・感情"), "目")
        self.assertEqual(classify_category("tareme", "表情・感情"), "目")

    def test_wink_and_eye_posture_stay_expression(self):
        self.assertEqual(classify_category("wink", "一般"), "表情・感情")
        self.assertEqual(classify_category("one_eye_closed", "表情・感情"), "表情・感情")
        self.assertEqual(classify_category("closed_eyes", "髪・目・肌"), "表情・感情")
        self.assertEqual(classify_category("narrowed_eyes", "表情・感情"), "表情・感情")

    def test_accessory_action_and_effect_do_not_become_hair_or_eye(self):
        self.assertEqual(classify_category("hair_ornament", "アクセサリー"), "アクセサリー")
        self.assertEqual(classify_category("brushing_hair", "ポーズ・動作"), "ポーズ・動作")
        self.assertEqual(classify_category("glowing_eyes", "効果・演出"), "効果・演出")
        self.assertEqual(classify_category("eyes_in_shadow", "髪・目・肌"), "効果・演出")

    def test_skin_is_separated_but_body_and_sensitive_hair_are_preserved(self):
        self.assertEqual(classify_category("dark_skin", "髪・目・肌"), "肌")
        self.assertEqual(classify_category("pale_skin", "身体特徴"), "肌")
        self.assertEqual(classify_category("tanlines", "身体特徴"), "肌")
        self.assertEqual(classify_category("multiple_moles_under_one_eye", "肌"), "肌")
        self.assertEqual(classify_category("scar", "身体特徴"), "肌")
        self.assertEqual(classify_category("scar_on_face", "身体特徴"), "肌")
        self.assertEqual(classify_category("burn_scar", "身体特徴"), "肌")
        self.assertEqual(classify_category("dimples_of_venus", "身体特徴"), "肌")
        self.assertEqual(classify_category("median_furrow", "身体特徴"), "肌")
        self.assertEqual(classify_category("scratches", "身体特徴"), "肌")
        self.assertEqual(classify_category("hickey", "身体特徴"), "肌")
        self.assertEqual(classify_category("stitched_face", "身体特徴"), "肌")
        self.assertEqual(classify_category("stitched_arm", "身体特徴"), "肌")
        self.assertEqual(classify_category("stitched_leg", "身体特徴"), "肌")
        self.assertEqual(classify_category("slap_mark", "身体特徴"), "肌")
        self.assertEqual(classify_category("aegyo_sal", "身体特徴"), "肌")
        self.assertEqual(classify_category("birthmark", "身体特徴"), "肌")
        self.assertEqual(classify_category("red_hands", "身体特徴"), "肌")
        self.assertEqual(classify_category("red_nose", "身体特徴"), "肌")
        self.assertEqual(classify_category("black_hands", "身体特徴"), "肌")
        self.assertEqual(classify_category("stitched_torso", "身体特徴"), "肌")
        self.assertEqual(classify_category("facial_hair", "髪・目・肌"), "身体特徴")
        self.assertEqual(classify_category("mutton_chops", "顔・メイク"), "身体特徴")
        self.assertEqual(classify_category("pubic_hair", "成人向け/センシティブ"), "成人向け/センシティブ")
        self.assertEqual(classify_category("self-harm_scar", "成人向け/センシティブ"), "成人向け/センシティブ")

    def test_identity_accessory_object_and_sensitive_categories_are_not_reclassified(self):
        self.assertEqual(classify_category("iris_(pokemon)", "キャラクター"), "キャラクター")
        self.assertEqual(classify_category("os-tan", "作品・シリーズ"), "作品・シリーズ")
        self.assertEqual(classify_category("eyebrow_piercing", "アクセサリー"), "アクセサリー")
        self.assertEqual(classify_category("grape_hair_ornament", "成人向け/センシティブ"), "アクセサリー")
        self.assertEqual(classify_category("drill", "小物・道具"), "小物・道具")
        self.assertEqual(classify_category("japari_bun", "飲食物"), "飲食物")
        self.assertEqual(classify_category("blood_in_hair", "状態・質感"), "状態・質感")
        self.assertEqual(classify_category("cum_on_hair", "成人向け/センシティブ"), "成人向け/センシティブ")

    def test_plural_hair_styles_are_still_detected(self):
        self.assertEqual(classify_category("dreadlocks", "髪・目・肌"), "髪")
        self.assertEqual(classify_category("low_twintails", "髪・目・肌"), "髪")
        self.assertEqual(classify_category("twin_drills", "髪・目・肌"), "髪")
        self.assertEqual(classify_category("side_drill", "髪・目・肌"), "髪")

    def test_transient_eye_visibility_and_hair_interactions_leave_stable_groups(self):
        for tag in ("covered_eyes", "hidden_eyes", "one_eye_covered"):
            self.assertEqual(classify_category(tag, "髪・目・肌"), "状態・様子")
        self.assertEqual(classify_category("covered_collarbone", "身体特徴"), "状態・様子")
        self.assertEqual(classify_category("armpit_peek", "身体特徴"), "状態・様子")
        self.assertEqual(classify_category("sweaty_armpits", "身体特徴"), "状態・状況")
        self.assertEqual(classify_category("dirty_feet", "身体特徴"), "状態・状況")
        self.assertEqual(classify_category("stomach_growling", "身体特徴"), "状態・状況")
        self.assertEqual(classify_category("hairstyle_switch", "髪"), "状態・状況")
        self.assertEqual(classify_category("gauze_on_cheek", "アクセサリー"), "状態・状況")
        self.assertEqual(classify_category("runny_nose", "表情・感情"), "状態・状況")
        self.assertEqual(classify_category("single_tear", "表情・感情"), "状態・状況")
        self.assertEqual(classify_category("flying_teardrops", "表情・感情"), "状態・状況")
        self.assertEqual(classify_category("head_steam", "表情・感情"), "効果・演出")
        self.assertEqual(classify_category("fiery_tail", "身体特徴"), "効果・演出")
        self.assertEqual(classify_category("fiery_wings", "身体特徴"), "効果・演出")
        self.assertEqual(classify_category("flaming_hand", "身体特徴"), "効果・演出")
        self.assertEqual(classify_category("drawn_whiskers", "顔・表情"), "効果・演出")
        self.assertEqual(classify_category("aroused_nosebleed", "表情・感情"), "状態・状況")
        self.assertEqual(classify_category("spread_wings", "身体特徴"), "ポーズ・動作")
        self.assertEqual(classify_category("fangs_out", "身体特徴"), "表情・感情")
        self.assertEqual(classify_category("tail_between_legs", "身体特徴"), "ポーズ・動作")
        self.assertEqual(classify_category("tail_raised", "身体特徴"), "ポーズ・動作")
        self.assertEqual(classify_category("tail_around_own_leg", "身体特徴"), "ポーズ・動作")
        self.assertEqual(classify_category("stitched_mouth", "身体特徴"), "肌")
        self.assertEqual(classify_category("glowing_hair", "髪"), "効果・演出")
        self.assertEqual(classify_category("glowing_wings", "身体特徴"), "効果・演出")
        self.assertEqual(classify_category("glowing_tattoo", "身体特徴"), "効果・演出")
        self.assertEqual(classify_category("shiny_eyes", "目"), "効果・演出")
        self.assertEqual(classify_category("glowing_pupils", "目"), "効果・演出")
        self.assertEqual(classify_category("eye_glitter", "目"), "効果・演出")
        self.assertEqual(classify_category("melting_eyes", "目"), "効果・演出")
        self.assertEqual(classify_category("portal_(object)", "小物・道具"), "効果・演出")
        self.assertEqual(classify_category("drawn_ears", "身体特徴"), "効果・演出")
        self.assertEqual(classify_category("brown_feathers", "身体特徴"), "自然物")
        self.assertEqual(classify_category("glowing_skin", "肌"), "効果・演出")
        self.assertEqual(classify_category("hair_color_connection", "髪"), "作品関係")
        self.assertEqual(classify_category("eye_color_connection", "目"), "作品関係")
        self.assertEqual(classify_category("skin_color_connection", "肌"), "作品関係")
        self.assertEqual(classify_category("hairstyle_connection", "髪"), "作品関係")
        self.assertEqual(classify_category("borrowed_hairstyle", "髪"), "作品関係")
        self.assertEqual(classify_category("matching_hairstyle", "髪"), "作品関係")
        self.assertEqual(classify_category("ribbon_in_braid", "髪"), "アクセサリー")
        self.assertEqual(classify_category("bloodshot_eyes", "目"), "状態・状況")
        self.assertEqual(classify_category("lazy_eye", "目"), "視線・構図")
        self.assertEqual(classify_category("cross-eyed", "目"), "視線・構図")
        self.assertEqual(classify_category("eye_reflection", "目"), "効果・演出")
        self.assertEqual(classify_category("gazing_eye", "髪・目・肌"), "視線・構図")
        self.assertEqual(classify_category("hair_in_own_mouth", "髪・目・肌"), "ポーズ・動作")
        self.assertEqual(classify_category("ahoge_wag", "髪・目・肌"), "ポーズ・動作")

    def test_api_candidate_filter_rejects_pasted_prompt_strings(self):
        self.assertTrue(is_usable_api_tag("central_heterochromia"))
        self.assertTrue(is_usable_api_tag("heart-shaped_hair"))
        self.assertFalse(is_usable_api_tag("1girl+blue_eyes+twintails"))
        self.assertFalse(is_usable_api_tag("hair with spaces"))

    def test_existing_csv_has_expected_schema_before_refinement(self):
        csv_path = Path(__file__).parents[1] / "index.csv"
        with csv_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(
                reader.fieldnames,
                ["index", "tag", "db_category_filled", "tag_jp", "category_jp"],
            )
            self.assertGreater(sum(1 for _ in reader), 19000)


if __name__ == "__main__":
    unittest.main()
