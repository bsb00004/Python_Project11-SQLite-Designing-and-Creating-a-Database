#!/usr/bin/env python
# coding: utf-8

# ### Project 11 -  Designing and Creating a Database in SQLite3
# In this project, we're going to learn how to:
# 
# - Import data into SQLite
# - Design a normalized database schema
# - Create tables for our schema
# - Insert data into our schema
# 
# We will be working with a file of Major League Baseball games from [Retrosheet](https://www.retrosheet.org/). Retrosheet compiles detailed statistics on baseball games from the 1800s through to today. The main file we will be working from __game_log.csv__, has been produced by combining 127 separate CSV files from retrosheet, and has been pre-cleaned to remove some inconsistencies. The game log has hundreds of data points on each game which we will normalize into several separate tables using SQL, providing a robust database of game-level statistics.
# 
# In addition to the main file, I have also included three 'helper' files, also sourced from Retrosheet:
# 
# - park_codes.csv
# - person_codes.csv
# - team_codes.csv
# 
# These three helper files in some cases contain extra data, but will also make things easier as they will form the basis for three of our normalized tables.
# 
# An important first step when working with any new data is to perform exploratory data analysis (EDA). EDA gets us familiar with the data and gives us a level of background knowledge that will help us throughout our project. The methods we use when performing EDA will depend on what we plan to do with the data. In this case, we're wanting to create a normalized database, so the focus should be:
# 
# - Becoming familiar, at a high level, with the meaning of each column in each file.
# - Thinking about the relationships between columns within each file.
# - Thinking about the relationships between columns across different files.
# 
# It also included a __game_log_fields.txt__ file from Retrosheet which explains the fields included in our main file, which will be useful to assist our EDA. You can use !cat __game_log_fields.txt__ in its own Jupyter cell to read the contents of the file.
# 
# If you're not familiar with baseball some of this can seem overwhelming at first, however this presents a great opportunity. When you are working with data professionally, you'll often encounter data in an industry you might be unfamiliar with - it might be digital marketing, geological engineering or industrial machinery. In these instances, you'll have to perform research in order to understand the data you're working with.
# 
# Baseball is a great topic to practice these skills with. Because of the long history within baseball of the collection and analysis of statistics (most famously the Sabermetrics featured in the movie Moneyball), there is a wide range of online resources available to help you get answers to any questions you may have.
# 
# Let's get started exploring the data by using pandas to read and explore the data. Setting the following options after you import pandas is recommended– they will prevent the DataFrame output from being truncated, given the size of the main game log file:
# 
# - pd.set_option('max_columns', 180)
# - pd.set_option('max_rows', 200000)
# - pd.set_option('max_colwidth', 5000)
# 
# Then Using pandas, read in each of the four CSV files: __game_log.csv__, __park_codes.csv__, __person_codes.csv__, __team_codes.csv__. For each:
# 
# Use methods and attributes like _DataFrame.shape_, _DataFrame.head()_, and _DataFrame.tail()_ to explore the data.

# In[2]:


# Importing pandas, sqlite3 and csv
import sqlite3
import pandas as pd
import csv

pd.set_option('max_columns', 180)
pd.set_option('max_rows', 200000)
pd.set_option('max_colwidth', 5000)


# ## Getting to Know the Data

# In[3]:


log = pd.read_csv("game_log.csv",low_memory=False)
print(log.shape)
log.head()


# In[4]:


log.tail()


# It looks like the game log has a record of over 170,000 games.  It looks like these games are chronologically ordered and occur between 1871 and 2016.
# 
# For each game we have:
# 
# - general information on the game
# - team level stats for each team
# - a list of players from each team, numbered, with their defensive positions
# - the umpires that officiated the game
# - some 'awards', like winning and losing pitcher
# 
# We have a `game_log_fields.txt` file that tell us that the player number corresponds with the order in which they batted.
# 
# It's worth noting that there is no natural primary key column for this table.

# In[5]:


person = pd.read_csv('person_codes.csv')
print(person.shape)
person.head()


# This seems to be a list of people with IDs.  The IDs look like they match up with those used in the game log.  There are debut dates, for players, managers, coaches and umpires.  We can see that some people might have been one or more of these roles.
# 
# It also looks like coaches and managers are two different things in baseball.  After some research, managers are what would be called a 'coach' or 'head coach' in other sports, and coaches are more specialized, like base coaches.  It also seems like coaches aren't recorded in the game log.

# In[6]:


park = pd.read_csv('park_codes.csv')
print(park.shape)
park.head()


