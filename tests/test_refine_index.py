import unittest

from scripts.refine_index import apply_manual_corrections, merge_additions, refine_rows


class RefineIndexTests(unittest.TestCase):
    def test_refine_rows_removes_mixed_and_merges_hair_style(self):
        rows = [
            {
                "index": "0",
                "tag": "long_hair",
                "db_category_filled": "general",
                "tag_jp": "ロングヘア",
                "category_jp": "髪・目・肌",
            },
            {
                "index": "1",
                "tag": "closed_eyes",
                "db_category_filled": "general",
                "tag_jp": "目を閉じる",
                "category_jp": "髪・目・肌",
            },
            {
                "index": "2",
                "tag": "short_sidetail",
                "db_category_filled": "general",
                "tag_jp": "短いサイドテール",
                "category_jp": "髪型",
            },
        ]

        refined = refine_rows(rows)

        self.assertEqual([row["category_jp"] for row in refined], ["髪", "表情・感情", "髪"])
        self.assertNotIn("髪・目・肌", {row["category_jp"] for row in refined})
        self.assertNotIn("髪型", {row["category_jp"] for row in refined})

    def test_merge_additions_appends_contiguous_indices_and_rejects_duplicates(self):
        existing = [
            {
                "index": "10",
                "tag": "existing",
                "db_category_filled": "general",
                "tag_jp": "既存",
                "category_jp": "一般",
            }
        ]
        additions = [
            {
                "tag": "new_hair",
                "db_category_filled": "general",
                "tag_jp": "新しい髪",
                "category_jp": "髪",
            },
            {
                "tag": "new_eyes",
                "db_category_filled": "general",
                "tag_jp": "新しい目",
                "category_jp": "目",
            },
        ]

        merged = merge_additions(existing, additions)

        self.assertEqual([row["index"] for row in merged], ["10", "11", "12"])
        self.assertEqual([row["tag"] for row in merged[-2:]], ["new_hair", "new_eyes"])

        rerun = merge_additions(merged, additions)
        self.assertEqual(rerun, merged)

        with self.assertRaises(ValueError):
            merge_additions(existing, [dict(additions[0]), dict(additions[0])])

    def test_apply_manual_corrections_checks_old_values_and_updates_the_row(self):
        rows = [
            {
                "index": "3",
                "tag": "tanlines",
                "db_category_filled": "general",
                "tag_jp": "日焼け跡",
                "category_jp": "身体特徴",
            }
        ]
        corrections = [
            {
                "index": "3",
                "tag": "tanlines",
                "old_tag_jp": "日焼け跡",
                "new_tag_jp": "日焼け跡",
                "old_category_jp": "身体特徴",
                "new_category_jp": "肌",
                "reason": "肌に残る日焼けの境界",
            }
        ]

        corrected = apply_manual_corrections(rows, corrections)

        self.assertEqual(corrected[0]["category_jp"], "肌")
        self.assertEqual(corrected[0]["tag_jp"], "日焼け跡")

        with self.assertRaises(ValueError):
            apply_manual_corrections(rows, [dict(corrections[0], old_category_jp="目")])

    def test_apply_manual_corrections_finishes_a_partially_applied_row(self):
        rows = [
            {
                "index": "10",
                "tag": "birthmark",
                "db_category_filled": "general",
                "tag_jp": "あざ",
                "category_jp": "肌",
            }
        ]
        corrections = [
            {
                "index": "10",
                "tag": "birthmark",
                "old_tag_jp": "あざ",
                "new_tag_jp": "生まれつきのあざ",
                "old_category_jp": "身体特徴",
                "new_category_jp": "肌",
                "reason": "出生時からある皮膚の印",
            }
        ]

        result = apply_manual_corrections(rows, corrections)

        self.assertEqual(result[0]["tag_jp"], "生まれつきのあざ")
        self.assertEqual(result[0]["category_jp"], "肌")

        with self.assertRaises(ValueError):
            apply_manual_corrections(rows, [dict(corrections[0]), dict(corrections[0])])


if __name__ == "__main__":
    unittest.main()
