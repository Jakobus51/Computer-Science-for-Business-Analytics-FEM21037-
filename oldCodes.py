import pandas as pd
import xlsxwriter
import re
from tqdm import tqdm
import numpy as np
import binascii
import random

def getColumnInfo(trainData):
    workbook = xlsxwriter.Workbook('columnInfo.xlsx')
    worksheet = workbook.add_worksheet() 

    column = 0
    for columnName in trainData.columns:
        output = trainData[columnName].value_counts(dropna=False)  
        
        #Set index as a seperate column
        output = output.rename_axis('trait').reset_index()
        
        row = 0
        #Write the columnname to the excel
        worksheet.write(row, column, columnName)
        
        #Some indexing magic so everything end at the correct spot
        for i in range(0,len(output)):
            row += 1
            worksheet.write(row, column, str(output.loc[i][0]))
            worksheet.write(row, column+1, output.loc[i][1])
        column += 2
        
    workbook.close()

# def createBinaryMatrix(data):
#     #Store in a set so only unique values are stored
#     uniqueTitlewords = set()
#     for title in data["title"]:        
#         for word in title.split():
#             uniqueTitlewords.add(word)
#     uniqueTitlewords = (list(uniqueTitlewords)) 
     
    
#     binaryMatrix = np.zeros((len(data), len(uniqueTitlewords))) 
#     for j, word in enumerate(uniqueTitlewords):  
#         for i, title in enumerate(data["title"]):                    
#             if bool(re.search(r"\b{}\b".format(word), title)):         
#                 binaryMatrix[i,j] = 1
                
#     return(binaryMatrix, uniqueTitlewords)


# def createSignatureMatrix(binaryMatrix : np.matrix, uniqueTitlewords):
#     signature_matrix = np.full((binaryMatrix.shape), np.inf) 
    
#     print("Creating signature matrix")
#     for i, row in tqdm(enumerate(binaryMatrix)):
#         hashFunctions = createHashFunctions(uniqueTitlewords)
#         for j, cell in enumerate(row):
#             if cell == 1:                    
#                 for i in range(len(hashFunctions)):
#                     if(hashFunctions[i] <signature_matrix[i][j]):
#                         signature_matrix[i][j] =hashFunctions[i]
#     print(signature_matrix)
#     return signature_matrix
        
#Count how manu duplicates there are
def countRealDuplicates(data: pd.DataFrame):    
    duplicateValuesAll = data['modelID'].value_counts(dropna=False)
   
    duplicates = 0
    for duplicatevalue in duplicateValuesAll:
        if duplicatevalue == 2:
            duplicates += 1
        elif duplicatevalue == 3:
            duplicates += 3
        elif duplicatevalue == 4:
            duplicates += 6
    print(duplicates)
    
    

def createHashFunctions(uniqueTitlewords):      
    hashFunctionsRow = []
    D = len(uniqueTitlewords)
    for i in range(D):
        a= np.random.randint(0, D -1)
        np.random.seed(a)
        b= np.random.randint(0, D -1)        
        hashValue = (a*i + b) % 1031      #Use a prime that is bigger than your number of rows
        hashFunctionsRow.append(hashValue)
    return hashFunctionsRow
     
     
# def createCandidatePairs(products, b ,r, Split ):
#     candidatePairs = []   
    
#     treshhold = (1/b)**(1/r)
#     print("Making candidate pairs")
    
#     if(Split):
#         for band in tqdm(chunks(products, math.ceil(len(products)/b))):        
#             for product1ID in band:
#                 for product2ID in band:
#                     if product2ID > product1ID:                
#                         sim = JaccardSim(band[product1ID]["signature"], band[product2ID]["signature"])
#                         if sim > treshhold:
#                             band[product1ID]["candidatePairs"].append(band[product2ID]["index"])
#                             band[product2ID]["candidatePairs"].append(band[product1ID]["index"])
#                             candidatePairs.append([band[product1ID],band[product2ID]] )
#     else:
#         for product1ID in tqdm(products):
#             for product2ID in products:
#                 if product2ID > product1ID:                
#                     sim = JaccardSim(products[product1ID]["signature"], products[product2ID]["signature"])
#                     if sim > treshhold:
#                         products[product1ID]["candidatePairs"].append(products[product2ID]["index"])
#                         products[product2ID]["candidatePairs"].append(products[product1ID]["index"])
#                         candidatePairs.append([products[product1ID],products[product2ID]] )
#     return products, candidatePairs