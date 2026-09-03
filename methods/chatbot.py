import json

globalTokens = []

def loadMerges():
    path = r"C:\Users\Acey\Downloads\Dove Agent Build\Datasets\tokenData.json"
    with open(path, "r", encoding="utf-8") as file:
        mergeData = json.load(file)

    merges = []

    for left, right, tokenID in mergeData:
        merges.append(((left, right), tokenID))

    return merges


def trainModel(merges):
    path = "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\Datasets\\train\\train\\dialogues_train.txt"
    trainingData = []

    BOS = 2000
    EOU = 2001
    EOS = 2002

    with open(path, "r", encoding="utf-8") as file:

        for line in file:
            conversation = [BOS]
            utterances = line.strip().split("__eou__")

            for utterance in utterances:
                utterance = utterance.strip()
                if utterance:
                    encodedMessage = encodeMessage(utterance,merges)
                    conversation.extend(encodedMessage)
                    conversation.append(EOU)

            conversation.append(EOS)
            trainingData.append(conversation)

    return trainingData


def encodeMessage(message, merges):
    #iterate through message and check for matching pairs in respecti to the json file list
    tokens = list(message.encode("utf-8"))
    for pair, tokenID in merges:
        newTokens = []
        i = 0
        while i<len(tokens):
            if(i<len(tokens) - 1 and (tokens[i], tokens[i+1]) == pair):
                newTokens.append(tokenID)
                i+=2
            else:
                newTokens.append(tokens[i])
                i+=1
        tokens = newTokens
        
    return tokens


def decodeToken(token, decoder):

    if token < 256:
        return [token]

    left, right = decoder[token]

    return (decodeToken(left, decoder)+ decodeToken(right, decoder))


def decodeMessage(tokens, decoder, merges):
    byteTokens = []

    for token in tokens:
        byteTokens.extend(decodeToken(token, decoder))
    byteData = bytes(byteTokens)

    return byteData.decode("utf-8")
        


def decoder(merges):
    decoder = {}
    #finding the combination of initial tokens, or rules
    for pairs, tokenID in merges:
        decoder[tokenID] = pairs
    return decoder
    

def tokenizer(path):
    global globalTokens
    outputPath = r"C:\Users\Acey\Downloads\Dove Agent Build\Datasets\tokenData.json"
    
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            conversation = line.strip()
            #end of utterance
            eou = conversation.split("__eou__")

            for utterance in eou:
                utterance = utterance.strip()

                if utterance:
                    
                    byteData = utterance.encode("utf-8")
                    tokens = list(byteData)
                    globalTokens.append(tokens)
    #now begin finding the patternsL
    
    merges = {}
    currentByte = 256
    
    while currentByte<2000:
        pairCounts = {}
        
        for unqToken in globalTokens:
            for i in range(len(unqToken)-1):
                pair = (unqToken[i], unqToken[i+1])
                pairCounts[pair] = pairCounts.get(pair,0) + 1
                
                #most common pattern
        if not pairCounts:
            break
        highestComm = max(pairCounts,key=pairCounts.get)
        updatedToken = currentByte
        merges[highestComm] = updatedToken
        updateGlobalTokens = []
        
        for unqToken in globalTokens:
            newTokens = []
            i = 0
        #replace the old pattern with a standard new byte
            while i < len(unqToken):
                if (i < len(unqToken) - 1 and (unqToken[i], unqToken[i + 1]) == highestComm):
                    newTokens.append(updatedToken)
                    i += 2
                else:
                    newTokens.append(unqToken[i])
                    i += 1
                
            updateGlobalTokens.append(newTokens)
        globalTokens = updateGlobalTokens
        currentByte += 1
    
    mergeData = []
    for pair, tokenID in merges.items():
        mergeData.append([pair[0],pair[1],tokenID])
    
    with open(outputPath, "w", encoding="utf-8") as file:
        json.dump(mergeData, file)


if __name__ == "__main__":
    path = "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\Datasets\\train\\train\\dialogues_train.txt"
    print("Ready to run")
    test = "C:\\Users\\Acey\\Downloads\\Dove Agent Build\\Datasets\\testingEOU.txt"
    #tokenizer(path)
    #print(globalTokens)
    merges = loadMerges()
    trainingData = trainModel(merges)
    outputPath = r"C:\Users\Acey\Downloads\Dove Agent Build\Datasets\trainingTokens.json"

    with open(outputPath, "w", encoding="utf-8") as file:
        json.dump(trainingData, file)
