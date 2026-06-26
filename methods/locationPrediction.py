import spacy
import csv
import pandas as pd
import string
import math

def findLoc(input1, cities, cityPop, allTF):
    tfScores = findTF(input1)
    stateNames = set(cities["state_name"].astype(str).str.lower())
    stateIDs = set(cities["state_id"].astype(str))
    cityNames = set(cities["city"].astype(str).str.lower())
    statePop = set(cities["population"])
    #18713220 max population
    maxPop = max(cities["population"])
    
    
    cityPrediction = []
    statePrediction = []
    #temporary, combined with statePrediction
    idPrediction = []
    popWeight = {}
    cityWeight = {}
    stateWeight = {}
    
    for line in input1:
        line = line.split()
        for term in line:
            term = term.strip(".,;()[]")
            if term in stateIDs:
                idPrediction.append(term)
                #capatalize after id has been checked
            term = term.lower()
            if term in stateNames:
                statePrediction.append(term)
            if term in cityNames:
                cityPrediction.append(term)
    
    #convert the abreviations into full names to add weights to
    newNames = dict(
    zip(
        cities["state_id"].astype(str),
        cities["state_name"].astype(str).str.lower()
    )
)
    for name in idPrediction:
        if name in newNames:
            statePrediction.append(newNames[name])
    
    for element in cityPrediction:
        if element in cityWeight:
            #if element in tfScores:
            bias = findTfIDF(element, tfScores,allTF)
            cityWeight[element] += bias + .2
            #add bias for term frequency
        else:
            #if element in tfScores:
            bias = findTfIDF(element, tfScores, allTF)
            cityWeight[element] = bias + .2
            #check if the element is in the 2nd dataset
        match = cityPop[(cityPop["US City"].str.lower() == element.lower())]
        if not match.empty:
            pop = match.iloc[0]["Population 2024"]
            populationWeight = pop / maxPop * .2
            cityWeight[element] += populationWeight
            
    for element in statePrediction:
        if element in stateWeight:
            #if element in tfScores:
            bias = findTfIDF(element, tfScores,allTF)
            stateWeight[element] += bias + .2
        else:
            #if element in tfScores:
            bias = findTfIDF(element, tfScores, allTF)
            stateWeight[element] = bias + .2

    if not cityPrediction:
        cityPrediction.append("No city found")
        cityWeight["No city found"] = 0
        return "None", "None"
    if not statePrediction:
        statePrediction.append("No state found")
        stateWeight["No state found"] = 0
        return "None", "None"
    if not idPrediction:
        idPrediction.append("No ID")
        
    finalStatePrediction = max(stateWeight, key=stateWeight.get)
    finalCityPrediction = max(cityWeight, key=cityWeight.get)
    sortedCities = sorted(cityWeight.items(), key=lambda x: x[1], reverse=True)
    sortedStates = sorted(stateWeight.items(), key = lambda x: x[1], reverse=True)
    
    finalStatePrediction = sortedStates[0][0]
    finalCityPrediction = sortedCities[0][0]
    
    #make sure the predicted city and state match
    
    for city, score in sortedCities:
        match = cities[
        (cities["city"].str.lower() == city.lower()) &
        (cities["state_name"].str.lower() == finalStatePrediction.lower())
    ]

        if not match.empty:
            finalCityPrediction = city
            break
    return finalCityPrediction, finalStatePrediction




def tfIDF(inputTerm, resumes):
    inputTerm = inputTerm.strip(string.punctuation).lower()
    allRes = []

    for resume in resumes:
        tf = {}
        finalTF = {}
        lenTF = 0
        lines = resume.split("\n")

        for line in lines:
            terms = line.split()
            for term in terms:
                term = term.strip(string.punctuation).lower()
                if term == "":
                    continue
                tf[term] = tf.get(term, 0) + 1
                lenTF += 1
        for term in tf:
            finalTF[term] = tf[term] / lenTF

        allRes.append(finalTF)
    N = len(resumes)
    DF = 0
    for resumeTF in allRes:
        if inputTerm in resumeTF:
            DF += 1
    if DF == 0:
        return 0
    idf = math.log(N / DF)
    scores = []
    for resumeTF in allRes:
        tfScore = resumeTF.get(inputTerm, 0)
        tfidfScore = tfScore * idf
        scores.append(tfidfScore)

    return scores


def findTF(resume):
    tf = {}
    totalTerms = 0

    for line in resume:
        for term in line.split():
            term = term.strip(string.punctuation).lower()
            if term == "":
                continue
            tf[term] = tf.get(term, 0) + 1
            totalTerms += 1

    if totalTerms == 0:
        return {}
    for term in tf:
        tf[term] = tf[term] / totalTerms

    return tf

def findTfIDF(inputTerm, currentTF, allTF):
    inputTerm = inputTerm.strip(string.punctuation).lower()
    N = len(allTF)
    DF = 0

    for res in allTF:
        if inputTerm in res:
            DF += 1
    if DF == 0:
        return 0

    idf = math.log(N / DF)
    tf = currentTF.get(inputTerm, 0)

    return tf * idf
