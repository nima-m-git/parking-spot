'''This is a tool developed to find the most available parking spot by tracking
    them over time'''


# connect to postgres database with psycopg2
import psycopg2
from psycopg2 import sql

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

hours = [str(_).zfill(2) for _ in range(0,24)]

class Tables():
    table_entries = '''CREATE TABLE "parking_spot_entries" (
                        ID                         SERIAL PRIMARY KEY,
                        SPOT                      VARCHAR(5) NOT NULL,
                        EMPTY                        BOOLEAN NOT NULL,
                        TIME    INTEGER CHECK (TIME BETWEEN 0 and 24)
                        );'''
    
    table_status = '''CREATE TABLE "parking_spot_stats" (
                        ID                         SERIAL PRIMARY KEY,
                        SPOT                      VARCHAR(5) NOT NULL,
                        TIME    INTEGER CHECK (TIME BETWEEN 0 and 24),
                        EMPTY_PROB                       NUMERIC(3,2),
                        ENTRIES                               INTEGER,
                        STD                               NUMERIC(3,2)               
                        );'''
    def create_table(create_table_query):
        cur.execute(create_table_query)
        connection.commit()


class Entry():
    invalid = 'That is not a valid input. Try again.\n'
    
    def create_entry():
        ''' user input to fill entries '''
        while True: 
            spot = input('\nWhat is the parking spot?\n')
            if 0 < len(spot) <= 5:
                break
            else:
                print('5 char limit.')
                continue

        while True:
            empty = input('\nWas it empty? Enter "True" or "False"\n').title()
            if empty in ['True', 'False']:
                break
            else:
                print(invalid)
                continue

        while True:
            time = input('\nWhat was the time?\nEnter hour 0-23\n').zfill(2)
            if time in hours:
                break
            else:
                print(invalid)
                continue
        return spot, empty, time

    def submit_entry(entry):
        ''' submit user entry into postgres DB entries table'''
        spot, empty, time = entry
        entry_query = '''INSERT INTO "parking_spot_entries" (SPOT, EMPTY, TIME) VALUES (%s, %s, %s)'''
        entry_insert = (spot, empty, time)
        cur.execute(entry_query, entry_insert)
        connection.commit()
        print('Entry added.')

    def check_entry(entry):
        ''' check with user the entry is valid, if not - repeat entry'''
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

    def ask_for_entry():
        ''' run program, see if user wants to add an entry'''
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

# retrieves all spot names
cur.execute('SELECT DISTINCT spot FROM parking_spot_entries')
spot_list = cur.fetchall()              

# counts time each spot and time is avail
for spot in spot_list:
    for hour in hours:
        cur.execute("SELECT COUNT(*) FROM parking_spot_entries WHERE SPOT = (%s) AND TIME = (%s) AND EMPTY = true",
                    (spot, hour))
        empty_count = int(cur.fetchone()[0])
        cur.execute("SELECT COUNT(*) FROM parking_spot_entries WHERE SPOT = (%s) AND TIME = (%s)", (spot, hour))
        total_count = int(cur.fetchone()[0])
        # if there are no entries, probability and std are null
        if total_count:
            # calculate probability of spot being empty at given time 
            probability = empty_count/total_count
            P, TC = probability, total_count
            # calculate binomial distribution standard deviation for the probability
            STD = (P*(1-P)/TC)**0.5
        else:
            probability, STD = None, None

        entry_query = '''INSERT INTO "parking_spot_stats" (SPOT, TIME, EMPTY_PROB, ENTRIES, STD) 
                VALUES (%s, %s, %s, %s, %s)'''
        entry_insert = (spot, hour, P, TC, STD)
        cur.execute(entry_query, entry_insert)
        connection.commit()
    


