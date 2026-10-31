import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import main


PROJECT_DIR = Path(__file__).resolve().parent
COMPANIES_PATH = PROJECT_DIR / "data" / "external" / "companies.json"
COMPANIES = json.loads(COMPANIES_PATH.read_text(encoding="utf-8"))
LIMITATIONS = [
    chunk["text"]
    for chunk in main.chunks
    if chunk["title"] == "מגבלות"
]


class MainTests(unittest.TestCase):
    def test_import_does_not_run_interactive_flow(self):
        outputs_dir = PROJECT_DIR / "outputs"
        files_before = set(outputs_dir.iterdir()) if outputs_dir.exists() else set()
        result = subprocess.run(
            [sys.executable, "-c", "import main"],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        files_after = set(outputs_dir.iterdir()) if outputs_dir.exists() else set()
        self.assertEqual(files_after, files_before)

    def test_search_returns_customer_service_automation_first(self):
        results = main.search_chunks("עומס פניות וזמני תגובה ארוכים", main.chunks)

        self.assertTrue(results)
        self.assertEqual(results[0]["chunk"]["title"], "אוטומציה של שירות לקוחות")

    def test_search_without_matches_returns_empty_list(self):
        self.assertEqual(main.search_chunks("גידול עגבניות", main.chunks), [])

    def test_filter_includes_update_within_window(self):
        now = datetime.fromisoformat("2025-03-10T12:00:00+02:00")
        updates = [{"published_at": "2025-03-09T12:00:00+02:00"}]

        self.assertEqual(main.filter_recent_updates(updates, now), updates)

    def test_filter_includes_exact_48_hour_boundary(self):
        now = datetime.fromisoformat("2025-03-10T12:00:00+02:00")
        updates = [{"published_at": "2025-03-08T12:00:00+02:00"}]

        self.assertEqual(main.filter_recent_updates(updates, now), updates)

    def test_filter_excludes_update_older_than_48_hours(self):
        now = datetime.fromisoformat("2025-03-10T12:00:00+02:00")
        updates = [{"published_at": "2025-03-08T11:59:59+02:00"}]

        self.assertEqual(main.filter_recent_updates(updates, now), [])

    def test_filter_excludes_future_update(self):
        now = datetime.fromisoformat("2025-03-10T12:00:00+02:00")
        updates = [{"published_at": "2025-03-10T12:00:01+02:00"}]

        self.assertEqual(main.filter_recent_updates(updates, now), [])

    def test_filter_excludes_missing_and_invalid_dates(self):
        now = datetime.fromisoformat("2025-03-10T12:00:00+02:00")
        updates = [
            {"title": "missing"},
            {"published_at": "not-a-date"},
            {"published_at": None},
        ]

        self.assertEqual(main.filter_recent_updates(updates, now), [])

    def test_filter_excludes_date_without_timezone(self):
        now = datetime.fromisoformat("2025-03-10T12:00:00+02:00")
        updates = [{"published_at": "2025-03-09T12:00:00"}]

        self.assertEqual(main.filter_recent_updates(updates, now), [])

    def test_filter_compares_same_instant_across_timezones(self):
        now = datetime.fromisoformat("2025-03-10T12:00:00+02:00")
        updates = [
            {"published_at": "2025-03-10T11:00:00+01:00"},
            {"published_at": "2025-03-10T10:00:00+00:00"},
        ]

        self.assertEqual(main.filter_recent_updates(updates, now), updates)

    def test_filter_requires_timezone_aware_now(self):
        updates = [{"published_at": "2025-03-09T12:00:00+02:00"}]

        with self.assertRaises(ValueError):
            main.filter_recent_updates(updates, datetime(2025, 3, 10, 12))

    def test_brief_includes_fiction_label_and_service_source(self):
        company_info = COMPANIES["אופק ציוד משרדי"]
        results = main.search_chunks("עומס פניות וזמני תגובה ארוכים", main.chunks)
        brief = main.build_brief(
            "אופק ציוד משרדי",
            "לקוחות ממתינים זמן רב למענה",
            company_info,
            results,
            LIMITATIONS,
        )

        self.assertIn("נתוני תרגול מדומים", brief)
        self.assertIn("ללא חיפוש חי ברשת וללא מודל שפה", brief)
        self.assertIn("services.md", brief)
        self.assertIn("services-1", brief)
        self.assertIn("זמן ייחוס לתרגול", brief)
        self.assertIn("תאריך פרסום: 2025-03-10T08:00:00+02:00", brief)
        self.assertIn("מקור: נתון מדומה שנכתב לצורך התרגול", brief)
        self.assertNotIn("הרחבת מלאי תרגול ישנה", brief)

    def test_brief_reports_no_recent_updates(self):
        company_info = dict(COMPANIES["אופק ציוד משרדי"])
        company_info["updates"] = [
            {
                "title": "עדכון ישן",
                "summary": "אינו בחלון שנבדק.",
                "source": "תרגול",
                "published_at": "2025-03-08T11:59:59+02:00",
            }
        ]
        brief = main.build_brief("אופק ציוד משרדי", "פגישה", company_info, [], [])

        self.assertIn("לא נמצאו עדכונים מתאימים בחלון הזמן שנבדק.", brief)
        self.assertNotIn("לא התרחשו חדשות בעולם", brief)

    def test_meeting_goal_is_not_presented_as_verified_fact(self):
        brief = main.build_brief(
            "אופק ציוד משרדי",
            "לקוחות ממתינים זמן רב למענה",
            COMPANIES["אופק ציוד משרדי"],
            [],
            LIMITATIONS,
        )

        self.assertIn(
            "**מטרת הפגישה כפי שהוזנה (טרם אומתה):** לקוחות ממתינים זמן רב למענה",
            brief,
        )

    def test_missing_company_and_empty_results_are_explicit(self):
        brief = main.build_brief(
            "חברה לא מוכרת",
            "גידול עגבניות",
            None,
            [],
            LIMITATIONS,
        )

        self.assertIn("החברה אינה קיימת במאגר התרגול.", brief)
        self.assertIn("לא נמצאו שירותים מתאימים לפי מילות החיפוש.", brief)

    def test_limitations_are_included_without_matching_services(self):
        brief = main.build_brief(
            "אופק ציוד משרדי",
            "גידול עגבניות",
            COMPANIES["אופק ציוד משרדי"],
            [],
            LIMITATIONS,
        )

        self.assertIn("- מחיר נקבע לאחר בירור דרישות.", brief)
        self.assertIn(
            "- אין להבטיח חיסכון כספי או שיפור ביצועים ללא מדידה.",
            brief,
        )

    def test_saved_brief_matches_text_and_preserves_hebrew(self):
        brief = main.build_brief(
            "אופק ציוד משרדי",
            "לקוחות ממתינים זמן רב למענה",
            COMPANIES["אופק ציוד משרדי"],
            main.search_chunks("עומס פניות וזמני תגובה ארוכים", main.chunks),
            LIMITATIONS,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = main.save_brief(brief, Path(temp_dir))

            self.assertTrue(path.is_file())
            self.assertEqual(path.read_text(encoding="utf-8"), brief)
            self.assertIn("אופק ציוד משרדי", path.read_text(encoding="utf-8"))
            self.assertNotIn("אופק ציוד משרדי", path.name)


if __name__ == "__main__":
    unittest.main()
