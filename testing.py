#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 26 18:25:42 2022

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



df = []
for f in all_files:
    csv = pd.read_csv(f, usecols=fields)
    df.append(csv)
    

df = pd.concat(df)
reset_df = df




event_types = ['start of period', 'end of period', 'sub', 'timeout', 'unknown', 'ejection', 'nan']
df = df[df['event_type'].str.contains('|'.join(event_types))==False]

type_remove = ['Free Throw Technical', 'Free Throw Clear Path 1 of 2',
               'Free Throw Clear Path 2 of 2', 'Free Throw Flagrant 1 of 1', 
               'Free Throw Flagrant 1 of 1', 'Free Throw Flagrant 1 of 2',
               'Free Throw Flagrant 1 of 3', 'Free Throw Flagrant 2 of 2',
               'Free Throw Flagrant 2 of 3', 'Free Throw Flagrant 3 of 3', 
               'FLAGRANT.FOUL.TYPE']

type_remove = ' '.join(type_remove)

def tech_remove(x):
    if x in type_remove:
        return 1
    else:
        return 0

df['type_remove'] = df['type'].apply(tech_remove)
df['type_remove'].sum()

df = df.fillna(' ')
    
def description_remove(x):
    if search (r' T.FOUL', x):
        return 1
    elif search (r' t.foul', x):
        return 1
    elif search (r' hanging.tech.foul', x):
        return 1
    elif search (r' HANGING.TECH.FOUL', x):
        return 1
    elif search (r' c.p.foul', x):
        return 1
    elif search (r' C.P.FOUL', x):
        return 1
        
df['description_remove'] = df['description'].apply(description_remove)   
df['description_remove'].sum()


desc_df = df[df['description_remove']]

new_df = df[df['type'].str.contains('team rebound')]
# 22 cpfoul
# 706 t.foul
# 4 hanging

# 316 free throw flagrant
# 86 clear path
# 1247 technical



df = df[df['type'].str.contains('/'.join(type_remove))==False]
test = df[~df.type.str.contains(type_remove)]
test_2 = df[~df['type'].isin([type_remove])]

types = test['type'].unique()


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
team_crosswalk['team name'] = team_crosswalk['team name'].str.lower()
team_crosswalk = team_crosswalk.set_index('team name').T
team_crosswalk = team_crosswalk.to_dict('list')



blank_df['team'] = blank_df['team_separate'].map(team_crosswalk)
blank_df = blank_df.drop('team_separate', axis=1)


ft_df = df[df['event_type'].str.contains('free throw')]

ft_df['points'] = np.where((ft_df['result'] == 'made'), 1, 0)

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
df['team'] = df['team'].str.replace('(\W)', '')
df['event_type'] = df['event_type'].replace({'miss':'shot'})

df = df.sort_values(by=['game_id', 'period', 'elapsed'])
df.drop_duplicates(inplace=True, ignore_index=False)

df['second_chance'] = np.where((df['type'].eq('rebound offensive')) |
                               (df['type'].eq('team rebound')), 1, 0)
df['second_chance'].sum()
# a. made basket, no foul
conditions = [
    df['points'].eq(2) & # shift next row
    df.shift(1)['reason'].ne('s.foul'), 
    df['points'].eq(3) & # shift next row
    df.shift(1)['reason'].ne('s.foul'),
    df['type'].eq('violation:defensive goaltending')
    ]

choices = [1, 1, 1]
df['made basket, no foul'] = np.select(conditions, choices, default=0)

# b. turnover
df['turnover'] = np.where(df['event_type'].str.contains('turnover'), 1, 0)

# c. missed shot rebounded by opposing team
conditions = [
    df['event_type'].eq('rebound') & df['team'].ne(df.shift(1)['team'])
    ]

choices = [1]
df['def_rebound'] = np.select(conditions, choices, default=0)

# d. 
# final free throw made
conditions = [
    df['event_type'].eq('free throw') & df['result'].eq('made') & df['type'].eq('Free Throw 1 of 1'),
    df['event_type'].eq('free throw') & df['result'].eq('made') & df['type'].eq('Free Throw 2 of 2'),
    df['event_type'].eq('free throw') & df['result'].eq('made') & df['type'].eq('Free Throw 3 of 3')
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


# violation
df['off_violation'] = np.where((df['event_type'].eq('violation')) & 
                          (df['team'].ne(df.shift(1)['team'])), 1, 0)
# offensive foul
df['off_foul'] = np.where((df['event_type'].eq('foul') & (df['reason'].eq('off.foul'))), 1, 0)

# f. 
df['possession change'] = np.where((df['made basket, no foul']==1) |
                                   (df['turnover']==1) |
                                   (df['def_rebound'] ==1)|
                                   (df['final ft made']==1) |
                                   (df['off_violation']==1) |
                                   (df['off_foul']), 1, 0)
#df = df.drop('possession_number', axis=1)

df['new_game'] = np.where((df['game_id'].ne(df.shift(1)['game_id'])), 1, 0)

# get possession number within game
df['game_possession_number'] = df.groupby(df['new_game'].eq(1).cumsum())['possession change'].cumsum()
df['season_possession_number'] = df.groupby('new_game')['possession change'].cumsum()



































