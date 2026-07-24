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
from linkedIn_Agent import getCity


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
                
def encodeTerms(vectorModel):
    tempTitle = "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\Datasets\\job_dataset.csv"
    titleSet = pd.read_csv(tempTitle)

    encodedMap = {}

    titleSet = (
        titleSet["Title"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
        .unique()
    )

    for title in titleSet:
        encodedMap[title] = vectorModel.encode(title)

    return encodedMap

def encodeSkills(vectorModel):
    tempTitle = (
        "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\"
        "Datasets\\job_dataset.csv"
    )

    titleSet = pd.read_csv(tempTitle)
    encodedMap = {}

    for _, row in titleSet.iterrows():
        if pd.isna(row["Title"]) or pd.isna(row["Skills"]):
            continue

        title = str(row["Title"]).strip().lower()

        for skill in str(row["Skills"]).split(","):
            skill = skill.strip().lower()

            if not skill:
                continue

            if skill not in encodedMap:
                encodedMap[skill] = {
                    "vector": vectorModel.encode(skill),
                    "titles": []
                }

            if title not in encodedMap[skill]["titles"]:
                encodedMap[skill]["titles"].append(title)

    return encodedMap
        
if __name__ == "__main__":

    vectorModel = SentenceTransformer("all-MiniLM-L6-v2")
    encodedMap = encodeTerms(vectorModel)
    encodedSkills = encodeSkills(vectorModel)

    #print(list(encodedMap.keys())[:20])

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
    example = resumes["Resume_str"]

    cityPop = (
        "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\"
        "Datasets\\cityPop.csv"
    )
    cityPopulation = pd.read_csv(cityPop)

    extVar, text = uploadRes(inputPath)

    if text == "Error in extension type":
        print(text)
    else:
        city, state = findLoc(
            text,
            cities,
            cityPopulation,
            []
        )

    tfScores = []

    for resume in example.dropna():
        lines = str(resume).split("\n")
        temp = findTF(lines)
        tfScores.append(temp)

    lastPosition = None
    lastCity = None

    for i in range(min(20, len(example))):
        resumeText = example.iloc[i]

        if pd.isna(resumeText):
            print(f"Resume #{i} is empty.")
            continue

        lines = str(resumeText).split("\n")

        prediction = getPos(
            lines,
            encodedMap,
            encodedSkills,
            vectorModel
        )

        if prediction == 0:
            pos = None
            val = 0
            matchedSkill = None
            source = None
        else:
            pos = prediction["title"]
            val = prediction["score"]
            matchedSkill = prediction["skill"]
            source = prediction["source"]

        print(
            f"Resume #{i}\n"
            f"Position Prediction: {pos}\n"
            f"Value: {val}\n"
            f"Matched Skill: {matchedSkill}\n"
            f"Source: {source}"
        )

        city, state = findLoc(
            lines,
            cities,
            cityPopulation,
            tfScores
        )

        print(
            f"Resume #{i}\n"
            f"City: {city}\n"
            f"State: {state}"
        )

        if pos is not None:
            lastPosition = pos

        if city is not None:
            lastCity = city

    if lastPosition is not None and lastCity is not None:
        results, embeddings = runScraper(
            lastPosition,
            lastCity
        )
    else:
        print("No valid position and city available for the scraper.")
