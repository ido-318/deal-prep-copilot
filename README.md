# עוזר הכנה לפגישות — תרגול

פרויקט לימודי שמפיק תדרוך בעברית מתוך נתוני חברה ושירותים לדוגמה. נתוני
החברות והעדכונים מדומים, זמן הייחוס קבוע, ואין חיפוש חי ברשת או שימוש במודל
שפה. חיפוש השירותים מתבצע לפי התאמת מילים למסמך הפנימי.

## התקנה

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Streamlit תומך ב־Python 3.14; סביבת הפרויקט נבדקה עם Python 3.14.7.

## הרצת CLI

```bash
.venv/bin/python main.py
```

## הרצת ממשק Streamlit

```bash
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1
```

## הרצת בדיקות

```bash
.venv/bin/python -m unittest -v
```

הממשק יוצר ומציג תדרוך, שומר אותו במצב הממשק ומאפשר להוריד אותו כ־Markdown.
לא מתבצעת שמירה אוטומטית לדיסק. אין חיבור ל־API או פרסום ברשת.
