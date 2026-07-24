import pandas as pd
import nltk
from sentence_transformers import SentenceTransformer
from sentence_transformers import util


#var = lines in main.py
import pandas as pd
from sentence_transformers import util


def getPos(rawTxt, encodedMap, encodedSkills, model):
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

    tWeight = 0.2
    termWeights = {}
    options = {}
    optionSkills = {}
    finalPicks = {}

    for line in rawTxt:
        words = [
            word.strip(".,;:!?()[]{}\"'").lower()
            for word in line.split()
            if word.strip(".,;:!?()[]{}\"'")
        ]

        for i in range(len(words) - 2):
            gram = " ".join(words[i:i + 3])

            pick3 = posTitles(
                gram,
                encodedMap,
                model
            )

            for title, score in pick3.items():
                if title in finalPicks:
                    finalPicks[title] += score
                else:
                    finalPicks[title] = score

        for j in range(len(words) - 1):
            gram = " ".join(words[j:j + 2])

            pick2 = posTitles(
                gram,
                encodedMap,
                model
            )

            for title, score in pick2.items():
                if title in finalPicks:
                    finalPicks[title] += score
                else:
                    finalPicks[title] = score

        for term in words:

            if term in posSet:
                if term in termWeights:
                    termWeights[term] += tWeight
                else:
                    termWeights[term] = tWeight

            else:
                topPick = posSkills(
                    term,
                    encodedSkills,
                    model
                )

                for title, matchData in topPick.items():
                    score = matchData["score"]
                    matchedSkill = matchData["skill"]

                    if title in options:
                        options[title] += score
                    else:
                        options[title] = score

                    if (
                        title not in optionSkills
                        or score > optionSkills[title]["score"]
                    ):
                        optionSkills[title] = {
                            "skill": matchedSkill,
                            "score": score
                        }

    if termWeights:
        choice1 = max(termWeights, key=termWeights.get)
        choice1val = termWeights[choice1]
    else:
        choice1 = None
        choice1val = 0

    if options:
        choice2 = max(options, key=options.get)
        choice2val = options[choice2]
        choice2skill = optionSkills[choice2]["skill"]
    else:
        choice2 = None
        choice2val = 0
        choice2skill = None

    if finalPicks:
        ngramBest = max(finalPicks, key=finalPicks.get)
        ngramBestVal = finalPicks[ngramBest]
    else:
        ngramBest = None
        ngramBestVal = 0

    choices = [
        {
            "title": choice1,
            "score": choice1val,
            "source": "exact title",
            "skill": None
        },
        {
            "title": choice2,
            "score": choice2val,
            "source": "skill",
            "skill": choice2skill
        },
        {
            "title": ngramBest,
            "score": ngramBestVal,
            "source": "title phrase",
            "skill": None
        }
    ]

    choices = [
        choice
        for choice in choices
        if choice["title"] is not None
    ]

    if not choices:
        return 0

    bestChoice = max(
        choices,
        key=lambda choice: choice["score"]
    )

    if bestChoice["score"] <= 0:
        return 0

    return bestChoice
    


def posSkills(term, encodedSkills, vectorModel):
    embedding = vectorModel.encode(term)

    bestSkill = None
    bestScore = -1

    for skill, skillData in encodedSkills.items():
        vector = skillData["vector"]

        if term == skill:
            bestSkill = skill
            bestScore = 1.0
            break

        score = util.cos_sim(embedding, vector).item()

        if score > bestScore:
            bestScore = score
            bestSkill = skill

    if bestSkill is None:
        return {}

    return {
        title: {
            "score": bestScore,
            "skill": bestSkill
        }
        for title in encodedSkills[bestSkill]["titles"]
    }

def posTitles(term, encodedTitles, vectorModel):
    embedding = vectorModel.encode(term)

    bestTitle = None
    bestScore = -1

    for title, vector in encodedTitles.items():
        if term == title:
            return {title: 1.0}

        score = util.cos_sim(embedding, vector).item()

        if score > bestScore:
            bestScore = score
            bestTitle = title

    if bestTitle is None:
        return {}

    return {bestTitle: bestScore}
