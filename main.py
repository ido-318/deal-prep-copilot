from datetime import datetime, timedelta
from pathlib import Path
import re
import json

PROJECT_DIR = Path(__file__).resolve().parent
REFERENCE_NOW = datetime.fromisoformat("2025-03-10T12:00:00+02:00")
RECENT_UPDATE_WINDOW = timedelta(hours=48)
document_path = PROJECT_DIR / "data" / "internal" / "services.md"

content = document_path.read_text(encoding="utf-8")

chunks = []

# החלק שלפני כותרת השירות הראשונה הוא פתיח, ולכן מדלגים עליו
sections = content.split("\n## ")[1:]

for index, section in enumerate(sections, start=1):
    title, _, body = section.partition("\n")

    chunk = {
        "id": f"services-{index}",
        "title": title.strip(),
        "text": body.strip(),
        "source": document_path.name,
    }

    chunks.append(chunk)

def tokenize(text):
    """מחלץ מילים בעברית ובאנגלית, ללא סימני פיסוק."""
    return set(re.findall(r"[א-תa-z0-9]+", text.lower()))


def search_chunks(query, chunks, limit=2):
    query_words = tokenize(query)
    results = []

    for chunk in chunks:
        # המגבלות יחולו תמיד, בנפרד מחיפוש השירות המתאים
        if chunk["title"] == "מגבלות":
            continue

        chunk_words = tokenize(chunk["title"] + " " + chunk["text"])
        matched_words = query_words & chunk_words
        score = len(matched_words)

        if score > 0:
            results.append({
                "chunk": chunk,
                "score": score,
                "matched_words": sorted(matched_words),
            })

    return sorted(
        results,
        key=lambda result: result["score"],
        reverse=True,
    )[:limit]