# This seems to be a list of all baseball parks.  There are IDs which seem to match with the game log, as well as names, nicknames, city and league.

# In[7]:


team = pd.read_csv('team_codes.csv')
print(team.shape)
team.head()


# This seems to be a list of all teams, with team_ids which seem to match the game log. Interestingly, there is a `franch_id`, let's take a look at this:

# In[8]:


team["franch_id"].value_counts().head()


# We might have `franch_id` occurring a few times for some teams, let's look at the first one in more detail.

# In[9]:


team[team["franch_id"] == 'BS1']


# It appears that teams move between leagues and cities.  The team_id changes when this happens, `franch_id` (which is probably 'Franchise') helps us tie all of this together.

# **Defensive Positions**
# 
# In the game log, each player has a defensive position listed, which seems to be a number between 1-10.  Doing some research around this, I found [this article](http://probaseballinsider.com/baseball-instruction/baseball-basics/baseball-basics-positions/) which gives us a list of names for each numbered position:
# 
# 1. Pitcher
# 2. Catcher
# 3. 1st Base
# 4. 2nd Base
# 5. 3rd Base
# 6. Shortstop
# 7. Left Field
# 8. Center Field
# 9. Right Field
# 
# The 10th position isn't included, it may be a way of describing a designated hitter that does not field.  I can find a retrosheet page that indicates that position `0` is used for this, but we don't have any position 0 in our data.  I have chosen to make this an 'Unknown Position' so I'm not including data based on a hunch.
# 
# **Leagues**
# 
# Wikipedia tells us there are currently two leagues - the American (AL) and National (NL). Let's start by finding out what leagues are listed in the main game log:

# In[10]:


log["h_league"].value_counts()


# It looks like most of our games fall into the two current leagues, but that there are four other leagues.  Let's write a quick function to get some info on the years of these leagues:

# In[11]:


def league_info(league):
    league_games = log[log["h_league"] == league]
    earliest = league_games["date"].min()
    latest = league_games["date"].max()
    print("{} went from {} to {}".format(league,earliest,latest))

for league in log["h_league"].unique():
    league_info(league)


# Now we have some years which will help us do some research.  After some googling we come up with:
# 
# - `NL`: National League
# - `AL`: American League
# - `AA`: [American Association](https://en.wikipedia.org/wiki/American_Association_%2819th_century%29)
# - `FL`: [Federal League](https://en.wikipedia.org/wiki/Federal_League)
# - `PL`: [Players League](https://en.wikipedia.org/wiki/Players%27_League)
# - `UA`: [Union Association](https://en.wikipedia.org/wiki/Union_Association)
# 
# It also looks like we have about 1000 games where the home team doesn't have a value for league.

# ## Importing Data into SQLite
# 
# - Recreating the run_command() and run_query() functions.
# 
# - Using DataFrame.to_sql() to create tables for each of our dataframes in a new SQLite database, mlb.db:
#     - The table name should be the same as each of the CSV filename without the extension, eg game_log.csv should be imported to a table called game_log.
#     
# - Using run_command(), create a new column in the game_log table called game_id:
#     - Use SQL string concatenation to update the new columns with a unique ID using the Retrosheet format outlined above.

# In[12]:


# These helper functions will be useful as we work
# with the SQLite database from python

DB = "mlb.db"

def run_query(q):
    with sqlite3.connect(DB) as conn:
        return pd.read_sql(q,conn)

def run_command(c):
    with sqlite3.connect(DB) as conn:
        conn.execute('PRAGMA foreign_keys = ON;')
        conn.isolation_level = None
        conn.execute(c)

def show_tables():
    q = '''
    SELECT
        name,
        type
    FROM sqlite_master
    WHERE type IN ("table","view");
    '''
    return run_query(q)


# In[13]:


tables = {
    "game_log": log,
    "person_codes": person,
    "team_codes": team,
    "park_codes": park
}

with sqlite3.connect(DB) as conn:    
    for name, data in tables.items():
        conn.execute("DROP TABLE IF EXISTS {};".format(name))
        data.to_sql(name,conn,index=False)


# In[14]:


show_tables()


# In[15]:


c1 = """
ALTER TABLE game_log
ADD COLUMN game_id TEXT;
"""

# try/except loop since ALTER TABLE
# doesn't support IF NOT EXISTS
try:
    run_command(c1)
except:
    pass

c2 = """
UPDATE game_log
SET game_id = date || h_name || number_of_game
/* WHERE prevents this if it has already been done */
WHERE game_id IS NULL; 
"""

run_command(c2)

