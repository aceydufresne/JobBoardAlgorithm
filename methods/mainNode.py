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
        titleSet["Titles"]
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
    tempTitle = "C:\\Users\Acey\\Downloads\\Dove Agent Build\\Datasets\\job_dataset.csv"
    titleSet = pd.read_csv(tempTitle)
    encodedMap = {}
    skillSet = titleSet["Skills"].dropna().astype(str).str.lower().unique()

    for skills in titleSet["Skills"].dropna():
        for skill in skills.split(","):
            skill = skill.strip().lower()

            if skill not in encodedMap:
                encodedMap[skill] = vectorModel.encode(skill)
    return encodedMap
        
if __name__ == "__main__":
    
    vectorModel = SentenceTransformer("all-MiniLM-L6-v2")
    encodedMap = encodeTerms(vectorModel)
    encodedSkills = encodeSkills(vectorModel)
    
    print(list(encodedMap.keys())[:20])
    
    model = spacy.load("en_core_web_sm")
    #input is an environmental variable
    citiesCSV = "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\Datasets\\uscities.csv"
    cities = pd.read_csv(citiesCSV)
    inputPath =  "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\Agent Modules\\Dufresne Resume Spring 2025 (1).pdf"
    
    resExam = "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\Datasets\\Resume.csv"
    resumes = pd.read_csv(resExam)
    example = resumes["Resume_str"]
    
    cityPop = "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\Datasets\\cityPop.csv"
    cityPopulation = pd.read_csv(cityPop)
    
    extVar, text = uploadRes(inputPath)
    if text == "Error in extension type":
        print(text)
    
    tfScores = []
    for resume in example:
        lines = resume.split("\n")
        temp = findTF(lines)
        tfScores.append(temp)
    
    city,state = findLoc(text, cities, cityPopulation, tfScores)
    
    
    for i in range(20):
        lines = example[i].split("\n")
        
        pos, val = getPos(lines,encodedMap,encodedSkills, vectorModel)
        print(f"Resume #{i}\nPosition Prediction: {pos}\Value: {val}")
        
        city, state = findLoc(lines, cities, cityPopulation, tfScores)
        print(f"Resume #{i}\nCity: {city}\nState: {state}")

        #print(f"Resume #{i}\n\n {lines}")
    
