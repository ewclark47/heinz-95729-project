"""
author: Elliott Clark, Mayank Bansal
Module to handle all of the database queries that need to be made 
for ScottyBots functionality.
This module contains functions to add a course to a users schedule,
drop a course from a users schedule, search the available courses and
display them to the user and display a users individual schedule.
This module also validates user and schedule existence in serparate 
in order to add the user or schedule if needed prior to performing
any queries.
This module requires that `mysql` be installed within the Python
environment you are running this script in.
This module contains the following functions:
    * checkuser - checks if messaging user has an entry in the database
    * checkUserSchedule - checks the schedule for the user
    * addCourse - adds courses to a user's schedule
    * dropCourse - drops courses from a user's schedule
    * viewSchedule - shows the schedule for a user
    * findCourse - finds a course based on a description
    * method_tests - various tests for the module
"""

import mysql.connector
import os

mydb = mysql.connector.connect(
    user="ScottyAdmin",
    password=os.environ.get("DB_PASSWORD"),
    host="scottybot-db.mysql.database.azure.com",
    port=3306,
    database="scottybot",
    ssl_ca="DigiCertGlobalRootCA.crt.pem"
)
cursor = mydb.cursor()


def checkUser(username):
    """ Check to see if the user that mentioned ScottyBot is in the database
    If so, return True. If not, add the user to the database and then 
    return True 

    Parameters
    ----------
    username : str
        String containing the user identifier information

    Returns
    -------
    bool
        Based on the presence of user in database returns true or false 
    """

    queryString = "SELECT * FROM users WHERE UserName=\'"+str(username)+"\'"
    cursor.execute(queryString)
    validUser = cursor.fetchall()

    if len(validUser) > 0:
        return True
    else:
        queryString = "INSERT INTO users(UserName) VALUES (\'" + \
            str(username)+"\')"
        cursor.execute(queryString)
        mydb.commit()
        queryString = "SELECT * FROM users WHERE UserName=\'" + \
            str(username)+"\'"
        cursor.execute(queryString)
        addedUser = cursor.fetchall()
        return True


def checkUserSchedule(userID):
    """ Check to see if the user that mentioned ScottyBot has a schedule
    If so, return True. If not, add a schedule for the user to the database and then
    return True

    Parameters
    ----------
    userID : str
        String containing the user identifier information

    Returns
    -------
    bool
        Based on the presence of user's schedule in database returns true or false 
    """

    queryString = "SELECT * FROM schedules WHERE UserID="+str(userID)
    cursor.execute(queryString)
    scheduleDoesExist = cursor.fetchall()
    if len(scheduleDoesExist) > 0:
        return True
    else:
        # add in a schedule for this user with default values
        queryString = "INSERT INTO schedules(UserID) VALUES ("+str(userID)+")"
        cursor.execute(queryString)
        mydb.commit()
        return True