q = """
SELECT
    game_id,
    date,
    h_name,
    number_of_game
FROM game_log
LIMIT 5;
"""

run_query(q)


# ## Looking for Normalization Opportunities

# Rather than learn and follow specific normalized forms, we're going to look for specific opportunities to normalize our data by reducing repetition. Here are two examples of repetition we can find and remove:
# 
# - __Repetition in columns__
# - __Non-primary key columns should be attributes of the primary key__
# - __Redundant Data__
# 
# The following are opportunities for normalization of our data:
# 
# - In `person_codes`, all the debut dates will be able to be reproduced using game log data.
# - In `team_codes`, the start, end and sequence columns will be able to be reproduced using game log data.
# - In `park_codes`, the start and end years will be able to be reproduced using game log data.  While technically the state is an attribute of the city, we might not want to have a an incomplete city/state table so we will leave this in.
# - There are lots of places in `game` log where we have a player ID followed by the players name.  We will be able to remove this and use the name data in `person_codes`
# - In `game_log`, all offensive and defensive stats are repeated for the home team and the visiting team.  We could break these out and have a table that lists each game twice, one for each team, and cut out this column repetition.
# - Similarly, in `game_log`, we have a listing for 9 players on each team with their positions - we can remove these and have one table that tracks player appearances and their positions.
# - We can do a similar thing with the umpires from `game_log`, instead of listing all four positions as columns, we can put the umpires either in their own table or make one table for players, umpires and managers.
# - We have several awards in `game_log` like winning pitcher and losing pitcher.  We can either break these out into their own table, have a table for awards, or combine the awards in with general appearances like the players and umpires.

# ## Planning a Normalized Schema
# 

# The following schema was planned using [DbDesigner.net](https://dbdesigner.net/): This free tool allows you to create a schema and will create lines to show foreign key relations clearly.
# 
# Here are some tips when planning out your schema:
# 
#  - Don't be afraid to experiment. It's unlikely that your first few steps will be there in your finished product - try things and see how they look.
#  - If you're using a tool like DbDesigner which automatically shows lines for foreign key relationships, don't worry if your lines look messy. This is normal– you can move the tables around to neaten things up at the end, but don't waste time on it while you are still normalizing.
#  - The following facts about the data may help you with your normalization decisions:
#     - Historically, teams sometimes move between leagues.
#     - The same person might be in a single game as both a player and a manager
#     - Because of how pitchers are represented in the game log, not all pitchers used in a game will be shown. We only want to worry about the pitchers mentioned via position or the 'winning pitcher'/ 'losing pitcher'.
#  - It is possible to over-normalize. We want to finish with about 7-8 tables total.
# 
# Lastly, best advise is to spend between 60-90 minutes on your planning your schema.
# 
# <img src="https://raw.githubusercontent.com/dataquestio/solutions/c4b8f0070f124707344760aeb957e68aff514282/images/schema-screenshot.png">
# 
# 

# ## Creating Tables Without Foreign Keys
# So that we can work through the rest of the steps together, we have the above schema for the rest of this guided project. As we work through each table, we'll explain some of the decision made when normalizing and creating the schema. 
# 
# As we work through creating the tables in this schema, we'll talk about why we made particular choices during the normalization process. We'll start by creating the tables that don't contain any foreign key relations. It's important to start with these tables, as other tables will have relations to these tables, and so these tables will need to exist first.
# 
# The tables we will create are below, with some notes on the normalization choices made:
# 
# - person
#     - Each of the 'debut' columns have been omitted, as the data will be able to be found from other tables.
#     - Since the game log file has no data on coaches, we made the decision to not include this data.
# - park
#     - The start, end, and league columns contain data that is found in the main game log and can be removed.
# - league
#     - Because some of the older leagues are not well known, we will create a table to store league names.
# - appearance_type
#     - Our appearance table will include data on players with positions, umpires, managers, and awards (like winning pitcher). This table will store information on what different types of appearances are available.
#     
# We'll first create each table, and then we'll insert the data. Previously, we learned to use the CREATE statement with the VALUES clause to manually specify values to be inserted. For the person and park tables, we have person_codes and park_codes which contain the data we'll need. To use this data we'll CREATE with SELECT:
# 
# __INSERT INTO table_one__
# 
# __SELECT * FROM table_two;__
# 
# Note that you will need to adjust the select statement to specify select columns in order, since our original table and new table have different number of columns in different orders.
# 
# Similar to IF NOT EXISTS, we can use INSERT OR IGNORE [as specified in the SQLite documentation](https://www.sqlite.org/lang_insert.html) to prevent our code from failing if we run it a second time in our notebook.
# 
# For the league table you will need to manually specify the values, and for appearance_type we have provided a appearance_type.csv that you can import which contains all the values you need for this table.
# 
# Steps to follow:
# 
# 1. Create the person table with columns and primary key as shown in the schema diagram.
#  - Select the appropriate type based on the data.
#  - Insert the data from the person_codes table.
#  - Write a query to display the first few rows of the table.
# 2. Create the park table with columns and primary key as shown in the schema diagram.
#  - Select the appropriate type based on the data
#  - Insert the data from the park_codes table.
#  - Write a query to display the first few rows of the table.
# 3. Create the league table with columns and primary key as shown in the schema diagram.
#  - Select the appropriate type based on the data.
#  - Insert the data manually based on your research on the names of the six league IDs.
#  - Write a query to display the table.
# 4. Create the appearance_type table with columns and primary key as shown in the schema diagram.
#  - Select the appropriate type based on the data.
#  - Import and insert the data from appearance_type.csv.
#  - Write a query to display the table.

