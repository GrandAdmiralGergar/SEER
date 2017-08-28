'''
Created on Aug 22, 2017

@author: Gregory
'''

import math
import sqlite3
import databaseFunctions
import copy

beta = 24.0

## Cost function
def C(state):
    sum = 0.0
    for s in state:
        sum += math.exp(s / beta)
    return beta * math.log(sum) # Natural Log

def getTotalPrice(questionId, optionId, count):
    sqlConn = sqlite3.connect(databaseFunctions.DATABASE)
    optionIds, volumes = getMarketState(questionId, sqlConn)
    currentState = dict(zip(optionIds,volumes))
    newState = copy.copy(currentState)
    newState[optionId] += count
    sqlConn.close()
    return C(newState.values()) - C(currentState.values())

def determinePrices(optionIds, volumes):
    sum = 0.0
    prices = {}
    for outcome in volumes:
        sum += math.exp(outcome / beta)

    for i in xrange(0, len(volumes)):
        pricePoint = math.exp(volumes[i] / beta) / sum
        prices[optionIds[i]] = pricePoint
    return prices

def determineClosedPrices(optionIds, answerId):
    prices = {}
    for option in optionIds:
        if option == answerId:
            prices[option] = 1.0
        else:
            prices[option] = 0.0
    return prices

def getPrices(questionId, sqlConn):
    optionIds, volumes = getMarketState(questionId, sqlConn)
    if databaseFunctions.isQuestionClosed(questionId):
        answer = databaseFunctions.findQuestionAnswer(questionId)
        answerId = databaseFunctions.findOptionIdFromOption(answer, sqlConn)
        return determineClosedPrices(optionIds, answerId) 
    else:
        return determinePrices(optionIds, volumes)

def getMarketState(questionId, sqlConn):
    cursor = sqlConn.cursor()
    
    cursor.execute("SELECT id FROM Question_User_Status WHERE Question_id = ?", (questionId,))
    rawResults = cursor.fetchall()
    if rawResults == None:
        return None
    
    ids = []
    for result in rawResults:
        ids.append(result[0])
    
    #SQL injection opportunity, but this is a pain otherwise
    string = "SELECT option_id, SUM(shares) FROM Question_User_Options WHERE Question_User_Status_id IN(" + (", ".join(str(i) for i in ids)) + ") GROUP BY option_id ORDER BY option_id ASC"
    cursor.execute(string)
    rawResults = cursor.fetchall()
    if rawResults == None:
        return None
    
    optionIds = []
    volumes = []
    for result in rawResults:
        optionIds.append(result[0])
        volumes.append(result[1])
    
    return optionIds, volumes
    
#Actual function to enact a transaction after error checking to validate it
#Returns paired list of option ids to new, updated values
def doTrade(questionId, optionId, sharesPurchased):
    sqlConn = sqlite3.connect(databaseFunctions.DATABASE)
    cursor = sqlConn.cursor()
    
    optionIds, volumes =  getMarketState(questionId, sqlConn)
    newState = copy.copy(dict(zip(optionIds,volumes)))
    newState[optionId] += sharesPurchased

    prices = determinePrices(optionIds, newState.values())
    
    sqlConn.close()
    return prices
