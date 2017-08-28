from flask import Flask, send_file, session, redirect, url_for, escape, request

import traceback
from databaseFunctions import *
import json
import market
from market import getPrices
app = Flask(__name__)

app.secret_key = 'A0ZRi8bjs38683XHH!jmN]LWX/,?RT'

@app.route('/')
@app.route('/index.html')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/login')
def login():
    with file("static/login.html") as f:
        contents = f.read()
        loginJsUrl = url_for('static', filename='login.js')
        registerJsUrl = url_for('static', filename='register_new_user.js')
        contents = contents.replace('login.js', loginJsUrl)
        contents = contents.replace('register_new_user.js', registerJsUrl)
    return contents

@app.route('/loginAttempt', methods=['POST'])
def loginAttempt():
    username = request.form['username1']
    sqlConn = sqlite3.connect(DATABASE)
    uid = findUserIdFromUsername(username,sqlConn)
    sqlConn.close()
    if uid != None:
        session['username'] = username
        return "SUCCESS"
    else:
        return "Invalid credentials"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return login()

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    sqlConn = sqlite3.connect(DATABASE)
    uid = findUserIdFromUsername(username, sqlConn)
    with file("static/home.html") as f:
        contents = f.read()
        contents = contents.replace('USERNAME', session['username'])
        contents = contents.replace('QUESTIONS', buildHomeQuestionLinks(uid))
        contents = contents.replace('GROUPS', buildHomeGroupLinks(uid))
        contents = contents.replace('FOOTER', getFooter(session['username']))
    return contents

@app.route('/createUser', methods=['POST'])
def createUser():
    username = request.form['username1']
    password = request.form['password1']
    email = request.form['email1']
    success = False
    try:
        sqlConn = sqlite3.connect(DATABASE)
        cursor = sqlConn.cursor()
        
        cursor.execute("INSERT INTO User(username,email,password) VALUES(?,?,?)", (username, email, password,))
        uid = findUserIdFromUsername(username, sqlConn)
        cursor.execute("INSERT INTO Group_Membership(Group_ID, User_ID) VALUES(?,?)", (1,uid,))
        sqlConn.commit()
        session['username'] = username
        success = True
    except:
        success = False
    finally:
        sqlConn.close()
    return str(success)

@app.route('/createGroup')
def createGroup():
    if 'username' not in session:
        return redirect(url_for('login'))
    with file("static/createGroup.html") as f:
        contents = f.read()
        groupJsUrl = url_for('static', filename='createGroup.js')
        contents = contents.replace('CREATE_GROUP_JS', groupJsUrl)
        contents = contents.replace('FOOTER', getFooter(session['username']))
    return contents
    

@app.route('/createGroupDB', methods=['POST'])
def createGroupDB():
    username = session['username']
    groupName = request.form['groupName']
    groupDescription = request.form['groupDescription']
    ret = ""
    sqlConn = sqlite3.connect(DATABASE)
    uid = findUserIdFromUsername(username, sqlConn)
    cursor = sqlConn.cursor()
    try:
        cursor.execute("INSERT INTO \"Group\"(Creator, Name, Description) VALUES(?,?,?)", (uid, groupName,groupDescription,))
        cursor.execute("SELECT MAX(id) FROM \"Group\"")
        gid = cursor.fetchone()
        if gid != None:
            ret = gid[0]
            cursor.execute("INSERT INTO Group_Membership(Group_ID, User_ID) VALUES(?,?)", (ret, uid,))
            sqlConn.commit()
    except:
        ret = "FAILURE"
    finally:
        sqlConn.close()
        
    return str(ret)

@app.route('/group')
def showGroup():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    groupId = request.args.get('groupId')
    
    sqlConn = sqlite3.connect(DATABASE)
    uid = findUserIdFromUsername(username, sqlConn)
    groupName = findGroupFromGroupId(groupId, sqlConn)
    groupDescription = ""
    cursor = sqlConn.cursor()
    cursor.execute("SELECT Description FROM \"Group\" WHERE id = ?", (groupId,))
    rawResult = cursor.fetchone()
    if rawResult != None:
        groupDescription = str(rawResult[0])
        
    with file("static/showGroup.html") as f:
        contents = f.read()
        groupMembershipJs = url_for('static', filename='groupMembership.js')
        contents = contents.replace('GROUP_SCRIPT', groupMembershipJs)
        contents = contents.replace('GROUP_NAME', groupName)
        contents = contents.replace('GROUP_DESCRIPTION', groupDescription)
        contents = contents.replace('TABLE', buildShowGroupTable(groupId))
        contents = contents.replace('MEMBERSHIP_OPTIONS', buildGroupMembershipOptions(uid, groupId))
        contents = contents.replace('FOOTER', getFooter(session['username']))
    return contents

