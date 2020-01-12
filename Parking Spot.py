'''This is a tool developed to find the most available parking spot by tracking
    them over time'''


# connect to postgres database with psycopg2
import psycopg2
try:
    connection = psycopg2.connect(
                        user = 'Nima',
                        password = '',
                        host = '127.0.0.1',
                        database = 'djangoproject'
                        )
except:
    ('Could not connect to Database.')

cur = connection.cursor()
invalid = 'That is not a valid input. Try again.\n'


def create_table():
    create_table_query = '''CREATE TABLE "parking_spot" (
                    ID                         SERIAL PRIMARY KEY,
                    SPOT                      VARCHAR(5) NOT NULL,
                    EMPTY                        BOOLEAN NOT NULL,
                    TIME    INTEGER CHECK (TIME BETWEEN 0 and 24)
                    );'''

    #cur.execute(create_table_query)
    #connection.commit()

def create_entry():
    while True: 
        spot = input('\nWhat is the parking spot?\n')
        if 0 < len(spot) <= 5:
            break
        else:
            continue

    while True:
        empty = input('\nWas it empty? Enter "True" or "False"\n')
        if empty in ['True', 'False']:
            break
        else:
            print(invalid)
            continue

    hours = [str(_).zfill(2) for _ in range(0,24)]
    while True:
        time = input('\nWhat was the time?\nEnter hour 0-23\n').zfill(2)
        if time in hours:
            break
        else:
            print(invalid)
            continue
    return spot, empty, time


def submit_entry(entry):
    spot, empty, time = entry
    entry_query = '''INSERT INTO "parking_spot" (SPOT, EMPTY, TIME) VALUES (%s, %s, %s)'''
    entry_insert = (spot, empty, time)
    cur.execute(entry_query, entry_insert)
    connection.commit()
    print('Entry added.')

def check_entry(entry):
    spot, empty, time = entry
    print(f'\nYou entered:\nspot: {spot}\nEmpty: {empty}\nTime: {time}H')                   
    while True:
        check = input('\nIs this correct? Enter y/n.\n').lower() 
        if check.lower() == 'y':
            return True
            break
        elif check.lower() == 'n':
            return False
            break
        else:
            print(invalid)
            continue

#run program
# see if user wants to add an entry
def ask_for_entry():
    while True:
        check = input('\nWould you like to add an entry?\n\tEnter y/n.\n').lower()
        if check =='y':
            entry = create_entry()
            # check with user if entry is correct, if not repeat create_entry()
            while True:
                if check_entry(entry):
                    # add later option to change specific entry instead of re-do
                    submit_entry(entry)
                    break    
                else:
                    entry = create_entry()
                    continue
            continue          
        elif check =='n':
            if(connection):
                cur.close()
                connection.close()
                print('PostgreSQl connection is closed')
            break
        else:
            print(invalid)
            continue

ask_for_entry()
        
        



#Intro - ask the user to input labels for the parking spots they wish to track


#Create a database or spreadsheet with the prior user inputs


#Ask the user to enter when they notice a spot available or busy

'''spot number,
empty or taken,
time of day (24hours) X
can create a number tally, each addition is +1
- so 48 options per spot'''


#Do analysis and list the spots with highest frequency of availabiliy

#Extra: consider by time of day