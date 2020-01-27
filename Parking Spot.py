'''This is a tool developed to find the most available parking spot by tracking
    them over time'''


# connect to postgres database with psycopg2
import psycopg2
import itertools
import plotly.express as px
import plotly.graph_objects as go
import postgres_to_pandas as ptp

invalid = 'That is not a valid input. Try again.\n'
hours = [str(_).zfill(2) for _ in range(0,24)]

def is_valid(inp, condition, error=invalid):
    while True:
        entry = input(inp)
        if condition(entry):
            break
        else:
            print(error)
            continue
    return entry

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



class Tables():
    table_entries = '''CREATE TABLE "parking_spot_entries" (
                        ID                         SERIAL PRIMARY KEY,
                        SPOT                      VARCHAR(5) NOT NULL,
                        EMPTY                        BOOLEAN NOT NULL,
                        TIME    INTEGER CHECK (TIME BETWEEN 0 and 24)
                        );'''
    
    table_stats = '''CREATE TABLE "parking_spot_stats" (
                        ID                         SERIAL PRIMARY KEY,
                        SPOT                      VARCHAR(5) NOT NULL,
                        TIME    INTEGER CHECK (TIME BETWEEN 0 and 24),
                        PROBABILITY                      NUMERIC(3,2),
                        ENTRIES                               INTEGER,
                        STD                              NUMERIC(4,3)               
                        );'''
    def create_table(create_table_query):
        cur.execute(create_table_query)
        connection.commit()


class Entry():
 
    def create_entry():
        ''' user input to fill entries '''
        spot = is_valid('\nWhat is the parking spot?\n', lambda spot: 0 < len(spot) <= 5, error='5 char limit.')
        '''while True: 
            spot = input('\nWhat is the parking spot?\n')
            if 0 < len(spot) <= 5:
                break
            else:
                print('5 char limit.')
                continue'''

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

    def add_stats():
        '''Calculates probability and STD for each spot, time, and inserts into new table stats'''
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
                    probability = empty_count/total_count
                    STD = (probability*(1-probability)/total_count)**0.5

                entry_query = '''INSERT INTO "parking_spot_stats" (SPOT, TIME, PROBABILITY, ENTRIES, STD) 
                        VALUES (%s, %s, %s, %s, %s)'''
                entry_insert = (spot, hour, probability, total_count, STD)
                cur.execute(entry_query, entry_insert)
                connection.commit()

    def update_stats():
        '''Drops existing stats table, recreates and populates from new entries'''
        cur.execute('DROP TABLE parking_spot_stats')
        Tables.create_table(table_stats)
        add_stats()
        