def addCourse(username, courseNumber):
    """ Performs the function of adding course to the database based on 
    the username and course number

    Parameters
    ----------
    username : str
        String containing the user identifier information
    courseNumber : int
        Integer value of the course number
    """

    try:
        queryString = "SELECT * FROM course WHERE CourseNumber=" + \
            str(courseNumber)
        cursor.execute(queryString)
        courseInfo = cursor.fetchone()
        courseInfo = courseInfo[1:]
        new_str = ""
        for r in courseInfo:
            new_str += str(r)+", "
        courseInfo = new_str

        if checkUser(username):
            queryString = "SELECT UserID FROM users WHERE UserName=\'" + \
                str(username)+"\'"
            cursor.execute(queryString)
            userID = cursor.fetchone()
            userID = userID[0]
            # get how many courses this user has (IF THEY HAVE THEM) and then add in the request course as 'course#' based on that number
            if checkUserSchedule(userID):
                queryString = "SELECT CourseCount FROM schedules WHERE UserID=" + \
                    str(userID)
                cursor.execute(queryString)
                courseCount = cursor.fetchone()
                courseCount = courseCount[0]+1
                cursor.execute(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='schedules'")
                scheduleColumns = cursor.fetchall()
                columnList = []
                for column in scheduleColumns:
                    columnList.append(column[0])
                updateCol = "Course " + str(courseCount)
                if updateCol in columnList:
                    queryString = "UPDATE schedules SET `Course " + \
                        str(courseCount)+"`=\'"+str(courseInfo) + \
                        "\' WHERE UserID="+str(userID)
                    cursor.execute(queryString)
                    mydb.commit()
                    queryString = "UPDATE schedules SET CourseCount=" + \
                        str(courseCount)+" WHERE UserID="+str(userID)
                    cursor.execute(queryString)
                    mydb.commit()  # manual commit added because database was not receiving autocommit from update query
                else:
                    queryString = "ALTER TABLE schedules ADD `Course " + \
                        str(courseCount)+"` VARCHAR(500)"
                    cursor.execute(queryString)
                    queryString = "UPDATE schedules SET CourseCount=" + \
                        str(courseCount)+" WHERE UserID="+str(userID)
                    cursor.execute(queryString)
                    mydb.commit()  # manual commit added because database was not receiving autocommit from update query
                    queryString = "UPDATE schedules SET `Course " + \
                        str(courseCount)+"`=\'"+str(courseInfo) + \
                        "\' WHERE UserID="+str(userID)
                    cursor.execute(queryString)
                    mydb.commit()  # manual commit added because database was not receiving autocommit from update query
            else:
                print("Issue with the username")

    except mysql.connector.Error as e:
        print(e)


def dropCourse(username, courseNumber):
    """ Performs the function of dropping course to the database based on 
    the username and course number

    Parameters
    ----------
    username : str
        String containing the user identifier information
    courseNumber : int
        Integer value of the course number
    """

    try:
        cursor = mydb.cursor()
        queryString = "SELECT UserID FROM users WHERE username=\'" + \
            str(username)+"\'"
        cursor.execute(queryString)
        userID = cursor.fetchone()
        userID = userID[0]
        queryString = "SELECT CourseCount FROM schedules WHERE UserID=" + \
            str(userID)
        cursor.execute(queryString)
        courseCount = cursor.fetchone()
        courseCount = courseCount[0]
        # iterate through the schedule and figure out how to get the column
        # name for whichever course entry contain the specified course number
        # (our course description)
        # then update that column to null for the user "dropping" that course
        cursor.execute(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='schedules'")
        scheduleColumns = cursor.fetchall()
        columnList = []
        for column in scheduleColumns:
            columnList.append(column[0])
        cursor.execute("SELECT * FROM schedules WHERE UserID="+str(userID))
        scheduleRow = cursor.fetchone()
        scheduleValues = []
        for value in scheduleRow:
            scheduleValues.append(value)
        for i in range(len(scheduleValues)):
            if str(courseNumber) in str(scheduleValues[i]):
                columnName = columnList[i]
        cursor.execute("UPDATE schedules SET `"+str(columnName) +
                       "`=\' \' WHERE UserID="+str(userID))
        mydb.commit()
        # use the original coursecount to check if columns need slid left
        courses = []
        for i in range(1, courseCount+1):
            cursor.execute("SELECT `Course "+str(i) +
                           "` FROM schedules WHERE UserID="+str(userID))
            info = cursor.fetchone()
            courses.append(info[0])
        courses.remove(' ')
        for i in range(len(courses)):
            cursor.execute("UPDATE schedules SET `Course "+str(i+1) +
                           "`=\'"+str(courses[i])+"\' WHERE UserID="+str(userID))
            mydb.commit()
        cursor.execute("UPDATE schedules SET `Course " +
                       str(courseCount)+"`=\' \'")
        mydb.commit()
        cursor.execute("UPDATE schedules SET CourseCount=" +
                       str(courseCount-1)+" WHERE UserID="+str(userID))
        mydb.commit()

    except mysql.connector.Error as e:
        print(e)


def viewSchedule(username):
    """ Performs the function of viewing the schedule in the database based on 
    the username

    Parameters
    ----------
    username : str
        String containing the user identifier information

    Returns
    -------
    str
        String containing the schedule information for the user
    """
    try:
        cursor = mydb.cursor()
        if checkUser(username):
            queryString = "SELECT UserID FROM users WHERE UserName=\'" + \
                str(username)+"\'"
            userID = cursor.execute(queryString)
            userID = cursor.fetchone()
            userID = userID[0]
            if checkUserSchedule(userID):
                queryString = "SELECT * FROM schedules WHERE UserID=" + \
                    str(userID)
                cursor.execute(queryString)
                row = cursor.fetchone()
                scheduleString = ""
                if len(row[3:]) > 0:
                    for r in row[3:]:
                        if r == "" or r == " ":
                            scheduleString += ""
                        else:
                            scheduleString += "\n" + str(r)
                    if scheduleString == "":
                        scheduleString = "You haven't scheduled anything yet!"
                else:
                    scheduleString = "You haven't scheduled anything yet!"
        return scheduleString

    except mysql.connector.Error as e:
        print(e)


def findCourse(description):
    """ Performs the function of finding the courses in the database based on 
    the description

    Parameters
    ----------
    description : str
        String containing description of the course

    Returns
    -------
    str
        String containing possible courses based on the description
    """

    try:
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM course")
        courses = cursor.fetchall()
        possibleCourse = ""
        for course in courses:
            courseString = ""
            useableString = ""
            for c in course[1:]:
                useableString += str(c) + " "
                courseString += str(c).lower() + " "
            if str(description).lower() in courseString:
                possibleCourse += useableString + "\n"
        return possibleCourse

    except mysql.connector.Error as e:
        print(e)


def method_tests():
    """below was used for testing and will not be functionality in the final product"""
    try:
        cursor = mydb.cursor()
        # test using partial course number -> shows all
        """ #print("Finding a course using partial course number: ")
        findCourse(95) """
        # test using partial course name "Machine Learning" -> shows ecomm and MLPS
        # print("Finding a course using a topic: ")
        # findCourse("Design")
        # test find all courses -> works
        """ #print("Finding all courses: ")
        findCourse(" ") """

        # test viewing an empty schedule -> works
        # print(viewSchedule("nonexistuser"))
        # test adding a course when others have more courses -> works
        # addCourse("testuserrando", 95729)
        # test dropping a course -> works
        # dropCourse("testuserrando", 95729)

        # testing to make sure the new drop method shifts -> works
        """ addCourse("randotestuser",95702)
        addCourse("randotestuser",95729)
        addCourse("randotestuser",95828)
        dropCourse("randotestuser",95702)
        #print(viewSchedule("randotestuser"))
        addCourse("randotest",95702)
        addCourse("randotest",95729)
        addCourse("randotest",95828)
        dropCourse("randotest",95729)
        #print(viewSchedule("randotest"))
        addCourse("randouser",95702)
        addCourse("randouser",95729)
        addCourse("randouser",95828)
        dropCourse("randouser",95828)
        #print(viewSchedule("randouser")) """

    except mysql.connector.Error as e:
        print(e)

    finally:
        cursor.close()
        mydb.close()


if __name__ == '__main__':
    method_tests()