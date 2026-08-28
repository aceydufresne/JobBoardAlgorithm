import time
import csv
import schedule
from glassDoor_Agent import getGlassData
#from glassDoor_Agent import startAgent
#from glassDoor_Agent import stopAgent
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


def testSchedule():
    state, cities = stateSet("Georgia")
    positions = getPositions()
    runSchedule(cities, state, positions)

def callTime(state, positions):
    stateName, cities = stateSet(state)

    schedule.every().day.at("09:30").do(
        runSchedule,
        cities,
        stateName,
        positions
    )

    while True:
        schedule.run_pending()
        time.sleep(1)

def stateSet(stateName):
    if stateName == "Georgia":
        cities = [
        "Atlanta",
        "Augusta-Richmond County",
        "Columbus",
        "Macon-Bibb County",
        "Savannah",
        "Athens-Clarke County",
        "South Fulton",
        "Sandy Springs",
        "Roswell",
        "Warner Robins",
        "Johns Creek",
        "Mableton",
        "Albany",
        "Alpharetta",
        "Marietta",
        "Stonecrest",
        "Brookhaven",
        "Smyrna",
        "Valdosta",
        "Dunwoody",
        "Gainesville",
        "Newnan",
        "Peachtree Corners",
        "Milton",
        "Peachtree City",
        "East Point",
        "Rome",
        "Douglasville",
        "Woodstock",
        "Tucker",
        "Evans",
        "Canton",
        "Stockbridge",
        "Hinesville",
        "Kennesaw",
        "Dalton",
        "Statesboro",
        "Martinez",
        "Duluth",
        "LaGrange",
        "Redan",
        "Lawrenceville",
        "McDonough",
        "Chamblee",
        "Pooler",
        "Union City",
        "Carrollton",
        "Sugar Hill",
        "Decatur",
        "Cartersville",
        "Griffin",
        "Perry",
        "Acworth",
        "Suwanee",
        "Snellville",
        "Candler-McAfee",
        "Fayetteville",
        "Kingsland",
        "Forest Park",
        "Winder",
        "St. Marys",
        "Thomasville",
        "Holly Springs",
        "Villa Rica",
        "Conyers",
        "North Decatur",
        "Calhoun",
        "Richmond Hill",
        "Powder Springs",
        "Norcross",
        "Buford",
        "North Druid Hills",
        "Tifton",
        "Grovetown",
        "Lithia Springs",
        "Fairburn",
        "Milledgeville",
        "St. Simons",
        "Dublin",
        "Americus",
        "Monroe",
        "Loganville",
        "Lilburn",
        "Brunswick",
        "Braselton",
        "Jefferson",
        "Riverdale",
        "Dallas",
        "College Park",
        "Moultrie",
        "Covington",
        "Clarkston",
        "Bainbridge",
        "Vinings",
        "Belvedere Park",
        "Wilmington Island",
        "Waycross",
        "Port Wentworth",
        "Mountain Park CDP",
        "Douglas"
        ]
        return stateName, cities

def getPositions():
    titlesPath = ("C:\\Users\\Acey\\Downloads\\Dove Agent Build\\" "Datasets\\titles.csv")
    finalTitles = []

    with open(titlesPath,mode="r",encoding="utf-8-sig",newline="") as titleFile:

        reader = csv.reader(titleFile)
        for row in reader:
            if not row:
                continue

            title = row[0].strip()
            if title:
                finalTitles.append(title)
    return finalTitles


def runSchedule(cities, state, positions):
    for city in cities:
        for position in positions:
            results = getGlassData(
                position,
                city,
                state,
            )


def embedListing(description, model):
    encodedDescription = {}
    words = description.lower().split()

    ngrams = []

    for n in range(1, 4):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i + n])
            ngrams.append(phrase)


    vectors = model.encode(ngrams)

    for phrase, vector in zip(ngrams, vectors):
        encodedDescription[phrase] = vector

    return encodedDescription   




def compareRes(resume, listing):
    threshold = 0.70
    matches = []

    for resumeTerm, resumeVector in resume.items():

        bestMatch = None
        bestScore = -1.0

        for listingTerm, listingVector in listing.items():

            score = cos_sim(
                resumeVector,
                listingVector
            ).item()

            if score > bestScore:
                bestScore = score
                bestMatch = listingTerm

        if bestScore >= threshold:
            matches.append({
                "resume_term": resumeTerm,
                "listing_term": bestMatch,
                "score": bestScore
            })

    return matches



if __name__ == "__main__":
    positions = getPositions()
    callTime("Georgia", positions)