@app.route('/joinGroup', methods=['POST'])
def joinGroup():
    username = session['username']
    uid = request.form['userId']
    gid = request.form['groupId']
    
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    cursor.execute("INSERT INTO Group_Membership(Group_Id, User_Id) VALUES(?,?) ", (gid, uid,))
    sqlConn.commit()
    sqlConn.close()
    return "SUCCESS"

@app.route('/leaveGroup', methods=['POST'])
def leaveGroup():
    username = session['username']
    uid = request.form['userId']
    gid = request.form['groupId']
    
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    cursor.execute("DELETE FROM Group_Membership WHERE Group_Id = ? AND User_Id = ?", (gid, uid,))
    sqlConn.commit()
    sqlConn.close()
    return "SUCCESS"
    

@app.route('/user')
def showUser():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    uid = int(request.args.get('userId'))
    
    sqlConn = sqlite3.connect(DATABASE)
    ownUserId = findUserIdFromUsername(username, sqlConn)
     
    if uid == ownUserId:
        sqlConn.close()
        return redirect(url_for('home'))
    
    pageUserName = findUserFromUserId(uid, sqlConn)
    
    with file("static/showUser.html") as f:
        contents = f.read()
        contents = contents.replace('USER_NAME', pageUserName)
        contents = contents.replace('LIST', buildShowUserList(uid))
        contents = contents.replace('FOOTER', getFooter(session['username']))
    return contents

@app.route('/addUserToGroup')
def addUserToGroup():
    username = request.args.get('username')
    groupname = request.args.get('groupname')
    
    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    cursor.execute("INSERT INTO Group_Membership(Name) VALUES(?)", (groupname,))
    sqlConn.commit()
    sqlConn.close()
    return "SUCCESS"
    

@app.route('/createQuestion')
def createQuestionPage():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    
    with file("static/createQuestion.html") as f:
        contents = f.read()
        jsUrl = url_for('static', filename='createQuestion.js')
        contents = contents.replace('CREATE_QUESTION_JS', jsUrl)
        contents = contents.replace('GROUP_BOXES', buildCreateQuestionCheckboxes(username))
        contents = contents.replace('FOOTER', getFooter(session['username']))
    return contents

@app.route('/createQuestionDB', methods=['POST'])
def createQuestion():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    ret = "FAILURE"
    
    username = session['username']
    questionTitle = request.form['question']
    jsonArray = request.form['options']
    jsonGroupArray = request.form['groupIds']

    options = json.loads(jsonArray)
    groupIds = json.loads(jsonGroupArray)
    
    try:
        sqlConn = sqlite3.connect(DATABASE)
        cursor = sqlConn.cursor()
        id = findUserIdFromUsername(username, sqlConn)
        initialValue = 1.0 / len(options)
        if id != None:
            cursor.execute("INSERT INTO Question(Question, Asker_ID, Start_Time) VALUES(?,?,DateTime('now'))", (questionTitle, id,))
            cursor.execute("SELECT MAX(id) FROM Question")
            qid = cursor.fetchone()[0]
            ret = qid #The return value is the qid so that the page can redirect appropriately
            for option in options:
                cursor.execute("INSERT INTO Option(Question_ID, option) VALUES(?,?)", (qid,option,))
            for groupId in groupIds:
                cursor.execute("INSERT INTO Question_Group_Membership(Question_ID, Group_ID) VALUES(?,?)", (qid, groupId,))
        sqlConn.commit()
    except:
        ret = "FAILURE"
    finally:
        sqlConn.close()
    
    return str(ret)

