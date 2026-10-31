"""
TP01 - Python Web Scraping Case Study
Module : Big Data Analytics (Master 2 - AI & Data Science)

Main source     : Google Books API  https://www.googleapis.com/books/v1/volumes
                  (free, open, no account needed, answers in JSON)
Fallback source : Open Library API  https://openlibrary.org/search.json
                  (used automatically if the main source cannot be reached)

Install once :  pip install requests beautifulsoup4 pandas
Run          :  python tp01_book_scraper.py

Program plan
------------
SECTION 1 : Configuration
SECTION 2 : Network check (is the source reachable? which one do we use?)
SECTION 3 : Downloading a web page / API answer          (Question 1)
SECTION 4 : Cleaning text with BeautifulSoup             (Question 2)
SECTION 5 : Main source - Google Books                   (Questions 1 and 2)
SECTION 6 : Fallback source - Open Library               (Questions 1 and 2)
SECTION 7 : Saving to CSV with pandas                    (Question 3)
SECTION 8 : Checking the 1000 rows rule                  (Question 4)
SECTION 9 : Main program
"""

import json
import socket
import sys
import time
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

# The Windows console often cannot print accented letters -> avoid crashes.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# =====================================================================
# SECTION 1 : CONFIGURATION
# Every setting lives here, so you can change behaviour in one place.
# =====================================================================
# "auto" = try Google Books, switch to Open Library if it is unreachable.
# You can force one source: "google_books" or "open_library".
SOURCE = "auto"

GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"
GOOGLE_API_KEY = ""          # optional: a free key avoids rate limits (leave "" to skip)
OPEN_LIBRARY_URL = "https://openlibrary.org/search.json"

# Educational subjects to collect (the more subjects, the more books)
SUBJECTS = [
    "computer science", "artificial intelligence", "data science", "mathematics",
    "statistics", "physics", "chemistry", "biology", "engineering", "economics",
    "philosophy", "history", "psychology", "medicine" , "geology",
]
PAGES_PER_SUBJECT = 5        # Google Books: 5 pages x 40 books = 200 books per subject
TARGET_ROWS = 1200           # stop when we have this many (safety margin over 1000)
MAX_FAILED_SUBJECTS = 3      # give up on a source after this many subjects fail in a row

OUTPUT_CSV = "books_dataset.csv"
MIN_ROWS = 1000
HEADERS = {"User-Agent": "Mozilla/5.0 (Student TP01 scraper - educational use)"}
TIMEOUT_SECONDS = 20
RETRIES = 3                  # how many times we try one URL before giving up
DELAY_SECONDS = 0.5          # pause between requests (be polite to the server)
PRINT_PREVIEW = True         # Question 1: show the source code on screen
PREVIEW_CHARS = 600          # characters printed per answer (None = print EVERYTHING)

# Language codes -> readable names (unknown codes are kept as they are)
LANGUAGE_NAMES = {
    "en": "English", "fr": "French", "de": "German", "es": "Spanish",
    "ar": "Arabic", "ru": "Russian", "it": "Italian", "pt": "Portuguese",
    "zh": "Chinese", "ja": "Japanese", "nl": "Dutch", "la": "Latin",
    "eng": "English", "fre": "French", "ger": "German", "spa": "Spanish",
    "ara": "Arabic", "rus": "Russian", "ita": "Italian", "por": "Portuguese",
    "chi": "Chinese", "jpn": "Japanese", "dut": "Dutch", "lat": "Latin",
}


# =====================================================================
# SECTION 2 : NETWORK CHECK
# "getaddrinfo failed" means the DNS lookup of a site name failed.
# We test that BEFORE downloading anything.
# =====================================================================
def host_is_reachable(url):
    """
    Stage 2.1 : extract the host name from the URL
    Stage 2.2 : ask DNS for its IP address (same call that fails inside requests)
    Stage 2.3 : return True if it resolves, False (with an explanation) otherwise
    """
    parsed = urlparse(url)                                           # 2.1
    host = parsed.hostname
    port = parsed.port or 443
    try:
        ip = socket.getaddrinfo(host, port)[0][4][0]                 # 2.2
    except socket.gaierror as error:
        print(f"[!] DNS lookup failed for '{host}': {error}")        # 2.3
        return False
    print(f"[OK] '{host}' resolves to {ip}")
    return True