# In[16]:


c1 = """
CREATE TABLE IF NOT EXISTS person (
    person_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT
);
"""

c2 = """
INSERT OR IGNORE INTO person
SELECT
    id,
    first,
    last
FROM person_codes;
"""

q = """
SELECT * FROM person
LIMIT 5;
"""

run_command(c1)
run_command(c2)
run_query(q)


# In[17]:


c1 = """
CREATE TABLE IF NOT EXISTS park (
    park_id TEXT PRIMARY KEY,
    name TEXT,
    nickname TEXT,
    city TEXT,
    state TEXT,
    notes TEXT
);
"""

c2 = """
INSERT OR IGNORE INTO park
SELECT
    park_id,
    name,
    aka,
    city,
    state,
    notes
FROM park_codes;
"""

q = """
SELECT * FROM park
LIMIT 5;
"""

run_command(c1)
run_command(c2)
run_query(q)


# In[18]:


c1 = """
CREATE TABLE IF NOT EXISTS league (
    league_id TEXT PRIMARY KEY,
    name TEXT
);
"""

c2 = """
INSERT OR IGNORE INTO league
VALUES
    ("NL", "National League"),
    ("AL", "American League"),
    ("AA", "American Association"),
    ("FL", "Federal League"),
    ("PL", "Players League"),
    ("UA", "Union Association")
;
"""

q = """
SELECT * FROM league
"""

run_command(c1)
run_command(c2)
run_query(q)


# In[19]:


c1 = "DROP TABLE IF EXISTS appearance_type;"

run_command(c1)

c2 = """
CREATE TABLE appearance_type (
    appearance_type_id TEXT PRIMARY KEY,
    name TEXT,
    category TEXT
);
"""
run_command(c2)

appearance_type = pd.read_csv('appearance_type.csv')

with sqlite3.connect('mlb.db') as conn:
    appearance_type.to_sql('appearance_type',
                           conn,
                           index=False,
                           if_exists='append')

q = """
SELECT * FROM appearance_type;
"""

run_query(q)


# ## Adding The Team and Game Tables
# 
# Now that we have added all of the tables that don't have foreign key relationships, lets add the next two tables. The game and team tables need to exist before our two appearance tables are created. Here are the schema of these tables, and the two tables they have foreign key relations to:
# 
# <img src= "https://s3.amazonaws.com/dq-content/193/mlb_schema_2.svg">
# 
# Here are some notes on the normalization choices made with each of these tables:
# 
# - team
#     - The start, end, and sequence columns can be derived from the game level data.
# - game
#     - We have chosen to include all columns for the game log that don't refer to one specific team or player, instead putting those in two appearance tables.
#     - We have removed the column with the day of the week, as this can be derived from the date.
#     - We have changed the day_night column to day, with the intention of making this a boolean column. Even though SQLite doesn't support the BOOLEAN type, we can use this when creating our table and SQLite will manage the underlying types behind the scenes (for more on how this works [refer to the SQLite documentation](https://www.sqlite.org/datatype3.html)). This means that anyone quering the schema of our database in the future understands how that column is intended to be used.
#     
# In an earlier mission, we discussed in passing that by default, SQLite doesn't enforce foreign key relationships. To ensure the integrity of our data, we need to make sure we enable it after each time we create a sqlite3 connection object in python.
# 
# If you are re-using the run_command() function from the earlier project, you can add a single line to enable enforcement of foreign key restraints:
# 
#     def run_command(c):
#         with sqlite3.connect(DB) as conn:
#             conn.execute('PRAGMA foreign_keys = ON;')
#             conn.isolation_level = None
#             conn.execute(c)
# 
# Steps to follow:
# 
# 1. Create the team table with columns, primary key, and foreign key as shown in the schema diagram.
#     - Select the appropriate type based on the data.
#     - Insert the data from the team_codes table.
#     - Write a query to display the first few rows of the table.
# 2. Create the game table with columns, primary key, and foreign key as shown in the schema diagram.
#     - Select the appropriate type based on the data.
#     - Insert the data from the game_log table.
#     - Write a query to display the first few rows of the table.

