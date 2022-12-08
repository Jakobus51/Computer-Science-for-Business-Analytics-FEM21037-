import pandas as pd
from sklearn.model_selection import train_test_split
import classes
import numpy as np
import math
import time

results = []
tik = time.time()
for bootstrap in range(5):
    tiktik = time.time()
    df = pd.read_excel('data_excel.xlsx')
    (trainData, testData) = train_test_split(df, test_size=(1-0.63))
   
    possiblePairs = len(testData) * (len(testData) -1) * 0.5
    
    testData = classes.standardizeTitles(testData)
    testData = classes.removeSingleOccurenceWords(testData)
    products = classes.reduceProductInfo(testData)    
    products = classes.createHashValues(products)
    totalDuplicates = classes.getRealDuplicates(products)  

    #rArray = [50, 100]    
    #numberOfHashes = round(len(classes.getuniqueWordSet(products)) / 2)
    
    #Number of hashes set to 200, so each bootstrap has the same rArray
    numberOfHashes = 200

    rArray = [round(numberOfHashes/ 1),
              round(numberOfHashes/ 2),
              round(numberOfHashes/ 3),
              round(numberOfHashes/ 4),
              round(numberOfHashes/ 5),
              round(numberOfHashes/ 6),
              round(numberOfHashes/ 7),
              round(numberOfHashes/ 8),
              round(numberOfHashes/ 9),
              round(numberOfHashes/ 10),
              round(numberOfHashes/ 12),
              round(numberOfHashes/ (numberOfHashes/14)),
              round(numberOfHashes/ (numberOfHashes/12)),
              round(numberOfHashes/ (numberOfHashes/10)),
              round(numberOfHashes/ (numberOfHashes/9)),
              round(numberOfHashes/ (numberOfHashes/8)),
              round(numberOfHashes/ (numberOfHashes/7)),
              round(numberOfHashes/ (numberOfHashes/6)),
              round(numberOfHashes/ (numberOfHashes/5)),
              round(numberOfHashes/ (numberOfHashes/4)),
              round(numberOfHashes/ (numberOfHashes/3)),
              round(numberOfHashes/ (numberOfHashes/2)),
              round(numberOfHashes/ numberOfHashes)]
    treshHolds = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    iteration = 0
    for r in rArray:
        
        b= math.ceil(numberOfHashes/ r)        
       
        print("starting round {} with r={} and b={}".format(bootstrap, r, b))     
       
        products = classes.createSignatures(products, numberOfHashes)
        candidatePairs, products = classes.findCandidatePairsHashed(products, b)      
        FoCstar = len(candidatePairs)/ possiblePairs
        
        f1Star, precisionStar, recallStar, TP = classes.calculateF1(candidatePairs, totalDuplicates)
        #print("f1*={0:.3f}, precision*={1:.3f}, recall*={2:.3f}, TP*={3}".format(f1Star, precisionStar, recallStar, TP))
        
        bestf1 = 0
        for treshHold in treshHolds:        
            candidatePairsUpdated = classes.classification(candidatePairs, treshHold)    
            f1, precision, recall, TP = classes.calculateF1(candidatePairsUpdated, totalDuplicates)
            if f1 > bestf1:
                bestTreshHold = treshHold
                bestf1 = f1
                bestTP = TP
                bestPrecision = precision
                bestRecall = recall
                FoC = len(candidatePairsUpdated)/ possiblePairs

                
                
        #print("f1={0:.3f}, precision={1:.3f}, recall={2:.3f}, TP={3}, TreshHold={4}".format(bestf1, bestPrecision, bestRecall, bestTP, bestTreshHold))
        
        results.append({"iteration": iteration,
                        "t": (1/b)**(1/r),
                        "r": r,
                        "b": b,
                        "numberOfHashes": numberOfHashes,
                        "FoC": FoC,
                        "f1*": np.round(f1Star, 3),
                        "precision*": np.round(precisionStar, 3),
                        "recall*": np.round(recallStar, 3),
                        "Foc": FoC,
                        "f1": np.round(bestf1, 3),
                        "treshHold" : bestTreshHold,
                        "precision": np.round(bestPrecision, 3),
                        "recall": np.round(bestRecall, 3),
                        "bootstrap": bootstrap 
                        })     
        iteration += 1
    print("time one bootstrap {0:.0f} seconds".format(time.time() - tiktik))
        
print("Total time  {0:.0f} seconds".format(time.time() - tik))
resultsdf = pd.DataFrame(results)
resultsdf.to_csv('BootstrappedResults.csv', index=False, header=True)
averagedf = resultsdf.groupby('iteration').mean()
averagedf.to_csv('AveragedBootstrappedResults.csv', index=False, header=True)