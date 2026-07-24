import sys
import os
import subprocess
from playwright.sync_api import sync_playwright
import urllib.parse
from geopy.geocoders import Nominatim
#from geopy.distance import geodesic
from nltk.corpus import stopwords
import re
import math
import pandas as pd
from collections import Counter

def getCity(location):

    linkArray = {
        "Atlanta, Georgia": "90000052",
        "New York, New York": "102571732",
        "Chicago, Illinois": "103112676",
        "Dallas, Texas": "104194190"
    }


    cityCoordsMap = {
        "Atlanta, Georgia": (33.7489, -84.3903),
        "New York, New York": (40.7128, -74.0060),
        "Chicago, Illinois": (41.8781, -87.6298),
        "Dallas, Texas": (32.7767, -96.7970)
    }

    geolocator = Nominatim(user_agent="cityMatch")
    locationInput = geolocator.geocode(location)

    if not locationInput:
        return None

    user_coords = (locationInput.latitude, locationInput.longitude)

    closest = None
    minDist = float("inf")

    for cityName, coords in cityCoordsMap.items():
        dist = geodesic(user_coords, coords).miles

        if dist < minDist:
            minDist = dist
            closest = cityName

    return closest, linkArray[closest], minDist
            
            
def getData(path, username, password, titles, geoId):
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(path, wait_until="domcontentloaded")
        page.locator("#username").fill(username)
        page.locator("#password").fill(password)
        page.locator('button[type="submit"]').click()

        page.wait_for_url("**linkedin.com/feed/**")

        for title in titles:
            print(f"\nSearching for: {title}")

            query = urllib.parse.quote(title)
            jobs_url = f"https://www.linkedin.com/jobs/search/?geoId={geoId}&keywords={query}&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true"

            page.goto(jobs_url, wait_until="domcontentloaded")
            page.wait_for_selector('a[href*="/jobs/view/"]', timeout=15000)

            count = page.locator('a[href*="/jobs/view/"]').count()
            print("Jobs found:", count)

            for i in range(min(10, count)):
                job_links = page.locator('a[href*="/jobs/view/"]')
                job = job_links.nth(i)

                try:
                    job.click()
                    page.wait_for_timeout(2000)

                    title_text = ""
                    if page.locator("h1").count() > 0:
                        title_text = page.locator("h1").first.inner_text().strip()

                    desc_box = page.locator(
                        '.jobs-description-content__text, '
                        '.jobs-box__html-content, '
                        '[class*="jobs-description"]'
                    )

                    if desc_box.count() > 0:
                        desc = desc_box.first.inner_text().strip()
                    else:
                        desc = page.inner_text("body")

                    results.append({
                        "search_title": title,
                        "title": title_text,
                        "description": desc
                    })

                except Exception as e:
                    print("Skipped job", i, "because:", e)

        browser.close()
    return results

def saveRes(results):
    file_path = r"E:\\job_results.txt"

    with open(file_path, "w", encoding="utf-8") as f:
        for job in results:
            f.write(f"TITLE: {job['title']}\n")
            f.write(f"DESCRIPTION:\n{job['description']}\n")
            f.write("=" * 80 + "\n")

        print("Saved to:", file_path)

def tokenize(text):
    stopWords = set(stopwords.words("english"))

    words = re.findall(r"[a-zA-Z]+", text.lower())

    return [
        word for word in words
        if word not in stopWords and len(word) > 2
    ]


def build_idf(df):
    # df should contain resume text
    docSets = []
    resumeDf = pd.read_csv(path2)
    resumeTexts = resumeDf["Resume_str"].dropna().astype(str)
    embeddings = vecEmbed(results, resumeTexts)

    for resume in df:
        tokens = tokenize(resume)
        docSets.append(tokens)

    N = len(docSets)
    idf = {}

    all_terms = set()

    for doc in docSets:
        all_terms.update(doc)

    for term in all_terms:
        docs_with_term = 0

        for doc in docSets:
            if term in doc:
                docs_with_term += 1

        if docs_with_term == 0:
            docs_with_term = 1

        idf[term] = math.log(N / docs_with_term)

    return idf


def cleanSet(listing, idf):
    tokens = tokenize(listing)

    if not tokens:
        return {}

    counts = Counter(tokens)
    total_words = len(tokens)
    tfidf_scores = {}

    for term, count in counts.items():
        tf = count / total_words
        term_idf = idf.get(term, 0)
        tfidf_scores[term] = tf * term_idf

    return tfidf_scores


def vecEmbed(arrayListing, df):
    idf = build_idf(df)
    all_scores = []

    for listing in arrayListing:
        if isinstance(listing, dict):
            listing = listing.get("description", "")

        scores = cleanSet(listing, idf)
        all_scores.append(scores)

    return all_scores

def runScraper(title, location):
    path2 = 'resume_dataset.csv'
    df = pd.read_csv(path2)
    path = "https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin"
    username = 'datasetprepper@gmail.com'
    password = 'one2three!'
    closest, geoId, minDist = getCity(location)
    print("Closest city:", closest)
    results = getData(path, username, password, [title], geoId)
    saveRes(results)
    embeddings = vecEmbed(results, df)

    return results, embeddings

if __name__  == "__main__":
    title = "Example"
    location = "Null"
    results = runScraper(title, location)
