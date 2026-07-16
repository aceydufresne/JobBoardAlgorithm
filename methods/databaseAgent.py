import mysql.connector
import sys

    
def fetch(username):
    db = mysql.connector.connect(host = "***",
                                 user = "***",
                                 passwd = "***",
                                 database = "***")
    mycursor = db.cursor()
    sql = """
SELECT username, resumeTxt, city, state
FROM users
WHERE username = %s
"""
    mycursor.execute(sql, (username))
    result = mycursor.fetchone()
    
    if result:
        username, city, state, resume = result
    else:
        print("error line 19")
    
    return username, city, state, resume


        

def update_term(term, isFirst):
    
    db = mysql.connector.connect(host = "***",
                                 user = "***",
                                 passwd = "***",
                                 database = "***")
    mycursor = db.cursor()

    
    sql = """
    SELECT `count`, resCount
    FROM terms
    WHERE term = %s
    """
    
    mycursor.execute(sql,(term,))
    result = mycursor.fetchone()
    if result is None:
        termCount = 1
        docCount = 1
        sqlInsert = """
        INSERT INTO terms (term, `count`, resCount)
        VALUES (%s, %s, %s)
        """
        mycursor.execute(sqlInsert, (term,termCount, docCount))
    else:
        termCount, docCount = result
        termCount += 1
        if isFirst == True:
            docCount +=1
        sqlUpdate = """
        UPDATE terms
        SET `count` = %s,
        resCount = %s
        WHERE term = %s
        """
        mycursor.execute(sqlUpdate, (termCount,docCount, term))
    db.commit()
    mycursor.close()
    db.close()
    return termCount, docCount
        
    
if __name__ == "__main__":
    name = "example"
    city = "kennesaw"
    state = "ga"
    print(sys.executable)
