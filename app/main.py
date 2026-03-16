from fastapi import FastAPI
from app.db import get_connection

app = FastAPI()


@app.get("/dictionary")
def lookup(word: str):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Get entry
    query_entry = """
    SELECT id, word, reading
    FROM dictionary_entries
    WHERE word=%s OR reading=%s
    LIMIT 1
    """

    cursor.execute(query_entry, (word, word))
    entry = cursor.fetchone()

    if not entry:
        conn.close()
        return {
            "word": word,
            "meanings_en": [],
            "meanings_vi": []
        }

    entry_id = entry["id"]

    # Get English meanings
    query_en = """
    SELECT meaning
    FROM dictionary_meanings
    WHERE entry_id=%s
    """

    cursor.execute(query_en, (entry_id,))
    meanings_en = [row["meaning"] for row in cursor.fetchall()]

    # Get Vietnamese meanings
    query_vi = """
    SELECT meaning_vi
    FROM dictionary_meanings_vi
    WHERE entry_id=%s
    """

    cursor.execute(query_vi, (entry_id,))
    meanings_vi = [row["meaning_vi"] for row in cursor.fetchall()]

    conn.close()

    return {
        "word": entry["word"],
        "reading": entry["reading"],
        "meanings_en": meanings_en,
        "meanings_vi": meanings_vi
    }