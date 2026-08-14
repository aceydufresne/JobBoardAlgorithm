from sentence_transformers import SentenceTransformer
import random as rand
from datasets import load_dataset

def loadWeights():
     vectorModel = SentenceTransformer("all-MiniLM-L6-v2")
     return vectorModel

def agent(path):
    agent_name = ["Dove", "Carla", "Levi"]
    #model = loadWeights()
    RanName = rand.randrange(len(agent_name))
    name = agent_name[RanName]
    greetingToken = ["Hello,", "Hey,", "How are you?"]
    ranGreet = rand.randrange(len(greetingToken))
    greet = greetingToken[ranGreet]
    firstMessage(greet, path)

def callAssociate(message, term):
    print("Calling employee")
    print(f"User said {message}")
    print(f"{term} was flagged")

def firstMessage(greetToken, path):
    interrogativeTokens = ["How", "What"]
    ranInter = rand.randrange(len(interrogativeTokens))
    interrogativeToken = interrogativeTokens[ranInter]
    #redundant but can easily be modified later
    if interrogativeToken == "How":
        firstQuestion = "How are you doing today?"
        print(firstQuestion)
        pathway = 0
    elif interrogativeToken == "What":
        firstQuestion = "What can I help you with today?"
        print(firstQuestion)
        pathway = 1
    response = input()
    
    isGoing = True
    sentinmentScore = 0.0
    suspiciousMeter = 0.0
    
    ##main conversation loop
    while isGoing:
        print("Testing")
        userMessage = input()
        attitudeWords = {"fuck": .5,
                         "fucking": .5,
                         "fuckin": .5,
                         "fucker": .5,
                         "motherfucker": .5,
                         "mother fucker": .5,
                         "mother fucking": .5,
                         "motherfucking": .5,
                         "motha fucka": .3,
                         "shit": .3,
                         "cunt": .7,
                         "bitch": .3,
                         "ass" : .5,
                         "asshole": .5,
                         "dam": .2,
                         "damn": .3,
                         "dammit" : .3,
                         "damnit": .3,
                         
                         }
        stopWords = {"kill": .7,
                     "killed": 1.0,
                     "killing": 1.0,
                     "murder" : 1.0,
                     "murdering": 1.0,
                     "shoot" : .7,
                     "shooting": .7,
                     "shootup": .7,
                     "shotup": .7,
                     "shot": .7,
                     "killing myself": .7,
                     "killingmyself" : .7
        }
        message = userMessage.split()
        
        for term in message:
            
            if term in attitudeWords:
                sentinmentScore += attitudeWords[term]
            elif term in stopWords:
                callAssociate(userMessage, term)
            if term not in stopWords:
                tempChar = list(term)
                
                for key, value in stopWords.items():
                    compareLength = min(len(term), len(key))
                    stopThreshold = round(compareLength * 0.7)
                    stopChat = 0
                    tempKey = list(key)
                    
                    if len(tempChar) >= 6:
                        if len(tempKey) >= len(tempChar):
                        
                            for i in range(len(tempChar)):
                                if tempChar[i] == tempKey[i]:
                                    stopChat += 1
                                    if stopChat >= stopThreshold:
                                        callAssociate(message, term)
                                        isGoing = False
                                        break
                        elif len(tempKey) < len(tempChar):
                            for j in range(len(tempKey)):
                                if tempChar[j] == tempKey[j]:
                                    stopChat+=1
                                    if stopChat>=stopThreshold:
                                        callAssociate(message, term)
                                        isGoing = False
                                        break
                                    #redundent check, will remove later
                                    #sanity check
                    elif len(tempChar) < 6:
                        stopThreshold = len(tempChar)
                        for key, value in stopWords.items():
                            tempKey = list(key)
                            if len(tempKey) >= len(tempChar):
                                for i in range(len(tempChar)):
                                    if tempChar[i] == tempKey[i]:
                                        stopChat+=1
                                        if stopChat >= stopThreshold:
                                            callAssociate(message, term)
                                            isGoing = False
                                            break
                            elif len(tempKey) <= len(tempChar):
                                for j in range(len(tempKey)):
                                    if tempChar[j] == tempKey[j]:
                                        stopChat+=1
                                        if stopChat>= stopThreshold:
                                            callAssociate(message, term)
                                            isGoing = False
                                            break
                            
                            
            else:
                print("No stopwords found yet")
                
                
    
if __name__ == "__main__":
    path = "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\Datasets\\train\\train\\dialogues_train.txt"
    print("Ready to run")
    agent(path)