def filter_recent_updates(updates, now):
    """מחזיר עדכונים מתוארכים בחלון 48 השעות עד now, כולל הגבולות."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now חייב לכלול אזור זמן.")

    window_start = now - RECENT_UPDATE_WINDOW
    recent_updates = []
    for update in updates:
        published_at = update.get("published_at")
        if not isinstance(published_at, str):
            continue

        try:
            published_time = datetime.fromisoformat(published_at)
        except ValueError:
            continue

        if published_time.tzinfo is None or published_time.utcoffset() is None:
            continue
        if window_start <= published_time <= now:
            recent_updates.append(update)

    return recent_updates


def format_datetime(value):
    offset = value.utcoffset()
    if offset is None:
        raise ValueError("התאריך חייב לכלול אזור זמן.")

    total_minutes = int(offset.total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"{value:%d.%m.%Y, %H:%M} (UTC{sign}{hours:02d}:{minutes:02d})"


def build_brief(company, meeting_goal, company_info, results, limitations):
    """בונה תדרוך Markdown על סמך נתוני המאגר ותוצאות החיפוש בלבד."""
    lines = [
        f"# תדרוך לפגישה: {company}",
        "",
        f"**מטרת הפגישה כפי שהוזנה (טרם אומתה):** {meeting_goal}",
        "",
        "> נתוני תרגול מדומים; ללא חיפוש חי ברשת וללא מודל שפה.",
        f"> זמן ייחוס לתרגול: {format_datetime(REFERENCE_NOW)} (לא זמן חדשות חי).",
    ]

    if company_info is None:
        lines.extend(["", "## מידע על החברה", "החברה אינה קיימת במאגר התרגול."])
    else:
        lines.extend(["", "## רקע על החברה"])
        lines.append(company_info["description"])

        updates = filter_recent_updates(company_info.get("updates", []), REFERENCE_NOW)
        if updates:
            lines.extend(["", "## עדכונים"])
            for update in updates:
                lines.extend([
                    f"### {update['title']}",
                    "",
                    update["summary"],
                    "",
                    f"תאריך פרסום: {format_datetime(datetime.fromisoformat(update['published_at']))}",
                    "",
                    f"מקור: {update['source']}",
                ])
        else:
            lines.extend([
                "",
                "## עדכונים",
                "לא נמצאו עדכונים מתאימים בחלון הזמן שנבדק.",
            ])

    lines.extend(["", "## שירותים רלוונטיים"])
    if not results:
        lines.append("לא נמצאו שירותים מתאימים לפי מילות החיפוש.")
    else:
        for result in results:
            chunk = result["chunk"]
            lines.extend([
                f"### {chunk['title']}",
                "",
                chunk["text"],
                "",
                f"מקור: {chunk['source']} | מזהה מקטע: {chunk['id']}",
            ])

    lines.extend(["", "## מגבלות מהמסמך הפנימי"])
    if limitations:
        lines.extend(
            f"- {line}"
            for limitation in limitations
            for line in limitation.splitlines()
            if line.strip()
        )
    else:
        lines.append("לא נמצאו מגבלות במסמך הפנימי.")

    questions_by_service = {
        "אוטומציה של שירות לקוחות": [
            "באילו ערוצים מתקבלות פניות, וכיצד הן מועברות כיום לנציגים?",
            "מהו היקף הפניות ומהם זמני המענה הנוכחיים בשעות שונות?",
            "איזה יעד למיון ולהעברת פניות תרצו לבחון?",
        ],
        "עוזר ידע פנים־ארגוני": [
            "באילו מסמכים או נהלים העובדים מתקשים למצוא מידע?",
            "כיצד העובדים מחפשים מידע כיום, ואילו קשיים הם נתקלים בהם?",
            "האם חשוב שהתשובות יכללו הפניה למסמך המקור?",
        ],
        "הכנה לפגישות מכירה": [
            "איזה מידע פנימי על הלקוח זמין לקראת הפגישה?",
            "אילו נושאים או הזדמנויות תרצו לבדוק בשיחה?",
            "אילו שאלות ומקורות חשוב לכלול בתדרוך?",
        ],
    }

    questions = []
    for result in results:
        title = result["chunk"]["title"]
        service_questions = questions_by_service.get(title)
        if service_questions is None:
            service_questions = [
                "איזה אתגר תרצו לפתור, וכיצד הוא מטופל כיום?",
                "איזו תוצאה תרצו לבחון, ואיזה מידע יעזור להעריך אותה?",
            ]
        for question in service_questions:
            if question not in questions:
                questions.append(question)

    if not questions:
        questions = [
            "איזה אתגר או צורך תרצו לקדם בפגישה?",
            "כיצד הנושא מטופל כיום, ומה תרצו לשפר או לברר?",
            "איזה מידע או דוגמאות יעזרו להבין את המצב?",
        ]

    lines.extend(["", "## שאלות שכדאי לברר בפגישה"])
    lines.extend(f"- {question}" for question in questions)

    return "\n".join(lines)


def save_brief(brief, output_dir):
    """שומר תדרוך UTF-8 בתיקיית היעד ומחזיר את נתיב הקובץ."""
    output_dir.mkdir(parents=True, exist_ok=True)
    brief_path = output_dir / f"brief-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.md"
    brief_path.write_text(brief, encoding="utf-8")
    return brief_path


def main():
    company = input("מה שם החברה שאיתה נפגשים? ").strip()
    query = input("מה מטרת הפגישה? ").strip()

    if not company or not query:
        print("צריך להזין גם שם חברה וגם מטרת פגישה.")
        raise SystemExit(1)

    companies_path = PROJECT_DIR / "data" / "external" / "companies.json"
    companies = json.loads(companies_path.read_text(encoding="utf-8"))
    company_info = companies.get(company)
    results = search_chunks(query, chunks)

    limitations = [
        chunk["text"]
        for chunk in chunks
        if chunk["title"] == "מגבלות"
    ]
    brief = build_brief(company, query, company_info, results, limitations)

    outputs_dir = PROJECT_DIR / "outputs"
    brief_path = save_brief(brief, outputs_dir)
    print(brief)
    print(f"\nהתדרוך נשמר בקובץ: {brief_path.relative_to(PROJECT_DIR)}")


if __name__ == "__main__":
    main()