def choose_source():
    """
    Stage 2.4 : respect the manual choice if SOURCE is not "auto"
    Stage 2.5 : otherwise test Google Books, then Open Library
    Stage 2.6 : return the name of the source to use, or None if nothing works
    """
    if SOURCE != "auto":                                             # 2.4
        return SOURCE

    if host_is_reachable(GOOGLE_BOOKS_URL):                          # 2.5
        return "google_books"
    print("-> Google Books unreachable, trying the fallback source.")
    if host_is_reachable(OPEN_LIBRARY_URL):
        return "open_library"
    return None                                                      # 2.6


# =====================================================================
# SECTION 3 : DOWNLOADING A WEB PAGE / API ANSWER   (Question 1)
# One small function that every other section reuses.
# =====================================================================
def fetch_page(url, params=None):
    """
    Stage 3.1 : send an HTTP GET request (with User-Agent and timeout)
    Stage 3.2 : if the server says "too many requests" (429) or has an
                error (5xx), wait a bit and try again
    Stage 3.3 : return None for any other problem (e.g. 404)
    Stage 3.4 : retry a few times if the network itself fails
    Stage 3.5 : wait a little after each request to be polite
    """
    for attempt in range(1, RETRIES + 1):                            # 3.4
        try:
            response = requests.get(url, params=params, headers=HEADERS,
                                    timeout=TIMEOUT_SECONDS)         # 3.1
        except requests.RequestException as error:
            print(f"[!] Network error (try {attempt}/{RETRIES}): {error}")
            time.sleep(1)
            continue

        if response.status_code == 429 or response.status_code >= 500:   # 3.2
            print(f"[!] Server busy (HTTP {response.status_code}), waiting...")
            time.sleep(2 * attempt)
            continue
        if response.status_code != 200:                              # 3.3
            print(f"[!] HTTP {response.status_code} for {response.url}")
            return None

        response.encoding = "utf-8"
        time.sleep(DELAY_SECONDS)                                    # 3.5
        return response.text
    return None


def show_source(label, text):
    """Stage 3.6 : display the source code (JSON) on screen (Question 1)."""
    print(f"\n===== SOURCE CODE of {label} ({len(text)} chars) =====")
    if PRINT_PREVIEW:
        print(text if PREVIEW_CHARS is None else text[:PREVIEW_CHARS] + "\n...")


# =====================================================================
# SECTION 4 : CLEANING TEXT WITH BEAUTIFULSOUP   (Question 2)
# Some descriptions contain HTML tags such as <b> or <br>.
# =====================================================================
def value_or_na(value):
    """Stage 4.1 : return the value, or "N/A" when it is missing / empty."""
    return value if value not in (None, "", []) else "N/A"


def clean_html(text):
    """
    Stage 4.2 : parse the text as HTML with BeautifulSoup
    Stage 4.3 : keep only the readable text (tags removed)
    Stage 4.4 : return "N/A" if nothing is left
    """
    if not text:
        return "N/A"
    soup = BeautifulSoup(text, "html.parser")                        # 4.2
    plain = soup.get_text(" ", strip=True)                           # 4.3
    return plain if plain else "N/A"                                 # 4.4


def language_name(codes):
    """Stage 4.5 : 'en' -> 'English' (a list of codes becomes 'English, French')."""
    if isinstance(codes, str):
        codes = [codes]
    names = [LANGUAGE_NAMES.get(code, code) for code in (codes or [])[:3]]
    return value_or_na(", ".join(names))


# =====================================================================
# SECTION 5 : MAIN SOURCE - GOOGLE BOOKS   (Questions 1 and 2)
# =====================================================================
def build_google_record(item, subject):
    """
    Stage 5.1 : read the two blocks of one result: volumeInfo and saleInfo
    Stage 5.2 : pick the fields we need, "N/A" when the API does not give them
    Stage 5.3 : return ONE dictionary (= one CSV row)
    """
    info = item.get("volumeInfo") or {}                              # 5.1
    sale = item.get("saleInfo") or {}
    price = sale.get("listPrice") or {}

    return {                                                         # 5.2 / 5.3
        "book_id": item["id"],
        "book_name": info["title"],
        "author": value_or_na(", ".join((info.get("authors") or [])[:3])),
        "release_date": value_or_na(info.get("publishedDate")),
        "number_of_pages": value_or_na(info.get("pageCount") or None),
        "main_language": language_name(info.get("language")),
        "price": value_or_na(price.get("amount")),
        "price_currency": value_or_na(price.get("currencyCode")),
        "domain_tag": value_or_na(", ".join(info.get("categories") or [])),
        "search_subject": subject,
        "publisher": value_or_na(info.get("publisher")),
        "rating_out_of_5": value_or_na(info.get("averageRating")),
        "number_of_ratings": value_or_na(info.get("ratingsCount")),
        "description": clean_html(info.get("description")),
        "book_url": value_or_na(info.get("infoLink")),
        "source": "Google Books",
    }


