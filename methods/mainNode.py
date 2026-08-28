import fitz
import os
import pandas as pd
from locationEmbedding import findLoc
from locationEmbedding import findTF
from locationEmbedding import findTfIDF
import spacy
from pypdf import PdfReader
from docx import Document
import mysql.connector
from dbAgent import fetch
from dbAgent import update_term
import string
from sentence_transformers import SentenceTransformer
from findPosition import getPos
from findPosition import posSkills
from linkedIn_Agent import runScraper
from linkedIn_Agent import getLinkedData
from linkedIn_Agent import getCity
from zipRecruit_Agent import getData
from glassDoor_Agent import getGlassData
import numpy as np
from scrapingAgent import embedListing
from scrapingAgent import compareRes
import pandas as pd
import numpy as np
import mysql.connector


def uploadRes(resPath):
    
    #sort based upon if the input is already a txt format,
    #or pdf extension
    extVar = None
    extension = resPath.split(".")
    if extension[-1] == "pdf":
        reader = PdfReader(resPath)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        lines = text.split("\n")
        lines = [line.strip() for line in lines if line.strip()]
        
    elif extension[-1] == "docx":
        doc = Document(resPath)
        lines = []
        for line in doc.paragraphs:
            lines.append(line.text)
            
    elif extension[-1] == "txt":
        #input is already a string
        with open(resPath, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file]
            
    else:
        negResponse = "Error in extension type"
        return extVar, negResponse
    
    termSend(lines)
    return extVar, lines
    
    
def termSend(lines):

    termMap = {}
    for line in lines:
        for word in line.split():
            word = word.lower()
            word = word.strip(string.punctuation)
            
            if word:
                if word not in termMap:
                    termMap[word] = 1
                    update_term(word, True)
                    
                else:
                    update_term(word, False)
                    termMap[word] += 1
                


jobDatasetPath = (
    r"C:\Users\Acey\Downloads\Dove Agent Build"
    r"\Datasets\job_dataset.csv"
)


def encodeTerms(model):
    encodedMap = {}

    jobData = pd.read_csv(jobDatasetPath)

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="***",
        database="encodedTerms"
    )

    cursor = conn.cursor()

    for title in jobData["Title"]:
        
        if pd.isna(title):
            continue
        
        title = title.lower().strip()

        if title in encodedMap:
            continue

        cursor.execute(
            "SELECT vector FROM term_vectors WHERE term = %s",
            (title,)
        )

        result = cursor.fetchone()

        if result is not None:

            vector = np.frombuffer(
                result[0],
                dtype=np.float32
            )

        else:

            vector = model.encode(title)
            cursor.execute(
                """
                INSERT INTO term_vectors (term, vector)
                VALUES (%s, %s)
                """,
                (
                    title,
                    vector.astype(np.float32).tobytes()
                )
            )

        encodedMap[title] = vector

    conn.commit()
    cursor.close()
    conn.close()

    return encodedMap

def encodeSkills(model):
    encodedSkills = {}

    path = r"C:\Users\Acey\Downloads\Dove Agent Build\Datasets\job_dataset.csv"
    jobData = pd.read_csv(path)

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="***",
        database="encodedTerms"
    )

    cursor = conn.cursor()

    for _, row in jobData.iterrows():

        # Skip incomplete rows
        if pd.isna(row["Title"]) or pd.isna(row["Skills"]):
            continue

        title = row["Title"].lower().strip()
        skills = row["Skills"].split(";")

        for skill in skills:
            skill = skill.lower().strip()

            if not skill:
                continue

            if len(skill) > 255:
                print("Skipping oversized skill:")
                print(skill)
                continue

            if skill in encodedSkills:
                encodedSkills[skill]["titles"].add(title)
                continue

            cursor.execute(
                "SELECT vector FROM term_vectors WHERE term = %s",
                (skill,)
            )

            result = cursor.fetchone()

            if result is not None:
                vector = np.frombuffer(
                    result[0],
                    dtype=np.float32
                )

            else:
                vector = model.encode(skill)

                cursor.execute(
                    """
                    INSERT INTO term_vectors (term, vector)
                    VALUES (%s, %s)
                    """,
                    (
                        skill,
                        vector.astype(np.float32).tobytes()
                    )
                )

            encodedSkills[skill] = {
                "vector": vector,
                "titles": {title}
            }

    conn.commit()
    cursor.close()
    conn.close()

    return encodedSkills


def testPositions(posSet, encodedMap, encodedSkills, vectorModel, resumes):
    results = []

    for _, row in resumes.iterrows():
        resume = row["Resume_str"]

        if pd.isna(resume):
            continue

        rawTxt = str(resume).splitlines()

        result = getPos(rawTxt,encodedMap,encodedSkills,vectorModel,posSet)
        results.append(result)

    return results
        
        
if __name__ == "__main__":

    vectorModel = SentenceTransformer("all-MiniLM-L6-v2")

    encodedMap = encodeTerms(vectorModel)
    encodedSkills = encodeSkills(vectorModel)

    model = spacy.load("en_core_web_sm")

    citiesCSV = (
        "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\"
        "Datasets\\uscities.csv"
    )
    cities = pd.read_csv(citiesCSV)

    inputPath = (
        "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\"
        "Agent Modules\\Dufresne Resume Spring 2025 (1).pdf"
    )

    resExam = (
        "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\"
        "Datasets\\Resume.csv"
    )
    resumes = pd.read_csv(resExam)

    cityPop = (
        "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\"
        "Datasets\\cityPop.csv"
    )
    cityPopulation = pd.read_csv(cityPop)

    tempTitle = (
        "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\"
        "Datasets\\job_dataset.csv"
    )

    titleSet = pd.read_csv(tempTitle)

    posSet = set(
        titleSet["Title"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
    )

    extVar, rawExample = uploadRes(inputPath)

    allTF = findTF(rawExample)

    city, state = findLoc(
        rawExample,
        cities,
        cityPopulation,
        allTF
    )

    position = getPos(
        rawExample,
        encodedMap,
        encodedSkills,
        vectorModel,
        posSet
    )



    zipResults = getData(
        position["title"],
        city,
        state
    )

    glassResults = getGlassData(
        position["title"],
        city,
        state
    )

    allJobs = zipResults + glassResults


    embeddedListings = []

    for job in allJobs:

        description = job["description"]

        if not description:
            continue

        embedded = embedListing(
            description,
            vectorModel
        )

        embeddedListings.append({
            "title": job["title"],
            "url": job["url"],
            "description": description,
            "embeddings": embedded
        })
        
        
    resumeText = " ".join(rawExample)

    embeddedResume = embedListing(
        resumeText,
        vectorModel
    )

    allMatches = []

    for listing in embeddedListings:

        matches = compareRes(
            embeddedResume,
            listing["embeddings"]
        )

        allMatches.append({
            "title": listing["title"],
            "url": listing["url"],
            "matches": matches
        })