# In[20]:


c1 = """
CREATE TABLE IF NOT EXISTS team (
    team_id TEXT PRIMARY KEY,
    league_id TEXT,
    city TEXT,
    nickname TEXT,
    franch_id TEXT,
    FOREIGN KEY (league_id) REFERENCES league(league_id)
);
"""

c2 = """
INSERT OR IGNORE INTO team
SELECT
    team_id,
    league,
    city,
    nickname,
    franch_id
FROM team_codes;
"""

q = """
SELECT * FROM team
LIMIT 5;
"""

run_command(c1)
run_command(c2)
run_query(q)


# In[21]:


c1 = """
CREATE TABLE IF NOT EXISTS game (
    game_id TEXT PRIMARY KEY,
    date TEXT,
    number_of_game INTEGER,
    park_id TEXT,
    length_outs INTEGER,
    day BOOLEAN,
    completion TEXT,
    forefeit TEXT,
    protest TEXT,
    attendance INTEGER,
    legnth_minutes INTEGER,
    additional_info TEXT,
    acquisition_info TEXT,
    FOREIGN KEY (park_id) REFERENCES park(park_id)
);
"""

c2 = """
INSERT OR IGNORE INTO game
SELECT
    game_id,
    date,
    number_of_game,
    park_id,
    length_outs,
    CASE
        WHEN day_night = "D" THEN 1
        WHEN day_night = "N" THEN 0
        ELSE NULL
        END
        AS day,
    completion,
    forefeit,
    protest,
    attendance,
    length_minutes,
    additional_info,
    acquisition_info
FROM game_log;
"""

q = """
SELECT * FROM game
LIMIT 5;
"""

run_command(c1)
run_command(c2)
run_query(q)


# ## Adding the Team Appearance Table
# 
# At this point, because we have told SQLite to enforce foreign key constraints and have inserted data that obeys these contraints, we'll get an error if we try to drop a table or delete rows within a table. For example, you might try running DELETE FROM park where park_id = "FOR01";. If you get stuck, one option is to run !rm mlb.db in its own Jupyter cell to delete the database file so you can run all your cells to recreate the database files, tables and data.
# 
# Our next task is to add the team_appearance table. Here is the schema of the table and the three tables it has foreign key relations to:
# <img src="https://s3.amazonaws.com/dq-content/193/mlb_schema_3.svg">
# 
# The team_appearance table has a compound primary key composed of the team name and the game ID. In addition, a boolean column home is used to differentiate between the home and the away team. The rest of the columns are scores or statistics that in our original game log are repeated for each of the home and away teams.
# 
# In order to insert this data cleanly, we'll need to use a UNION clause:
# 
#     INSERT INTO team_appearance
#         SELECT
#             h_name,
#             game_id,
#             1 AS home,
#             h_league,
#             h_score,
#             h_line_score,
#             h_at_bats,
#             [...]
#         FROM game_log
# 
#     UNION
# 
#         SELECT    
#             v_name,
#             game_id,
#             0 AS home,
#             v_league,
#             v_score,
#             v_line_score,
#             v_at_bats,
#             [...]
#         from game_log;
# 
# In order to save yourself from having to manually type all the column names, you might like to use a query like the following to extract the schema from the game_log table, and use that as a starting point for your query:
# 
#     SELECT sql FROM sqlite_master
#     WHERE name = "game_log"
#     AND type = "table";
# 
# Steps to folow:
# 
# 1. Create the team_appearance table with columns, primary key, and foreign keys as shown in the schema diagram.
#     - Select the appropriate type based on the data.
#     - Insert the data from the game_log table, using a UNION clause to combine the data from the column sets for the home and away teams.
#     - Write a query to verify that your data was inserted correctly.

# In[22]:


c1 = """
CREATE TABLE IF NOT EXISTS team_appearance (
    team_id TEXT,
    game_id TEXT,
    home BOOLEAN,
    league_id TEXT,
    score INTEGER,
    line_score TEXT,
    at_bats INTEGER,
    hits INTEGER,
    doubles INTEGER,
    triples INTEGER,
    homeruns INTEGER,
    rbi INTEGER,
    sacrifice_hits INTEGER,
    sacrifice_flies INTEGER,
    hit_by_pitch INTEGER,
    walks INTEGER,
    intentional_walks INTEGER,
    strikeouts INTEGER,
    stolen_bases INTEGER,
    caught_stealing INTEGER,
    grounded_into_double INTEGER,
    first_catcher_interference INTEGER,
    left_on_base INTEGER,
    pitchers_used INTEGER,
    individual_earned_runs INTEGER,
    team_earned_runs INTEGER,
    wild_pitches INTEGER,
    balks INTEGER,
    putouts INTEGER,
    assists INTEGER,
    errors INTEGER,
    passed_balls INTEGER,
    double_plays INTEGER,
    triple_plays INTEGER,
    PRIMARY KEY (team_id, game_id),
    FOREIGN KEY (team_id) REFERENCES team(team_id),
    FOREIGN KEY (game_id) REFERENCES game(game_id),
    FOREIGN KEY (team_id) REFERENCES team(team_id)
);
"""

run_command(c1)

c2 = """
INSERT OR IGNORE INTO team_appearance
    SELECT
        h_name,
        game_id,
        1 AS home,
        h_league,
        h_score,
        h_line_score,
        h_at_bats,
        h_hits,
        h_doubles,
        h_triples,
        h_homeruns,
        h_rbi,
        h_sacrifice_hits,
        h_sacrifice_flies,
        h_hit_by_pitch,
        h_walks,
        h_intentional_walks,
        h_strikeouts,
        h_stolen_bases,
        h_caught_stealing,
        h_grounded_into_double,
        h_first_catcher_interference,
        h_left_on_base,
        h_pitchers_used,
        h_individual_earned_runs,
        h_team_earned_runs,
        h_wild_pitches,
        h_balks,
        h_putouts,
        h_assists,
        h_errors,
        h_passed_balls,
        h_double_plays,
        h_triple_plays
    FROM game_log

UNION

    SELECT    
        v_name,
        game_id,
        0 AS home,
        v_league,
        v_score,
        v_line_score,
        v_at_bats,
        v_hits,
        v_doubles,
        v_triples,
        v_homeruns,
        v_rbi,
        v_sacrifice_hits,
        v_sacrifice_flies,
        v_hit_by_pitch,
        v_walks,
        v_intentional_walks,
        v_strikeouts,
        v_stolen_bases,
        v_caught_stealing,
        v_grounded_into_double,
        v_first_catcher_interference,
        v_left_on_base,
        v_pitchers_used,
        v_individual_earned_runs,
        v_team_earned_runs,
        v_wild_pitches,
        v_balks,
        v_putouts,
        v_assists,
        v_errors,
        v_passed_balls,
        v_double_plays,
        v_triple_plays
    from game_log;
"""

run_command(c2)

q = """
SELECT * FROM team_appearance
WHERE game_id = (
                 SELECT MIN(game_id) from game
                )
   OR game_id = (
                 SELECT MAX(game_id) from game
                )
ORDER By game_id, home;
"""

run_query(q)


