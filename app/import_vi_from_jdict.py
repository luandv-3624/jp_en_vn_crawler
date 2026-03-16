import requests
import time
from db import get_connection

API_URL = "https://api.jdict.net/api/v1/search"

BATCH_SIZE = 100
REQUEST_DELAY = 0.5
MAX_RETRY = 3


def fetch_entries(cursor):
    query = """
    SELECT id, word, reading
    FROM dictionary_entries
    WHERE vi_crawled = FALSE
    ORDER BY id
    LIMIT %s
    """
    cursor.execute(query, (BATCH_SIZE,))
    return cursor.fetchall()


def crawl_meaning(keyword):

    params = {
        "keyword": keyword,
        "type": "word"
    }

    for attempt in range(MAX_RETRY):

        try:

            r = requests.get(API_URL, params=params, timeout=10)

            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")

            data = r.json()

            meanings = []

            if "list" in data:

                for item in data["list"]:

                    if item.get("word") == keyword:

                        suggest = item.get("suggest_mean", "")

                        for m in suggest.split(";"):
                            m = m.strip()
                            if m:
                                meanings.append(m)

                        break

            return meanings

        except Exception as e:

            print(f"Retry {attempt+1}/{MAX_RETRY} for {keyword} : {e}")

            time.sleep(2)

    print(f"FAILED after {MAX_RETRY} retries: {keyword}")

    return []


def main():

    conn = get_connection()
    cursor = conn.cursor()

    total_processed = 0

    while True:

        rows = fetch_entries(cursor)

        if not rows:
            print("DONE: All entries crawled.")
            break

        for entry_id, word, reading in rows:

            keyword = word if word else reading

            try:

                meanings = crawl_meaning(keyword)

                for meaning in meanings:

                    cursor.execute(
                        """
                        INSERT IGNORE INTO dictionary_meanings_vi
                        (entry_id, meaning_vi, source)
                        VALUES (%s,%s,%s)
                        """,
                        (entry_id, meaning, "jdict")
                    )

                cursor.execute(
                    """
                    UPDATE dictionary_entries
                    SET vi_crawled = TRUE
                    WHERE id = %s
                    """,
                    (entry_id,)
                )

                conn.commit()

                total_processed += 1

                print(f"OK {entry_id} | {keyword} | meanings={len(meanings)}")

                time.sleep(REQUEST_DELAY)

            except Exception as e:

                print("ERROR:", keyword, e)

                time.sleep(2)

    print("TOTAL PROCESSED:", total_processed)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
    