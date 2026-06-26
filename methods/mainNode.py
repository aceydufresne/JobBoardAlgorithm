import fitz
import os
import pandas as pd
from locationEmbedding import findLoc
from locationEmbedding import findTF
from locationEmbedding import findTfIDF
import spacy
from pypdf import PdfReader
from docx import Document

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
        return extVar, lines
    elif extension[-1] == "docx":
        doc = Document(resPath)
        lines = []
        for line in doc.paragraphs:
            lines.append(line.text)
        return extVar, lines
    elif extension[-1] == "txt":
        #input is already a string
        with open(resPath, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file]
        return extVar, lines
    else:
        negResponse = "Error in extension type"
        return extVar, negResponse

if __name__ == "__main__":
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
    
    tfScores = findTfIDF(example)
    
    city,state = findLoc(text, cities, cityPopulation, example, tfScores)
    
    
    for i in range(20):
        lines = example[i].split("\n")
        
        city, state = findLoc(lines, cities, cityPopulation, example, tfScores)
        print(f"Resume #{i}\nCity: {city}\nState: {state}")

        #print(f"Resume #{i}\n\n {lines}")
