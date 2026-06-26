import spacy
import csv
import pandas as pd

def findLoc(input1, cities, cityPop):
    stateNames = set(cities["state_name"].astype(str).str.upper())
    stateIDs = set(cities["state_id"].astype(str).str.upper())
    cityNames = set(cities["city"].astype(str).str.upper())
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
            term = term.upper()
            if term in stateNames:
                statePrediction.append(term)
            if term in cityNames:
                cityPrediction.append(term)
    
    #convert the abreviations into full names to add weights to
    newNames = dict(
    zip(
        cities["state_id"].astype(str).str.upper(),
        cities["state_name"].astype(str).str.upper()
    )
)
    for name in idPrediction:
        if name in newNames:
            statePrediction.append(newNames[name])
    
    for element in cityPrediction:
        if element in cityWeight:
            #add bias for term frequency
            cityWeight[element] += .2
        else:
            cityWeight[element] = .2
            #check if the element is in the 2nd dataset
        match = city[(cityPop["US City"].str.upper() == element.upper())]
        if not match.empty:
            pop = match.iloc[0]["Population 2024"]
            populationWeight = pop / maxPop * .2
            cityWeight[element] += populationWeight
            
    for element in statePrediction:
        if element in stateWeight:
            stateWeight[element] += .2
        else:
            stateWeight[element] = .2
    
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
        (cities["city"].str.upper() == city.upper()) &
        (cities["state_name"].str.upper() == finalStatePrediction.upper())
    ]

        if not match.empty:
            finalCityPrediction = city
            break
    return finalCityPrediction, finalStatePrediction