class Statistics():

    def best_prob_for_time():
        ''' present spot with the highest probability at user given time'''
        time = is_valid(inp=("What time(hour) do you want to find the best probabilities for?\n"), 
                            condition = lambda time: time.zfill(2) in hours, error = ('That is not a valid time.'))
        query_max_prob = ('''SELECT SPOT, PROBABILITY, STD, ENTRIES FROM parking_spot_stats WHERE TIME = {} ORDER BY PROBABILITY DESC'''.format(time))
        cur.execute(query_max_prob)
        top_five = cur.fetchall()[:5]
        print(f'At time {time}Hs, the spots with the highest probability of being empty are:\n')
        for i in range(5):
            spot, probability, STD, entries = top_five[i]
            print(f"\nSpot: {spot},\tProbability: {probability},\tSTD: {STD},\tEntries: {entries}")


    def prob_of_spots_per_time_visual():
        ''' present graph of probability of spots for user selected time'''
        time = input("What time(hour) do you want to view the spot's probabilities for?\n").zfill(2)
        query = ('SELECT SPOT, PROBABILITY, STD, ENTRIES FROM parking_spot_stats WHERE TIME = {}'.format(time))
        # graph using plotly
        data = ptp.query_to_df(query)
        fig = px.bar(data, x='spot', y='probability', error_y='std',
                    color='probability', color_continuous_scale='purp',
                    plot_bgcolor='rgba(0,0,0,0)', 
                    hover_data=['entries'],              
        )
        fig.update_layout(
                title={
                    'text':'{}Hs'.format(time),
                    'y':0.95,
                    'x':0.5,
                    'font':{
                        'size': 28},
                    },
                xaxis_title="Spot",
                yaxis_title="Probability",
                font=dict(
                    family="Courier New, monospace",
                    size=16,
                    color="#000000"
                    ),
            )
        fig.show()


    def spots_prob_change_over_time_visual():
        ''' present change of probability for all spots over time '''
        # ask user which spots they would like to view
        while True:
            selected_spots = input('\nWhich spot(s) would you like to view? Enter "all" for all.\nEnter "spots" for a list of spots.\n').lower()
            cur.execute('SELECT DISTINCT spot FROM parking_spot_stats')
            spots = [s[0] for s in cur.fetchall()]
            count = 1
            if selected_spots == 'spots':
                print(spots)
                continue
            elif selected_spots == 'all':
                data = ptp.table_to_df('parking_spot_stats')
                break
            elif selected_spots in spots:
                many = None
                while True:
                    another = input('Add another spot? Enter y/n.\n').lower()
                    if another == 'n':
                        many = 0
                        break
                    elif another == 'y':
                        selected_spots = list(selected_spots)
                        while True:
                            many = input('How many more spots would you like to add?\n')
                            # check input is valid
                            try:
                                many = int(many)
                                if 0 <= many < len(spots):
                                    break
                                else:
                                    print(f'You can only add between 0 and {len(spots)-1} more spots.\n')
                                    continue
                            except ValueError:
                                print('That is not a valid integer.\n')
                                continue
                        # add 'many' input spots to list
                        for i in range(int(many)):
                            while True:
                                new_spot = (input('Enter spot:\t'))
                                remaining_spots = [spot for spot in spots if spot not in selected_spots]
                                # repitition not allowed
                                if new_spot in selected_spots:
                                    inp = input('''You have already entered that spot, try another.\nTo view chosen spots, enter "view".
                                                To view remaining spots, enter "spots". Any other key to continue.\n''')
                                    if inp == 'view':
                                        print(selected_spots)
                                    if inp == 'spots':
                                        print(remaining_spots)
                                    continue
                                elif new_spot in spots:
                                    selected_spots.append(new_spot)
                                    break
                                else:
                                    print('That is not a valid spot.\n')
                                    if input('Do you want to view available spots? Enter "y", or another key to try again.\n').lower() == 'y':
                                        print(remaining_spots)
                                    continue
                        break
                    else:
                        print(invalid)
                        continue
                if (count+many)>1:
                    query = ('SELECT SPOT, PROBABILITY, TIME, STD, ENTRIES FROM parking_spot_stats WHERE SPOT IN {}'.format(tuple(selected_spots)))
                else:
                    # cast needed when single value passed to avoid type error
                    query = ('SELECT SPOT, PROBABILITY, TIME, STD, ENTRIES FROM parking_spot_stats WHERE SPOT = (SELECT CAST({} AS VARCHAR))'.format(selected_spots))
                data = ptp.query_to_df(query)
                break         
            else:
                print(invalid)
                continue
            
        fig = px.scatter(data,
                        x='time', 
                        y='probability', 
                        hover_name='spot',
                        color='spot', 
                        hover_data=['entries', 'std'], 
                        size='std', 
                        # find way to scale size, reverse     
                    )       
        fig.update_traces(mode='lines+markers')          
        fig.update_layout(
                title={
                    'text':'Spots\' Probabiliy change over Time',
                    'y':0.95,
                    'x':0.5,
                    'font':{
                        'size': 28},
                    },
                xaxis_title="Time (Hours)",
                yaxis_title="Probability",
                font=dict(
                    family="Courier New, monospace",
                    size=16,
                    color="#000000"
                    ),
                xaxis=dict(
                    tickmode='linear',
                    ticks='outside',
                    tick0=0,
                    dtick=1,
                    range=[-.5,23.5]
                    ),
                yaxis=dict(
                    tickmode='linear',
                    ticks='outside',
                    tick0=0,
                    dtick=0.25,
                    range=[-0.01, 1.01]
                    ),
                legend=go.layout.Legend(
                    traceorder="normal",
                    bordercolor="Black",
                    borderwidth=1
                    ),
                #paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                #height=500
            )   
        fig.show()




Entry.create_entry()