# ## Adding the Person Appearance Table
# The final table we need to create is person_appearance. Here is the schema of the table and the four tables it has foreign key relations to:
# <img src="https://s3.amazonaws.com/dq-content/193/mlb_schema_4.svg">
# 
# The person_appearance table will be used to store information on appearances in games by managers, players, and umpires as detailed in the appearance_type table.
# 
# We'll need to use a similar technique to insert data as we used with the team_appearance table, however we will have to write much larger queries - one for each column instead of one for each team as before. We will need to work out for each column what the appearance_type_id will be by cross-referencing the columns with the appearance_type table.
# 
# We have decided to create an integer primary key for this table, because having every column be a compound primary quickly becomes cumbersome when writing queries. In SQLite, if you have an integer primary key and don't specify a value for this column when inserting rows, [SQLite will autoincrement this column for you](https://sqlite.org/autoinc.html).
# 
# Below is an excerpt of the query that we'll write to insert the data:
# 
#     INSERT INTO person_appearance (
#         game_id,
#         team_id,
#         person_id,
#         appearance_type_id
#     )
#         SELECT
#             game_id,
#             NULL,
#             lf_umpire_id,
#             "ULF"
#         FROM game_log
#         WHERE lf_umpire_id IS NOT NULL
# 
#     UNION
# 
#         SELECT
#             game_id,
#             NULL,
#             rf_umpire_id,
#             "URF"
#         FROM game_log
#         WHERE rf_umpire_id IS NOT NULL
# 
#     UNION
# 
#         SELECT
#             game_id,
#             v_name,
#             v_manager_id,
#             "MM"
#         FROM game_log
#         WHERE v_manager_id IS NOT NULL
# 
#     UNION
# 
#         SELECT
#             game_id,
#             h_name,
#             h_manager_id,
#             "MM"
#         FROM game_log
#         WHERE h_manager_id IS NOT NULL
# 
#     UNION
# 
#         SELECT
#             game_id,
#             CASE
#                 WHEN h_score > v_score THEN h_name
#                 ELSE v_name
#                 END,
#             winning_pitcher_id,
#             "AWP"
#         FROM game_log
#         WHERE winning_pitcher_id IS NOT NULL
# 
#     UNION
#         [...]
#         
# When we get to the offensive and defensive positions for both teams, we essentially are performing 36 permutations: 2 (home, away) * 2 (offense + defense) * 9 (9 positions).
# 
# To save us from manually copying this out, we can instead use a loop and [python string formatting](https://pyformat.info/) to generate the queries:
# 
#     template = """
#     INSERT INTO person_appearance (
#         game_id,
#         team_id,
#         person_id,
#         appearance_type_id
#     ) 
#         SELECT
#             game_id,
#             {hv}_name,
#             {hv}_player_{num}_id,
#             "O{num}"
#         FROM game_log
#         WHERE {hv}_player_{num}_id IS NOT NULL
#     UNION
# 
#         SELECT
#             game_id,
#             {hv}_name,
#             {hv}_player_{num}_id,
#             "D" || CAST({hv}_player_{num}_def_pos AS INT)
#         FROM game_log
#         WHERE {hv}_player_{num}_id IS NOT NULL;
#     """
# 
#     run_command(c1)
#     run_command(c2)
# 
#     for hv in ["h","v"]:
#         for num in range(1,10):
#             query_vars = {
#                 "hv": hv,
#                 "num": num
#             }
#              '#'run commmand is a helper function which runs
#              '#'a query against our database.
#             run_command(template.format(**query_vars))
#             
# Note that when you get to the umpire columns you will have to enclose them in square brackets, ie [1b_umpire_id] instead of 1b_umpire_id. This is because SQL will try an interpret any token starting with a numeric character as a number - using the square brackets is SQL version of putting the column name in quotes.
# 
# Steps to follow:
# 
# 1. Create the person_appearance table with columns, primary key, and foreign keys as shown in the schema diagram.
#     - Select the appropriate type based on the data.
#     - Insert the data from the game_log table, using UNION clauses to combine the data from the columns for managers, umpires, pitchers, and awards.
#     - Use a loop with string formatting to insert the data for offensive and defensive positions from the game_log table.
#     - Write a query to verify that your data was inserted correctly.

# In[23]:


c0 = "DROP TABLE IF EXISTS person_appearance"

run_command(c0)

c1 = """
CREATE TABLE person_appearance (
    appearance_id INTEGER PRIMARY KEY,
    person_id TEXT,
    team_id TEXT,
    game_id TEXT,
    appearance_type_id,
    FOREIGN KEY (person_id) REFERENCES person(person_id),
    FOREIGN KEY (team_id) REFERENCES team(team_id),
    FOREIGN KEY (game_id) REFERENCES game(game_id),
    FOREIGN KEY (appearance_type_id) REFERENCES appearance_type(appearance_type_id)
);
"""

