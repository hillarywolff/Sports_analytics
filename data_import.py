#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 14 19:20:31 2022

@author: hillarywolff
"""
import pandas as pd
import glob
import numpy as np
from re import search

PATH = r"/Users/hillarywolff/Desktop/basketball_data/"
all_files = glob.glob(PATH+ "*.csv")


fields = ['game_id', 'data_set', 'team', 'period', 'away_score', 'home_score', 
          'remaining_time','elapsed', 'play_length', 'play_id', 'event_type', 'points', 'reason', 
          'result', 'steal', 'type', 'description']

big_ass_df = pd.DataFrame()

df = []
for f in all_files:
    csv = pd.read_csv(f, usecols=fields)
    # do all data processing here
    df.append(csv)


big_ass_df = pd.concat(df)


df = big_ass_df
####################################################################

event_types = ['start of period', 'end of period', 'sub', 'timeout', 'unknown', 'ejection', 'nan']
df = df[df['event_type'].str.contains('|'.join(event_types))==False]

# remove rows: 
# where type = t.foul, c.p.foul, free throw technical, free throw clear path 1 of 2, 
# free throw clear path 2 of 2, free throw flagrant 1 of 1, free throw flagrant 1 of 2, 
# free throw flagrant 1 of 3, free throw flagrant 2 of 2, free throw flagrant 2 of 3, 
# free throw flagrant 3 of 3, **and 1 baskets**?
# 
# where type = team rebound and above dummy = 1

type_remove = ['t.foul', 'c.p.foul', 'Free Throw Technical', 'Free Throw Clear Path 1 of 2',
               'Free Throw Clear Path 2 of 2', 'Free Throw Flagrant 1 of 1', 
               'Free Throw Flagrant 1 of 1', 'Free Throw Flagrant 1 of 2',
               'Free Throw Flagrant 1 of 3', 'Free Throw Flagrant 2 of 2',
               'Free Throw Flagrant 2 of 3', 'Free Throw Flagrant 3 of 3']

df = df[df['type'].str.contains('/'.join(type_remove))==False]


df = df.fillna(0)


# create new df where team = 0
def separate_team(x):
    if search(r' ', x):
        return x.split(' ')[0]
    
blank_df = df[df['team']==0]
blank_df = blank_df[blank_df['description']!=0]
blank_df['description'] = blank_df['description'].str.lower()
blank_df['team_separate'] = blank_df['description'].apply(separate_team)

# NEED TO REPLACE JUMP BALL TEAM NAME

crosswalk = pd.read_csv("/Users/hillarywolff/Desktop/nba_crosswalk.csv")
team_crosswalk = crosswalk
team_crosswalk.columns
team_crosswalk['team'] = team_crosswalk['team'].str.strip()
team_crosswalk['team name'] = team_crosswalk['team name'].str.lower()
team_crosswalk = team_crosswalk.set_index('team name').T
team_crosswalk = team_crosswalk.to_dict('list')

blank_df['team'] = blank_df['team_separate'].map(team_crosswalk)
blank_df = blank_df.drop('team_separate', axis=1)


ft_df = df[df['event_type'].str.contains('free throw')]

ft_df['points'] = np.where((ft_df['result'] == 'made'), 1, 0)


# need to delete places from main df that were fixed in two side dfs
# create a dummy to indicate which rows were fixed? 
# dummy = 1 where team name = 0 or where event type = ft and result = made and points != 1

conditions = [
    df['event_type'].eq('free throw') & df['result'].eq('made') & df['points'].ne(1),
    df['team'].eq(0)
]

choices = [1, 1]

df['remove'] = np.select(conditions, choices, default=0)

df = df[df.remove == 0]
# dropped rows where other dfs fixed

df = pd.concat([df, blank_df, ft_df])
df = df.drop('remove', axis=1)
# remove unnecessary col

################################################################
###############################################################
df['game_id'] = df['game_id'].str.replace('(\D+)', '')
df = df.sort_values(by=['game_id', 'period', 'elapsed'])


# a. made basket, no and 1
conditions = [
    df['points'].eq(2) & # shift next row
    df.shift(1)['reason'].ne('s.foul'), 
    df['points'].eq(3) & # shift next row
    df.shift(1)['reason'].ne('s.foul'),
    df['type'].eq('violation:defensive goaltending')
    ]

choices = [1, 1, 1]
df['basket, no foul'] = np.select(conditions, choices, default=0)

# b. turnover
df['turnover'] = np.where(df['event_type'].str.contains('turnover'), 1, 0)

# c. missed shot rebounded by opposing team
conditions = [
    df['type'].eq('rebound') & df['team'].ne(df.shift(1)['team'])
    ]

choices = [1]
df['missed_shot_rebound'] = np.select(conditions, choices, default=0)

# d. 
# final free throw made
conditions = [
    df['event_type'].eq('free throw') & df['result'].eq('made') & df['description'].eq('Free Throw 1 of 1'),
    df['event_type'].eq('free throw') & df['result'].eq('made') & df['description'].eq('Free Throw 2 of 2'),
    df['event_type'].eq('free throw') & df['result'].eq('made') & df['description'].eq('Free Throw 3 of 3')
    ]
choices = [1, 1, 1]
df['final ft made'] = np.select(conditions, choices, default=0)

# e. 
# first posession of new quarter
conditions = [
    df.shift(1)['period'].ne(df['period'])
    ]
choices = [1]
df['first poss of qt'] = np.select(conditions, choices, default=0)

# f. 
df['possession change'] = np.where((df['basket, no foul']==1) |
                                   (df['turnover']==1) |
                                   (df['missed_shot_rebound'] ==1)|
                                   (df['final ft made']==1), 1, 0)

# creates dummy to indicate there is a change in possession
# use this to determine play number 


# g. 
# MISSING: potential possession number within game
# first row of game = 1, second is row 1 + row 2 sum possession

# df['potential possession number'] = df.shift(1, fill_value=1)['sum possession changes'] + df['sum possession changes']

    
# if df.shift(2)['game_id'].eq(df.shift(1)['game_id']):
#     df['potential possession num'] = df.shift(1)['potential possession number'] + df.shift(2)['sum possession changes']
    

# h. unique possession identifier
# string concat game id, potential possession number


# i. indication of start of new possession

# if df.shift(1)['period'].ne(df['period']) return 'new quarter'
# if df.shift(1)['unique possession id'].ne(df['unique possession id']), df['event_type'], df['indication of start of possession']

# j. extended description

# if df.shift(1)['period'].ne(df['period']) return 'new quarter'
# if df.shift(1)['unique possession id'].ne(df['unique possession id']), concat df['event_type'], df['type']
# else, df['extended description of start of possession']



# ** not seeing any mention of 'hanging.tech.foul'**

# new possession level df
poss_df = df[df['possession change']==1]
poss_df['poss number'] = range(len(poss_df))

# if df.shift(1)['game_id'].eq(df['game_id']):
#     poss_df['poss number'] = range(len(poss_df))
# elif df.shift(1)['game_id'].ne(df['game_id']):
#     poss_df['poss number'] # restart numbering


#m=df['game_id'].ne(df.shift(1)['game_id'])
#df['poss number'] = np.where(m, df.groupby(m.ne(m.shift()).cumsum()).cumcount()+1, 0)

poss_df['poss number'].max()
# 257,775 possessions 

# if sum possession change != 1 , return nan
# elif sum possession change.eq(1) & game_id.eq(shift(1)game_id), return n+1 (where n = np.where(closest value >0))
# elif sum possession change.eq(1) & game_id.ne(shift(1)game_id), return 0


# anchor = 5
# dists = anchor - nonzeros
# anchor = 5
# dists = anchor - nonzeros
# nhops = min(dists, key=abs)
# hnops = min((anchor - df[df.A != 0].index), key=abs)

# what does the turnouver do in the posession that it occurs
# what does the turnover do to the next possession
# what does the utrnover do two possessions down the road

test = df[['team', 'possession change']]
# need to check if shift is doing what i want



# chance level data: dummy for offensive rebound within possession








