
import pandas as pd
from sqlalchemy import create_engine

# follows django database settings format, replace with your own settings
DATABASES = {
    'djangoproject':{
        'NAME': 'djangoproject',
        'USER': 'Nima',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': 5432,
    },
}

# choose the database to use
db = DATABASES['djangoproject']

# construct an engine connection string
engine_string = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
    user = db['USER'],
    password = db['PASSWORD'],
    host = db['HOST'],
    port = db['PORT'],
    database = db['NAME'],
)

# create sqlalchemy engine
engine = create_engine(engine_string)

# read a table from database into pandas dataframe, replace "tablename" with your table name
def query_to_df(query):
    df = pd.read_sql_query(query,engine)
    return df

def table_to_df(table):
    df = pd.read_sql_table(table,engine)
    return df

