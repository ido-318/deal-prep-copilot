import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).with_name("app.py")


class StreamlitAppTests(unittest.TestCase):
    def create_app(self):
        return AppTest.from_file(str(APP_PATH)).run()

    def test_app_opens_without_errors(self):
        app = self.create_app()

        self.assertFalse(app.exception)
        self.assertIn(
            "עוזר הכנה לפגישות — תרגול",
            [title.value for title in app.title],
        )

    def test_creates_brief_for_example_company(self):
        app = self.create_app()
        app.text_area(key="goal_input").set_value("לקוחות ממתינים זמן רב למענה")
        app.button[0].click().run()

        self.assertFalse(app.exception)
        self.assertIn("brief", app.session_state)
        self.assertEqual(app.session_state["brief_company"], "אופק ציוד משרדי")
        self.assertIn(
            "אוטומציה של שירות לקוחות",
            app.session_state["brief"],
        )
        self.assertTrue(app.get("download_button"))

    def test_rejects_empty_input(self):
        app = self.create_app()
        app.text_area(key="goal_input").set_value("   ")
        app.button[0].click().run()

        self.assertFalse(app.exception)
        self.assertIn("יש להזין שם חברה ומטרת פגישה.", app.error[0].value)
        self.assertNotIn("brief", app.session_state)

    def test_handles_company_missing_from_database(self):
        app = self.create_app()
        app.text_input(key="company_input").set_value("חברה לא מוכרת")
        app.text_area(key="goal_input").set_value("גידול עגבניות")
        app.button[0].click().run()

        self.assertFalse(app.exception)
        self.assertIn(
            "החברה אינה קיימת במאגר התרגול.",
            app.session_state["brief"],
        )
        self.assertIn(
            "לא נמצאו שירותים מתאימים לפי מילות החיפוש.",
            app.session_state["brief"],
        )


if __name__ == "__main__":
    unittest.main()
