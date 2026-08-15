from sentence_transformers import SentenceTransformer, util
import random as rand


def loadWeights():
     vectorModel = SentenceTransformer("all-MiniLM-L6-v2")
     return vectorModel

def agent(path):
    agent_name = ["Dove", "Carla", "Levi"]
    model = loadWeights()
    RanName = rand.randrange(len(agent_name))
    name = agent_name[RanName]
    greetingToken = ["Hello,", "Hey,", "How are you?"]
    ranGreet = rand.randrange(len(greetingToken))
    greet = greetingToken[ranGreet]
    firstMessage(greet, path, model)

def callAssociate(message, term):
    print("Calling employee")
    print(f"User said {message}")
    print(f"{term} was flagged")
    
def levenshteinDist(term1, term2):
    cleaned_term1 = term1.lower().replace(" ", "")
    cleaned_term2 = term2.lower().replace(" ", "")
    term1Array = list(term1)
    term2Array = list(term2)
    #term1Array.insert(0,0)
    #term2Array.insert(0,0)
    term1Array.append(" ")
    term2Array.append(" ")
    levList = [term1Array,term2Array]
    
    if not cleaned_term1:
        if len(cleaned_term2) > 0:
            return len(cleaned_term2)
        else:
            print("empty words, error")
    elif not cleaned_term2:
        if len(cleaned_term1) > 0:
            return len(cleaned_term1)
        else:
            print("empty words, error")
    
    elif term1 == term2:
        return 0
    
    else:
        cache = [[float("inf")]*(len(term2)+1) for i in range(len(term1)+1)]
        for j in range(len(term2)+1):
            cache[len(term1)][j] = len(term2)-j
        for i in range(len(term1)+1):
            cache[i][len(term2)] = len(term1)-i
        
        for i in range(len(term1)- 1, -1, -1):
            for j in range(len(term2)-1,-1,-1):
                if term1[i] == term2[j]:
                    cache[i][j] = cache[i+1][j+1]
                else:
                    cache[i][j] = 1 + min(cache[i+1][j], cache[i][j+1], cache[i+1][j+1])
                    
    return cache[0][0]

def messageSet(model):
    uploadRes = ["find a job", "a nice place to work", "career"]
    uploadLoc = ["you find my address", "state should i be looking in", "city am i in"]
    resSet = []
    locSet = []
    for val in uploadRes:
        tempEmbed = model.encode(val)
        resSet.append(tempEmbed)
    for val in uploadLoc:
        tempEmbed = model.encode(val)
        locSet.append(tempEmbed)
    
    return resSet, locSet
   
def skipGram(message,model):
    skipVal = 3
    messages = messageSet(model)
    isFound = False
    message = message.split()

    for target in messages:
        for i, word in enumerate(message):
            start = max(0, i - skipVal)
            end = min(len(message), i + skipVal + 1)

            for j in range(start, end):
                if i == j:
                    continue

                contextWord = message[j]
                tempVal = levenshteinDist(target,contextWord)
                if tempVal <= 3:
                    isFound = True
    return isFound

def nextMessage(currentContext,model):
    if currentContext == " ":
        return "How can I help you today?"
    else:
        message = botResponse(currentContext,model)
        return message


def firstMessage(greetToken, path, model):
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
    stopSentinment = -0.5
    badMood = False
    
    requests = ["need", "want", "can", "looking", "require"]
    addressing = ["you", "me", "i", "him", "her"]
    addressing = addressing.extend(["Dove", "Carla", "Levi"])
    affirmResponse = ["yes", "of course", "obviously","please", "do that"]
    negativeResponse = ["no", "not", "of course not", "obviously not", "please dont", "dont"]
    newMessage = nextMessage(" ", model)
    
    ##main conversation loop
    while isGoing:
        attitude_threshold = 3
        
        if sentinmentScore <= stopSentinment:
            badMood = True
            print("It seems like you are irritated, can I pass you to another employee?")
            response = input()
            
        
        print(newMessage)
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
        
        
        message = input().split()
        
        requestNode = False
        memory = 7
        tempBool = False
        context = 5
        tempUserMess = []
        tempCount = 0
        
        for term in message:
            tempCount += 1
            if requestNode == True:
                memory -= 1
                if term in addressing:
                    requestNode = True
                    memory = 7
            elif term in addressing:
                requestNode == True
                memory -= 1
                tempBool = True
            elif tempBool == True:
                if term in requests:
                    requestNode = True
                    memory -= 1
            elif tempBool == True and requestNode == True:
                tempUserMess.append(term)
            elif tempCount == len(message) and sentinmentScore >= stopSentinment and isGoing == True:
                embeddedMessage = userMessage(message)
                botResponse(embeddedMessage, model)

            if term in attitudeWords:
                sentinmentScore += attitudeWords[term]
            elif term in stopWords:
                callAssociate(userMessage, term)
            if term not in stopWords:
                tempChar = list(term)
                
                for index in attitudeWords:
                    dist = levenshteinDist(term, index)
                    if dist > attitude_threshold:
                        tempVal = attitudeWords[index]
                        sentinmentScore -= tempVal
                    else:
                        break
                for index in stopWords:
                    dist = levenshteinDist(term, index)
                    if dist > attitude_threshold:
                        tempVal = stopWords[index]
                        stopSentinment += tempVal
                    else:
                        break
                
                if term in requests:
                    requestNode = True
                    
                else:
                    requestNode = False
                    memory = 7

def userMessage(message, model):
    requests = ["need", "want", "can", "looking", "require"]
    addressing = ["you", "me", "i", "him", "her"]
    terms = message.split()
    finalContext = []
    for term in terms:
        if term in requests:
            break
        elif term in addressing:
            break
        else:
            finalContext.append(term)
    embeddedMessage = model.encode(finalContext)
    return embeddedMessage

def botResponse(userMessage, model):
        res, loc = messageSet(model)
        bestChoice = " "
        bestChoiceVal = 0.0
        for val in res:
            tempSim = util.cos_sim(val, userMessage)
            if tempSim >= bestChoiceVal:
                bestChoice = val
                bestChoiceVal = tempSim
            else:
                break
        for val in loc:
            tempSim = util.cos_sim(val, userMessage)
            if tempSim >= bestChoiceVal:
                bestChoice = val
                bestChoiceVal = tempSim
        if bestChoice in res:
            nextMessage("Sure, I can help you find a job listing.", model)
            return "Sure, I can help you find a job listing."
        elif bestChoice in loc:
            nextMessage("Of course, let me find the current location listed in your resume.", model)
            return "Of course, let me find the current location listed in your resume."
        
if __name__ == "__main__":
    path = "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\Datasets\\train\\train\\dialogues_train.txt"
    print("Ready to run")
    agent(path)
