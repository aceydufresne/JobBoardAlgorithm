import pandas as pd
import nltk
from sentence_transformers import SentenceTransformer
from sentence_transformers import util


#var = lines in main.py
def getPos(rawTxt, encodedMap, model):
    tempTitle = "C:\\Users\Acey\\Downloads\\Dove Agent Build\\Datasets\\job_dataset.csv"
    titleSet = pd.read_csv(tempTitle)
    posSet = titleSet["Title"].dropna().astype(str).str.lower().unique()
    skillSet = titleSet["Skills"].dropna().astype(str).str.lower().unique()
    tWeight = .2
    termWeights = {}
    options ={}
    position = None
    choice1 = None
    choice1val = 0
    choice2 = None
    choice2val = 0
    gram3 = None
    gram3Val = 0
    gram2 = None
    gram2Val = 0
    finalPicks = {}
    
    
    for line in rawTxt:
        ngram = []
        ngram2 = []
        words = [
        word.strip(".,;()[]").lower()
        for word in line.split()
    ]

        for i in range(len(words) - 3 + 1):
            gram = " ".join(words[i:i + 3])

            pick3 = posSkills(gram, encodedMap, model)

            for name, val in pick3.items():
                if name in finalPicks:
                    finalPicks[name] += val
                else:
                    finalPicks[name] = val

        for j in range(len(words) - 2 + 1):
            gram = " ".join(words[j:j + 2])

            pick2 = posSkills(gram, encodedMap, model)

            for name, val in pick2.items():
                if name in finalPicks:
                    finalPicks[name] += val
                else:
                    finalPicks[name] = val


        for term in line:
            
            term = term.strip(".,;()[]").lower()
                
            if term in posSet:
                if term in termWeights:
                    termWeights[term] += tWeight
                else:
                    termWeights[term] = tWeight
            else:
                #bestChoices = embedded vectors, topPick term name
                topPick = posSkills(term, encodedMap, model)
                for name,val in topPick.items():
                    if name in options:
                        options[name] += val
                    else:
                        options[name] = val
                if not options:
                    choice2 = None
                else:
                    choice2 = max(options, key=options.get)
                    choice2val = max(options.values())
            
    if not termWeights:
        print("error")
        choice1 = None
    else:
        choice1 = max(termWeights, key=termWeights.get)
        choice1val = max(termWeights.values())
    if choice1val > choice2val:
        if choice1val == 0:
            return 0
        else:
            return (choice1,choice1val)
    elif choice2val > choice1val:
        if choice2val == 0:
            return 0
        else:
            return (choice2,choice2val)
    else:
        print("error")
    


def posSkills(term, encodedMap, vectorModel):
    embedding = vectorModel.encode(term)

    topPickTerm = None
    topPickVal = -1

    for skill, vector in encodedMap.items():
        if term == skill:
            return {skill: 1.0}

        sim = util.cos_sim(embedding, vector).item()

        if sim > topPickVal:
            topPickVal = sim
            topPickTerm = skill

    if topPickTerm is None:
        return {}

    return {topPickTerm: topPickVal}
