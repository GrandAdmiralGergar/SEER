'''
Created on Aug 13, 2017

@author: Gregory
'''

import sqlite3
from flask import request
from flask import Flask
import market

import numpy
from random import randint
import os.path
from datetime import datetime
app = Flask(__name__)

DATABASE = "SEER.db"

def getFooter(username):
    response = ""
    response += """
    <div data-role="footer" style="text-align:center">"""
    
    if username != None:
        response += "Currently logged in as " + username
    
    response += """
       <div data-role="navbar">
       <ul>
           <li> <a href="#" data-rel="back" data-icon="back">Back</a>
           <li> <a href="" data-icon="search">Search </a>
           <li> <a href="home" data-icon="home">Home</a>
           <li> <a href="logout" data-icon="delete">Logout</a>
       </ul>
       </div>
       <h4>CS530 Developing User Interfaces 2017</h4>
    </div>"""
    
    return response

def findUserIdFromUsername(username, sqlConn):
    cursor = sqlConn.cursor()
    cursor.execute("SELECT id FROM User WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result != None:
        id = result[0]
        return id
        if id == None:
            #Do some error
            pass
    return None

def findUserFromUserId(userId, sqlConn):
    cursor = sqlConn.cursor()
    cursor.execute("SELECT username FROM User WHERE id = ?", (userId,))
    result = cursor.fetchone()
    if result != None:
        name = result[0]
        if name == None:
            #Do some error
            pass
        return name
    return None
    
def findOptionFromOptionId(optionId, sqlConn):
    cursor = sqlConn.cursor()
    cursor.execute("SELECT option FROM Option WHERE id = ?", (optionId,))
    result = cursor.fetchone()
    if result != None:
        name = result[0]
        if name == None:
            #Do some error
            pass
        return name
    return None

def findOptionIdFromOption(option, sqlConn):
    cursor = sqlConn.cursor()
    cursor.execute("SELECT id FROM Option WHERE option = ?", (option,))
    result = cursor.fetchone()
    if result != None:
        oid = result[0]
        if oid == None:
            #Do some error
            pass
        return oid
    return None
    
def findGroupIdFromUsername(group, sqlConn):
    cursor = sqlConn.cursor()
    cursor.execute("SELECT id FROM \"Group\" WHERE Name = ?", (group,))

    result = cursor.fetchone()
    if result != None:
        id = result[0]
        if id == None:
            #Do some error
            pass
        return id
    return None

def findGroupFromGroupId(groupId, sqlConn):
    cursor = sqlConn.cursor()
    cursor.execute("SELECT Name FROM \"Group\" WHERE id = ?", (groupId,))
    result = cursor.fetchone()
    if result != None:
        name = result[0]
        if name == None:
            #Do some error
            pass
        return name
    return None

def isUserInGroup(usernameId, groupId):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    inGroup = False

    cursor.execute("SELECT COUNT(*) FROM Group_Membership WHERE User_ID = ? AND Group_ID = ?", (usernameId, groupId,))
    result = cursor.fetchone()
    if result != None and result[0] != None:
        count = int(result[0])
        inGroup = (count > 0)
    sqlConn.close()
    return inGroup

def findQuestionsAvailableToUser(userId, sqlConn):
    groups = findGroupsContainingUser(userId)
    
    cursor = sqlConn.cursor()
    cursor.execute("SELECT DISTINCT Question_ID FROM Question_Group_Membership WHERE Group_ID IN(" + (", ".join(str(i) for i in groups)) + ")")
    rawResults = cursor.fetchall()
    qids = []
    if rawResults != None:
        for result in rawResults:
            qids.append(result[0])
    return qids

def findQuestionsAvailableToGroup(groupId, sqlConn):
    cursor = sqlConn.cursor()
    cursor.execute("SELECT DISTINCT Question_ID FROM Question_Group_Membership WHERE Group_ID = ?", (groupId,))
    rawResults = cursor.fetchall()
    qids = []
    if rawResults != None:
        for result in rawResults:
            qids.append(result[0])
    return qids

def addUserToMarket(uid, qid):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()

    #Default value is used for the currency so this creates correct values
    cursor.execute("INSERT INTO Question_User_Status(Question_ID, User_ID) VALUES(?,?)", (qid,uid,))
    cursor.execute("SELECT MAX(id) FROM Question_User_Status")
    qusId = cursor.fetchone()[0]
    
    cursor.execute("SELECT id FROM Option WHERE Question_ID = ?", (qid,))
    optionIds = cursor.fetchall()
    for optionHat in optionIds:
        if optionHat[0] != None:
            cursor.execute("INSERT INTO Question_User_Options(Question_User_Status_id, option_id, shares) VALUES(?,?,0)", (qusId, optionHat[0],))
    
    sqlConn.commit()
    sqlConn.close()
            
def userCurrencyForQuestion(username, qid):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    uid = findUserIdFromUsername(username, sqlConn)
    ret = None
    if uid != None:
        cursor.execute("SELECT currency FROM Question_User_Status WHERE User_ID = ? AND Question_ID = ?", (uid, qid,))
        value = cursor.fetchone()
        if value != None:
            ret = value[0]
        else:
            addUserToMarket(uid, qid)
            return userCurrencyForQuestion(username, qid)        
    sqlConn.close()
    return ret

def userPortfolioForQuestion(username, qid):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    uid = findUserIdFromUsername(username, sqlConn)
    portfolio = None
    if uid != None:
        cursor.execute("SELECT id FROM Question_User_Status WHERE User_ID = ? AND Question_ID = ?", (uid, qid,))
        value = cursor.fetchone()
        if value != None:
            qusId = value[0]
            cursor.execute("SELECT option_id, shares FROM Question_User_Options WHERE Question_User_Status_Id = ?", (qusId,))
            rawResults = cursor.fetchall()
            
            portfolio = {}
            if rawResults != None:
                for result in rawResults:
                    portfolio[result[0]] = result[1]
        else:
            addUserToMarket(uid, qid)
            sqlConn.close()
            return userPortfolioForQuestion(username, qid)
    sqlConn.close()
    return portfolio

def userSharesForQuestionAndOption(username, qid, oid):
    return userPortfolioForQuestion(username, qid)[oid]

def updateUserSharesAndCurrencyForQuestionAndOption(username, qid, oid, shares, currencyChange):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    
    uid = findUserIdFromUsername(username, sqlConn)
    ret = None
    if uid != None:
        cursor.execute("SELECT id, currency FROM Question_User_Status WHERE User_ID = ? AND Question_ID = ?", (uid, qid,))
        value = cursor.fetchone()
        if value != None:
            qusId = value[0]
            currentCurrency = value[1]
            cursor.execute("SELECT shares FROM Question_User_Options WHERE Question_User_Status_Id = ? AND option_id = ?", (qusId,oid,))
            currentShares = cursor.fetchone()
            if currentShares != None:
                currentShares = currentShares[0]
                cursor.execute("UPDATE Question_User_Options SET shares = ? WHERE Question_User_Status_Id = ? AND option_Id = ?", (currentShares + shares, qusId, oid,))
                cursor.execute("UPDATE Question_User_Status SET currency = ? WHERE id = ?", (currentCurrency + currencyChange,qusId,))
                sqlConn.commit()
    sqlConn.close()
    return

def userNetValueForQuestion(username, qid):
    cash = userCurrencyForQuestion(username, qid)
    shares = userPortfolioForQuestion(username, qid)
        
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    prices = market.getPrices(qid, sqlConn)
    
    total = 0
    for option in shares.keys():
        total += prices[option] * shares[option]

    total += cash
    sqlConn.close()
    return total

def findQuestionTitleFromId(questionId):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    cursor.execute("SELECT Question FROM Question WHERE id = ?", (questionId,))
    questionTitle = cursor.fetchone()
    ret = None
    if questionTitle != None:
        ret = questionTitle[0]
    sqlConn.close()
    return ret

def isQuestionClosed(questionId):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    cursor.execute("SELECT Answer FROM Question WHERE id = ?", (questionId,))
    result = cursor.fetchone()
    sqlConn.close()
    
    return result[0] != None

def findQuestionAsker(questionId):    
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    cursor.execute("SELECT Asker_ID FROM Question WHERE id = ?", (questionId,))
    rawResults = cursor.fetchone()
    askerName = ""
    if rawResults != None:
        askerId = rawResults[0]
        askerName = findUserFromUserId(askerId, sqlConn)
    sqlConn.close()
    return askerName

def findQuestionAnswer(questionId):    
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    cursor.execute("SELECT Answer FROM Question WHERE id = ?", (questionId,))
    rawResults = cursor.fetchone()
    optionName = ""
    if rawResults != None:
        optionId = rawResults[0]
        optionName = findOptionFromOptionId(optionId, sqlConn)
    sqlConn.close()
    return optionName

def findUsersInGroup(groupName):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    gid = findGroupIdFromUsername(groupName, sqlConn)
    userNames = []
    if gid != None:
        cursor.execute("SELECT User_ID FROM Group_Membership WHERE Group_ID = ?", (gid,))
        users = cursor.fetchall()
        for user in users:
            userId = user[0]
            userNames.append(findUserFromUserId(userId, sqlConn))
    sqlConn.close()
    return userNames


def findGroupsContainingUser(userId):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    groupNames = []
    if userId != None:
        cursor.execute("SELECT Group_ID FROM Group_Membership WHERE User_ID = ?", (userId,))
        groups = cursor.fetchall()
        for group in groups:
            groupId = group[0]
            groupNames.append([groupId,findGroupFromGroupId(groupId, sqlConn)])
    sqlConn.close()
    return dict(groupNames)

def optionTableRow(option):
    return ""

class Option:
    def __init__(self):
        self.id = 0
        self.qid = 0
        self.text = ""
        self.value = 0
        self.volume = 0


def buildShowUserList(userId):
    sqlConn = sqlite3.connect(DATABASE)
    groupNames = findGroupsContainingUser(userId)
    response = """"""
    for id in groupNames.keys():
        response += """<a href="group?groupId=""" + str(id) + """" data-role="button" data-theme="a">""" + str(groupNames[id]) + """</a>"""
    sqlConn.close()
    return response

def getQuestionButtons(questionIds, sqlConn):
    cursor = sqlConn.cursor()
    questionLinks = []
    for qid in questionIds:
        cursor.execute("SELECT Question, Asker_ID, Start_Time, Closed_Time FROM Question WHERE id = ?", (qid,))
        [questionText, askerId, startTime, closedTime] = cursor.fetchone()
        asker = findUserFromUserId(askerId, sqlConn)
        question = """<a href="question?questionId=QID" data-role="button" data-icon="arrow-r" data-iconpos="right">QUESTION_TITLE (asked by ASKER)</a>"""
        question = question.replace("QID", str(qid))
        question = question.replace("QUESTION_TITLE", questionText)
        question = question.replace("ASKER", asker)
        questionLinks.append(question)
    return questionLinks

def getGroupButtons(groupIds, sqlConn):
    cursor = sqlConn.cursor()
    groupLinks = []
    for gid in groupIds:
        groupName = findGroupFromGroupId(gid, sqlConn)
        groupLink = """<a href="group?groupId=GID" data-role="button" data-inline="true" data-icon="arrow-r" data-iconpos="right">GROUP_NAME</a>"""
        groupLink = groupLink.replace("GID", str(gid))
        groupLink = groupLink.replace("GROUP_NAME", groupName)
        groupLinks.append(groupLink)
    return groupLinks

def buildHomeQuestionLinks(userId):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    qids = findQuestionsAvailableToUser(userId, sqlConn)
    
    questionLinks = getQuestionButtons(qids, sqlConn)
    sqlConn.close()
    return "<br>".join(questionLinks)

def buildHomeGroupLinks(userId):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    groups = findGroupsContainingUser(userId)
    groupLinks = getGroupButtons(groups, sqlConn)
    sqlConn.close()
    return " ".join(groupLinks)
    
def buildShowGroupTable(groupId):
    sqlConn = sqlite3.connect(DATABASE)
    groupName = findGroupFromGroupId(groupId, sqlConn)
    usernames = findUsersInGroup(groupName)
    questionIds = findQuestionsAvailableToGroup(groupId,sqlConn)
        
    questionLinks = getQuestionButtons(questionIds, sqlConn)
    
    response = """<table data-role="table" id="question-table" data-mode="reflow" class="ui-responsive">\n"""
    response += """<thead>
        <tr>
          <th data-priority="1">Members</th>
          <th data-priority="2">Questions</th>
        </tr>
    </thead>
    <tbody>"""
    
    for i in range(0, max(len(usernames), len(questionLinks))):
        uid = findUserIdFromUsername(usernames[i], sqlConn)
        
        response += """<tr>"""
        if i < len(usernames):
            response += """<th><a href="user?userId=""" + str(uid) + """" data-role="button" data-theme="a">""" + str(usernames[i]) + """</a></th>"""
        else:
            response += """<th></th>"""
        if i < len(questionLinks):
            response += """<th>""" + questionLinks[i] + """</th>"""
        else:
            response += """<th></th>"""
        response += """</tr>"""
    
    response += "</tbody></table>"
    sqlConn.close()
    return response

def buildGroupMembershipOptions(uid, groupId):
    sqlConn = sqlite3.connect(DATABASE)
    inGroup = isUserInGroup(uid, groupId)
    response = ""
    if inGroup:
        response += """<button onclick="leave_group(""" + str(uid) + ", " + str(groupId) + """)">Leave Group</button>"""
    else:
        response += """<button onclick="join_group(""" + str(uid) + ", " + str(groupId) + """)">Join Group</button>"""
    return response

def buildCreateQuestionCheckboxes(username):
    sqlConn = sqlite3.connect(DATABASE)
    userId = findUserIdFromUsername(username, sqlConn)
    if userId == None:
        sqlConn.close()
        return ""
    
    groupNames = findGroupsContainingUser(userId)
    response = ""
    for id in groupNames.keys():
        response += """
        <input type="checkbox" name="checkbox-group[]" id="checkbox-group""" + str(id) + """">
        <label for="checkbox-group""" + str(id) + """">""" +str(groupNames[id]) + """</label>"""
    return response

def buildQuestionCloser(questionId):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    cursor.execute("SELECT Question, Asker_ID, Start_Time, CLosed_Time, Answer FROM Question WHERE id = ?", (questionId,))
    [questionTitle, askerId, startTime, closedTime, answer] = cursor.fetchone()
    
    cursor.execute("SELECT id, Question_ID, option FROM Option WHERE Question_ID = ? ORDER BY id ASC", (questionId,))
    options = []
    queryResults = cursor.fetchone()
    while queryResults != None:
        option = Option()
        [option.id, option.qid, option.text] = queryResults
        options.append(option)
        queryResults = cursor.fetchone()
    
    response = """<a href="#closeQuestionPopup" data-role="button" data-rel="popup" data-transition="pop" >Close Question</a>
        <div class="ui-popup-container pop ui-popup-hidden ui-popup-truncate" id="popupClose-popup">
            <div data-role="popup" id="closeQuestionPopup" data-theme="a" class="ui-corner-all ui-popup ui-body-a ui-overlay-shadow">
                <div style="padding:15px 25px; text-align:center;" class="ui-body-a ui-corner-all">
            Select the correct response to close the question
        """
        
    for option in options:
        response += """<a href="closeQuestion?questionId=""" + str(questionId) + """&optionId=""" + str(option.id) + """" data-role="button" data-theme="a" >""" + str(option.text) +  """</a>"""
        
    response +=  """</div>  </div> </div>"""
    return response

def buildQuestionTable(questionId, username):
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    cursor.execute("SELECT Question, Asker_ID, Start_Time, CLosed_Time, Answer FROM Question WHERE id = ?", (questionId,))
    [questionTitle, askerId, startTime, closedTime, answer] = cursor.fetchone()
    
    isClosed = isQuestionClosed(questionId)
    
    cursor.execute("SELECT id, Question_ID, option FROM Option WHERE Question_ID = ? ORDER BY id ASC", (questionId,))
    options = []
    queryResults = cursor.fetchone()
    while queryResults != None:
        option = Option()
        [option.id, option.qid, option.text] = queryResults
        options.append(option)
        
        #Get next option
        queryResults = cursor.fetchone()
    
    for option in options:
        cursor.execute("SELECT SUM(shares) FROM Question_User_Options WHERE option_id = ?", (option.id,))
        queryResult = cursor.fetchone()
        if queryResult != None and queryResult[0] != None:
            option.volume = queryResult[0]
    
    prices = market.getPrices(questionId, sqlConn)
    
    for option in options:
        option.value = prices[option.id]
    
    portfolio = userPortfolioForQuestion(username, questionId)
    sqlConn.close()
    
    divs = ""
    response = """<table data-role="table" id="question-table" data-mode="reflow" class="ui-responsive">\n"""
    response += """<thead>
        <tr>
          <th data-priority="1">Options</th>
          <th data-priority="2">Value</th>
          <th data-priority="3">Volume</th>
          <th data-priority="4">Owned</th>
          <th data-priority="4"></th>
          <th data-priority="4"></th>
        </tr>
    </thead>
    <tbody>"""
    
    for option in options:
        response += """<tr>
          <th>""" + option.text + """</th>
          <td>""" + '{0:.4f}'.format(option.value) + """</td>
          <td>""" + str(option.volume) + """</td>
          <td>""" + str(portfolio[option.id]) + """</td>
          <td><a href="#buyShares""" + str(option.id) + """" data-rel="popup" data-transition="pop" class="ui-btn ui-alt-icon ui-nodisc-icon """ + ("ui-disabled" if isClosed else "") + """" aria-haspopup="true" aria-expanded="false" >Buy</a></td>
          <td><a href="#sellShares""" + str(option.id) + """"  data-rel="popup" data-transition="pop" class="ui-btn ui-alt-icon ui-nodisc-icon """ + ("ui-disabled" if isClosed else "") + """" aria-haspopup="true" aria-expanded="false">Sell</a></td>
        </tr>"""
        
        divs += """    
            <div class="ui-popup-container pop ui-popup-hidden ui-popup-truncate" id="popupBuy-popup">
                <div data-role="popup" id="buyShares""" + str(option.id) + """" data-theme="a" class="ui-corner-all ui-popup ui-body-a ui-overlay-shadow">
                    <form>
                        <div style="padding:15px 25px; text-align:center;" class="ui-body-a ui-corner-all">
                            <p>Purchase how many of this option?</p>
                            <label for="spin" class="ui-hidden-accessible">Quantity</label> 
                            <input type="text" data-role="spinbox" name="spin" id="spin" value="1" min="0" max="100" />
                           <!--  <p id="buyCost">0</p> -->
                            <button type="button" data-theme="b" class="ui-btn ui-btn-b ui-shadow ui-corner-all" data-mini="false" onclick="buy_click(this.id,spin.value)" name="buy" id="buy""" + str(option.id)+"""">Purchase</button>
                            <a href="#" data-rel="back" data-role="button" data-theme="a" data-icon="delete" data-iconpos="notext" class="ui-btn-right">Close</a>
                        </div>
                    </form>
                </div>
            </div>    
            <div class="ui-popup-container pop ui-popup-hidden ui-popup-truncate" id="popupSell-popup">
                <div data-role="popup" id="sellShares""" + str(option.id) + """" data-theme="a" class="ui-corner-all ui-popup ui-body-a ui-overlay-shadow">
                    <form>
                        <div style="padding:15px 25px; text-align:center;" class="ui-body-a ui-corner-all">
                            <p>Sell how many of this option?</p>
                            <label for="spin" class="ui-hidden-accessible">Quantity</label> 
                            <input type="text" data-role="spinbox" name="spin" id="spin" value="1" min="0" max="100" />
                            <!-- <p id="sellCost">0</p> -->
                            <button type="button" data-theme="b" class="ui-btn ui-btn-b ui-shadow ui-corner-all" data-mini="false" onclick="sell_click(this.id,spin.value)" name="sell" id="sell""" + str(option.id)+"""">Sell</button>
                            <a href="#" data-rel="back" data-role="button" data-theme="a" data-icon="delete" data-iconpos="notext" class="ui-btn-right">Close</a>
                        </div>
                    </form>
                </div>
            </div>"""
    
    response += """</tbody></table>"""
    response += divs
    
    return response