c2 = """
INSERT OR IGNORE INTO person_appearance (
    game_id,
    team_id,
    person_id,
    appearance_type_id
) 
    SELECT
        game_id,
        NULL,
        hp_umpire_id,
        "UHP"
    FROM game_log
    WHERE hp_umpire_id IS NOT NULL    

UNION

    SELECT
        game_id,
        NULL,
        [1b_umpire_id],
        "U1B"
    FROM game_log
    WHERE "1b_umpire_id" IS NOT NULL

UNION

    SELECT
        game_id,
        NULL,
        [2b_umpire_id],
        "U2B"
    FROM game_log
    WHERE [2b_umpire_id] IS NOT NULL

UNION

    SELECT
        game_id,
        NULL,
        [3b_umpire_id],
        "U3B"
    FROM game_log
    WHERE [3b_umpire_id] IS NOT NULL

UNION

    SELECT
        game_id,
        NULL,
        lf_umpire_id,
        "ULF"
    FROM game_log
    WHERE lf_umpire_id IS NOT NULL

UNION

    SELECT
        game_id,
        NULL,
        rf_umpire_id,
        "URF"
    FROM game_log
    WHERE rf_umpire_id IS NOT NULL

UNION

    SELECT
        game_id,
        v_name,
        v_manager_id,
        "MM"
    FROM game_log
    WHERE v_manager_id IS NOT NULL

UNION

    SELECT
        game_id,
        h_name,
        h_manager_id,
        "MM"
    FROM game_log
    WHERE h_manager_id IS NOT NULL

UNION

    SELECT
        game_id,
        CASE
            WHEN h_score > v_score THEN h_name
            ELSE v_name
            END,
        winning_pitcher_id,
        "AWP"
    FROM game_log
    WHERE winning_pitcher_id IS NOT NULL

UNION

    SELECT
        game_id,
        CASE
            WHEN h_score < v_score THEN h_name
            ELSE v_name
            END,
        losing_pitcher_id,
        "ALP"
    FROM game_log
    WHERE losing_pitcher_id IS NOT NULL

UNION

    SELECT
        game_id,
        CASE
            WHEN h_score > v_score THEN h_name
            ELSE v_name
            END,
        saving_pitcher_id,
        "ASP"
    FROM game_log
    WHERE saving_pitcher_id IS NOT NULL

UNION

    SELECT
        game_id,
        CASE
            WHEN h_score > v_score THEN h_name
            ELSE v_name
            END,
        winning_rbi_batter_id,
        "AWB"
    FROM game_log
    WHERE winning_rbi_batter_id IS NOT NULL

UNION

    SELECT
        game_id,
        v_name,
        v_starting_pitcher_id,
        "PSP"
    FROM game_log
    WHERE v_starting_pitcher_id IS NOT NULL

UNION

    SELECT
        game_id,
        h_name,
        h_starting_pitcher_id,
        "PSP"
    FROM game_log
    WHERE h_starting_pitcher_id IS NOT NULL;
"""

template = """
INSERT INTO person_appearance (
    game_id,
    team_id,
    person_id,
    appearance_type_id
) 
    SELECT
        game_id,
        {hv}_name,
        {hv}_player_{num}_id,
        "O{num}"
    FROM game_log
    WHERE {hv}_player_{num}_id IS NOT NULL

UNION

    SELECT
        game_id,
        {hv}_name,
        {hv}_player_{num}_id,
        "D" || CAST({hv}_player_{num}_def_pos AS INT)
    FROM game_log
    WHERE {hv}_player_{num}_id IS NOT NULL;
"""

run_command(c1)
run_command(c2)

for hv in ["h","v"]:
    for num in range(1,10):
        query_vars = {
            "hv": hv,
            "num": num
        }
        run_command(template.format(**query_vars))


# In[24]:


print(run_query("SELECT COUNT(DISTINCT game_id) games_game FROM game"))
print(run_query("SELECT COUNT(DISTINCT game_id) games_person_appearance FROM person_appearance"))

q = """
SELECT
    pa.*,
    at.name,
    at.category
FROM person_appearance pa
INNER JOIN appearance_type at on at.appearance_type_id = pa.appearance_type_id
WHERE PA.game_id = (
                   SELECT max(game_id)
                    FROM person_appearance
                   )
ORDER BY team_id, appearance_type_id
"""

run_query(q)


# ## Removing the Original Tables
# 
# We've now created all normalized tables and inserted all of our data!.
# Our last task is to remove the tables we created to import the original CSVs.
# 
# 1. Drop the tables we created to hold our unnormalized data:
#     - game_log.
#     - park_codes.
#     - team_codes.
#     - person_codes.

# In[25]:


show_tables()


# In[26]:


tables = [
    "game_log",
    "park_codes",
    "team_codes",
    "person_codes"
]

for t in tables:
    c = '''
    DROP TABLE {}
    '''.format(t)
    
    run_command(c)

show_tables()


# In this mission, we learned how to:
# 
# - Import CSV data into a database.
# - Design a normalized schema for a large, predominantly single table data set.
# - Create tables that match the schema design.
# - Migrate data from unnormalized tables into our normalized tables.
# 
# To extend this project, you might like to consider one or more of the following:
# 
# - Transform the the dates into a SQLite compatible format.
# - Extract the line scores into innings level data in a new table.
# - Create views to make querying stats easier, eg:
#     - Season level stats.
#     - All time records.
# - Supplement the database using new data, for instance:
#     - Add data from retrosheet game logs for years after 2016.
#     - Source and add missing pitcher information.
#     - Add player level per-game stats.
#     - Source and include base coach data.