def crawl_google_books():
    """
    Stage 5.4 : for each subject, request result pages 1, 2, 3 ... (40 books per page)
    Stage 5.5 : display the source code (JSON) of each page on screen
    Stage 5.6 : convert every result to a record, skipping duplicates
    Stage 5.7 : stop as soon as we have enough rows
    Stage 5.8 : stop early if the source keeps refusing our requests
    """
    records, seen, failed = [], set(), 0
    for subject in SUBJECTS:
        if failed >= MAX_FAILED_SUBJECTS:                            # 5.8
            print("[!] Too many failures in a row -> giving up on this source.")
            break
        for page in range(PAGES_PER_SUBJECT):                        # 5.4
            params = {
                "q": f'subject:"{subject}"',
                "printType": "books",
                "maxResults": 40,
                "startIndex": page * 40,
            }
            if GOOGLE_API_KEY:
                params["key"] = GOOGLE_API_KEY
            text = fetch_page(GOOGLE_BOOKS_URL, params=params)
            if text is None:
                print(f"[!] No answer for '{subject}' page {page + 1} -> next subject.")
                failed += 1
                break
            show_source(f"Google Books '{subject}' page {page + 1}", text)   # 5.5

            try:
                items = json.loads(text).get("items") or []
            except ValueError:
                print("[!] Answer is not valid JSON -> next subject.")
                break
            if not items:
                break                                                # no more results

            for item in items:                                       # 5.6
                title = (item.get("volumeInfo") or {}).get("title")
                if not item.get("id") or not title or item["id"] in seen:
                    continue
                seen.add(item["id"])
                records.append(build_google_record(item, subject))

            print(f"  ... {len(records)} unique books collected")
            if len(records) >= TARGET_ROWS:                          # 5.7
                return records
    return records


# =====================================================================
# SECTION 6 : FALLBACK SOURCE - OPEN LIBRARY   (Questions 1 and 2)
# Free and open. It gives no prices -> price stays "N/A".
# =====================================================================
def build_open_library_record(doc, subject):
    """
    Stage 6.1 : pick the fields we need from one JSON result ("doc")
    Stage 6.2 : return ONE dictionary (= one CSV row); missing data = "N/A"
    """
    authors = ", ".join((doc.get("author_name") or [])[:3])          # 6.1
    rating = doc.get("ratings_average")
    return {                                                         # 6.2
        "book_id": doc["key"],                       # e.g. "/works/OL45804W"
        "book_name": doc["title"],
        "author": value_or_na(authors),
        "release_date": value_or_na(doc.get("first_publish_year")),
        "number_of_pages": value_or_na(doc.get("number_of_pages_median")),
        "main_language": language_name(doc.get("language")),  # languages of the editions
        "price": "N/A",
        "price_currency": "N/A",
        "domain_tag": subject,
        "search_subject": subject,
        "publisher": "N/A",
        "rating_out_of_5": round(rating, 2) if rating else "N/A",
        "number_of_ratings": "N/A",
        "description": "N/A",
        "book_url": "https://openlibrary.org" + doc["key"],
        "source": "Open Library",
    }


