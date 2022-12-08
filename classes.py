import pandas as pd
import xlsxwriter
import re
from tqdm import tqdm
import numpy as np
import binascii
import random
import math
from collections import defaultdict
    
#Rename parts of the titles so they are comparable
def standardizeTitles(data: pd.DataFrame):
    data = data.reset_index()  # make sure indexes pair with number of rows
    
    
    
    for index, row in data.iterrows():   
        editedTitle = row['title'].lower()        
        
        #make sure they all look the same and remove some common words
        editedTitle = re.sub('(newegg.com|thenerds.net|best buy|diag|class)', '', editedTitle )
        editedTitle = re.sub('(-inch|"|inches| inch|"|in.)', 'inch', editedTitle )
        editedTitle= re.sub('(hertz| hz|-hz)', 'hz', editedTitle )
        editedTitle  = re.sub('(ledlcd|LED-LCD)', 'led lcd', editedTitle )
        editedTitle  = re.sub(r'[^0-9^a-zA-Z ]', '', editedTitle)
        data._set_value(index,'title',editedTitle) 
    return data


    
def removeSingleOccurenceWords(data: pd.DataFrame):
    titlewords = []   
    
    #iterate over each title and add each word of the title to a pd.series
    for title in data["title"]:
        for word in title.split():
            titlewords.append(word)
    wordcount = pd.Series(titlewords).value_counts()
    wordcount.name = "Count"
    
    #Set index as a seperate column
    wordcount = wordcount.rename_axis('Word').reset_index()
    singleWordList = wordcount[wordcount['Count'] == 1]
    
    
    for singleWord in singleWordList['Word']:   
        for index, title in enumerate(data['title']):   
            #returns true if the title contains the single word.     
            if bool(re.search(r"\b{}\b".format(singleWord), title)):         
                #Remove the words that only occur once
                editedTitle = re.sub(singleWord, '', title)
                data._set_value(index,'title',editedTitle)                                
            
    return data    


#Drop all the useless crap
def reduceProductInfo(data):
    products = {}
    for index, row in data.iterrows(): 
        products[index] = {
            "index": index,
            "shop" : row["shop"],            
            "modelID" : row["modelID"],
            "title": row["title"],
            "brand": row["Brand"],
            
            }
    return products    

#Turn each word of a title into a hashed value, and return a list of each hashed title
def createHashValues(products):
    for key in products: 
        product = products[key]
        uniqueTitlewords = set()        
        #add all unique title words to a set (whihc also removes the whitespaces and stuff)         
        for word in product["title"].split():
            uniqueTitlewords.add(word)      
        
        #Hash each unqie title word to an integer and add to the list
        hashedTitle = []
        for word in uniqueTitlewords:
            hashValue = binascii.crc32(word.encode('utf-8')) & 0xffffffff
            hashedTitle.append(hashValue)   
        product["hash"] = hashedTitle
        
    return products
          
          
#Get a list of all words that occur in the titles, since we use a set no duplicates will be saved
def getuniqueWordSet(products):
    uniqueTitlewords = set()    
    for key in products: 
        product = products[key]       
        for word in product["title"].split():
            uniqueTitlewords.add(word)   
    return uniqueTitlewords
        
#Use the hashed titles to generate a signature of each title which will be used for comparison    
def createSignatures(products, numberOfHashes):   
    uniqueWords = getuniqueWordSet(products)
    D = len(uniqueWords)         
    listA = createRandomNumberList(numberOfHashes, D)
    listB = createRandomNumberList(numberOfHashes, D)    
    
    for productID in products: 
        product = products[productID]  
        
        signature = []       
        for i in range(0, numberOfHashes):  
            minHashCode = D + 1      
            for wordID in product["hash"]:             
                        
                hashValue = (listA[i]*wordID + listB[i]) % D 
                if hashValue < minHashCode:
                    minHashCode = hashValue                    
            signature.append(minHashCode)
        product["signature"] = signature
    return products


def createRandomNumberList(k, D):   
    randList = []   
    #random.seed(10)
    while k > 0:   
        randIndex = random.randint(0, D) 

        #Keep going untill you found an unique one
        while randIndex in randList:
            randIndex = random.randint(0, D)  
                      
        randList.append(randIndex)
        k = k - 1

    return randList


    
    
#A or b or a matrix of integer with length #OfHashes
def JaccardSim(a, b):
    intersection = len(list(set(a).intersection(b)))
    union = (len(a) + len(b)) - intersection
    if union == 0:
        return 0
    Jsim = float(intersection) / union  
      
    return Jsim