@app.route('/question')
def questionPage():
    if 'username' not in session:
        return redirect(url_for('login'))
    sqlConn = sqlite3.connect(DATABASE)
    questionId = request.args.get('questionId')
    username = session['username']
    isClosed = isQuestionClosed(questionId)
    qids = findQuestionsAvailableToUser(findUserIdFromUsername(username, sqlConn), sqlConn)
    
    userHasAccess = False
    if int(questionId) in qids:
        userHasAccess = True
    
    if userHasAccess == False:
        return redirect(url_for('home'))
    
    with file("static/question.html") as f:
        contents = f.read()
        asker = findQuestionAsker(questionId)
        contents = contents.replace('ASKER', asker)
        if not isClosed:
            contents = contents.replace('HEADLINE', "You have USER_CURRENCY available, and a total worth of USER_WORTH on this market")
            contents = contents.replace('USER_CURRENCY', '{0:.2f}'.format(userCurrencyForQuestion(username, questionId)))
            contents = contents.replace('USER_WORTH', '{0:.2f}'.format(userNetValueForQuestion(username, questionId)))
        else:
            contents = contents.replace('HEADLINE', "Answer: ANSWER_OPTION<br>This market is closed - you ended up with a total value of USER_WORTH")
            contents = contents.replace('ANSWER_OPTION', findQuestionAnswer(questionId))
            contents = contents.replace('USER_WORTH', '{0:.2f}'.format(userNetValueForQuestion(username, questionId)))
            
        contents = contents.replace('TRANSACTION_JAVASCRIPT',  url_for('static', filename='transaction.js'))
        contents = contents.replace('QUESTION_TITLE', findQuestionTitleFromId(questionId))
        contents = contents.replace('QUESTION_TABLE', buildQuestionTable(questionId, username))
        contents = contents.replace('FOOTER', getFooter(session['username']))
        if asker == username and not isClosed:
            contents = contents.replace('CLOSER', buildQuestionCloser(questionId))
        else:
            contents = contents.replace('CLOSER', "")
    return contents

@app.route('/closeQuestion')
def closeQuestion():
    if 'username' not in session:
        return redirect(url_for('login'))
    questionId = request.args.get('questionId')
    optionId = request.args.get('optionId')
    username = session['username']
    askerName = findQuestionAsker(questionId)
    if username != askerName:
        return redirect(url_for('question?questionId=' + str(questionId)))

    sqlConn = sqlite3.connect(DATABASE)
    cursor = sqlConn.cursor()
    cursor.execute("UPDATE Question SET Closed_Time=DateTime('now'), Answer=? WHERE id=?",(optionId,questionId,))
    sqlConn.commit()
    sqlConn.close()
    return redirect('question?questionId=' + str(questionId))

@app.route('/buy', methods=['POST'])
def buyShares():
    username = session['username']
    questionId = request.form['questionId']
    optionId = int(request.form['optionId'])
    count = int(request.form['count'])
    
    
    sqlConn = sqlite3.connect(DATABASE)
    cost = market.getTotalPrice(questionId, optionId, count)
    sqlConn.close()
    
    if cost > userCurrencyForQuestion(username, questionId):
        return "Cannot afford transaction!"
    else:
        updateUserSharesAndCurrencyForQuestionAndOption(username, questionId, optionId, count, -cost)
    
    return "SUCCESS"

@app.route('/sell', methods=['POST'])
def sellShares():
    username = session['username']
    questionId = request.form['questionId']
    optionId = int(request.form['optionId'])
    count = int(request.form['count'])
    
    sqlConn = sqlite3.connect(DATABASE)
    cost = market.getTotalPrice(questionId, optionId, count)
    sqlConn.close()
    
    if abs(count) > userSharesForQuestionAndOption(username, questionId, optionId):
        return "Cannot afford transaction!"
    else:
        updateUserSharesAndCurrencyForQuestionAndOption(username, questionId, optionId, count, -cost)
    
    return "SUCCESS"

@app.route('/checkBuy', methods=['POST'])
def checkBuyShares():
    username = session['username']
    questionId = request.form['questionId']
    optionId = request.form['optionId']
    count = request.form['count']
    
    cost = market.getTotalPrice(questionId, optionId, count)
    return str(cost)

@app.route('/checkSell', methods=['POST'])
def checkSellShares():
    username = session['username']
    questionId = request.form['questionId']
    optionId = int(request.form['optionId'])
    count = int(request.form['count'])
    
    ret = market.getTotalPrice(questionId, optionId, -count)
    return str(ret)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=True, threaded=True)
    except Exception as e:
        print traceback.print_exc()