def crawl_open_library():
    """
    Stage 6.3 : for each subject, request result pages 1, 2, 3 ... (100 books per page)
    Stage 6.4 : display the source code (JSON) of each page on screen
    Stage 6.5 : convert every result to a record, skipping duplicates
    Stage 6.6 : stop as soon as we have enough rows
    Stage 6.7 : stop early if the source keeps refusing our requests
    """
    records, seen, failed = [], set(), 0
    for subject in SUBJECTS:
        if failed >= MAX_FAILED_SUBJECTS:                            # 6.7
            print("[!] Too many failures in a row -> giving up on this source.")
            break
        for page in range(1, PAGES_PER_SUBJECT + 1):                 # 6.3
            params = {
                "q": f'subject:"{subject}"',
                "fields": "key,title,author_name,first_publish_year,"
                          "number_of_pages_median,language,ratings_average",
                "limit": 100,
                "page": page,
            }
            text = fetch_page(OPEN_LIBRARY_URL, params=params)
            if text is None:
                print(f"[!] No answer for '{subject}' page {page} -> next subject.")
                failed += 1
                break
            show_source(f"Open Library '{subject}' page {page}", text)   # 6.4

            try:
                docs = json.loads(text).get("docs") or []
            except ValueError:
                print("[!] Answer is not valid JSON -> next subject.")
                break
            if not docs:
                break

            for doc in docs:                                         # 6.5
                if not doc.get("key") or not doc.get("title") or doc["key"] in seen:
                    continue
                seen.add(doc["key"])
                records.append(build_open_library_record(doc, subject))

            print(f"  ... {len(records)} unique books collected")
            if len(records) >= TARGET_ROWS:                          # 6.6
                return records
    return records


# =====================================================================
# SECTION 7 : SAVING TO CSV WITH PANDAS   (Question 3)
# =====================================================================
def save_to_csv(books, filename):
    """
    Stage 7.1 : refuse to continue if there is nothing to save
    Stage 7.2 : convert the list of dictionaries into a DataFrame
    Stage 7.3 : remove duplicates (same book_id = same book)
    Stage 7.4 : write the CSV (utf-8-sig so Excel reads it correctly)
    """
    if not books:                                                    # 7.1
        return None
    df = pd.DataFrame(books)                                         # 7.2
    df = df.drop_duplicates(subset="book_id")                        # 7.3
    df.to_csv(filename, index=False, encoding="utf-8-sig")           # 7.4
    return df


# =====================================================================
# SECTION 8 : CHECKING THE "AT LEAST 1000 ROWS" RULE   (Question 4)
# =====================================================================
def check_row_count(df, minimum=MIN_ROWS):
    """
    Stage 8.1 : count the rows
    Stage 8.2 : print a success or a warning message
    """
    rows = len(df)                                                   # 8.1
    if rows >= minimum:                                              # 8.2
        print(f"\n[OK] The file contains {rows} rows (>= {minimum}).")
        return True
    print(f"\n[WARNING] Only {rows} rows, the requirement is {minimum}.")
    return False


# =====================================================================
# SECTION 9 : MAIN PROGRAM
# =====================================================================
def main():
    # Step A - which source can we reach?
    source = choose_source()
    if source is None:
        print("\n[X] Neither Google Books nor Open Library can be resolved.")
        print("    Fix your DNS / VPN / proxy (or try another network, e.g. a phone hotspot),")
        print("    then run the script again. Nothing was saved.")
        return
    print(f"\nSource selected: {source}")

    # Step B - Questions 1 and 2 : download, display and extract
    books = crawl_google_books() if source == "google_books" else crawl_open_library()

    # Step B2 - in "auto" mode, if Google gave too few rows, give Open Library a chance
    #           and keep whichever result is bigger
    if SOURCE == "auto" and source == "google_books" and len(books) < MIN_ROWS:
        print(f"\n-> Only {len(books)} rows from Google Books, trying Open Library too.")
        if host_is_reachable(OPEN_LIBRARY_URL):
            other = crawl_open_library()
            if len(other) > len(books):
                books = other

    # Step C - Question 3 : save to CSV
    df = save_to_csv(books, OUTPUT_CSV)
    if df is None:
        print("\n[X] No book could be downloaded, so no CSV was written.")
        print("    If the source answered with errors (HTTP 403/429), wait a few minutes,")
        print("    or set SOURCE = \"open_library\" in SECTION 1.")
        return
    print(f"\nSaved to '{OUTPUT_CSV}'. Preview:")
    print(df[["book_name", "author", "release_date", "number_of_pages",
              "domain_tag"]].head(10).to_string())

    # Step D - Question 4 : verify the 1000 rows requirement
    check_row_count(df)


if __name__ == "__main__":
    main()