#Got this from: https://stackoverflow.com/questions/22878743/how-to-split-dictionary-into-multiple-dictionaries-fast
from itertools import islice
def chunks(data, SIZE=10000):
    it = iter(data)
    for i in range(0, len(data), SIZE):
        yield {k:data[k] for k in islice(it, SIZE)}
        
def findCandidatePairsHashed(products, b):
    candidatePairs = []   
    
    for productID in products:
        product = products[productID]
        bandedSignature = []
        
        #Divide your signature into bands and hash each band into bandedSignatures
        for subSignature in np.array_split(product["signature"], b):
            my_list = str(subSignature)
            hashValue = binascii.crc32(my_list.encode('utf-8')) & 0xffffffff
            bandedSignature.append(hashValue)            
        product["bandedSignature"] = bandedSignature
         
  
    for i in range(len(products) - 1):
        for j in range(i + 1, len(products)):             
            for k in range(b):
                if products[i]["bandedSignature"][k] == products[j]["bandedSignature"][k]:                    
                    candidatePairs.append([products[i],products[j]] )
                    break 
    return (candidatePairs, products)


def classification(candidatePairs, treshHold):
    candidatePairsUpdated = [] 
    for candidatePair in candidatePairs:
        if (candidatePair[0]["shop"] != candidatePair[1]["shop"]):
            if (isnan(candidatePair[0]["brand"]) or isnan(candidatePair[1]["brand"]) or (candidatePair[0]["brand"] == candidatePair[1]["brand"])):
                sim = JaccardSim(candidatePair[0]["hash"], candidatePair[1]["hash"])
                if  sim >= treshHold:
                    candidatePairsUpdated.append(candidatePair)
    return candidatePairsUpdated                  
                   
               
    

def isnan(value):
    try:
        return math.isnan(float(value))
    except:
        return False
    
def calculateF1(candidatePiars, totalDuplicates):   
    TP, FP = getEstimatedDuplicates(candidatePiars)
    if TP == 0:
        return 0, 0, 0, 0
    FN = (totalDuplicates - TP)
    precision = TP / (TP+FP)
    recall = TP / (TP + FN)
    f1 = 2 * ((precision * recall) / (precision + recall))
    
    return f1, precision, recall, TP
  
def getRealDuplicates(products):
    modelIDs = []
    
    #Append all model ids to a list and use value_count to see how often each modelID occurs
    for productID in products:        
        modelIDs.append(products[productID]["modelID"])
    modelIDs = pd.DataFrame(modelIDs)
    countedModelIDList = modelIDs.value_counts()
    
    #Unfortunatly sometimes the same modelID is used in the same webshop, these are not real duplicates
    #this happens 12 times in total
    AllRealDuplicates = []    
    fakeDuplicates =0
    for modelID, occurence in countedModelIDList.items():        
        if occurence > 1:
            duplicateProducts = []
            for index, product in products.items():
                if product["modelID"] == modelID[0]:
                    duplicateProducts.append(product)  
            
            fakeDuplicateItem = []
            for i in range(len(duplicateProducts) - 1):
                for j in range(i + 1, len(duplicateProducts)):   
                    if(duplicateProducts[i]["shop"] == duplicateProducts[j]["shop"]):
                        fakeDuplicates += 1
                        fakeDuplicateItem.append(duplicateProducts[i])
            if len(fakeDuplicateItem) == 1:
                duplicateProducts.remove(fakeDuplicateItem[0])
            if len(fakeDuplicateItem) == 2:
                duplicateProducts.remove(fakeDuplicateItem[0])
                duplicateProducts.remove(fakeDuplicateItem[1])
            AllRealDuplicates.append(duplicateProducts)
           
    duplicateCount = 0               
    for duplicates in AllRealDuplicates:        
        if len(duplicates) == 2:
            duplicateCount += 1
        elif len(duplicates) == 3:
            duplicateCount += 3
        elif len(duplicates) == 4:
            duplicateCount += 6
    return duplicateCount
            

def getEstimatedDuplicates(candidatePiars):
    truePositive = 0
    falsepositive = 0
    tpPairs = []
    for candidatePair in candidatePiars:
        #Unfortunatly some modelIDs occure twice in the same webshop, so we need to set an extra check so they are not seen as TP
        if (candidatePair[0]["modelID"] == candidatePair[1]["modelID"]):
            if (candidatePair[0]["shop"] != candidatePair[1]["shop"]):
                truePositive += 1
                tpPairs.append(candidatePair)
        else:
            falsepositive += 1
            
    return truePositive, falsepositive


