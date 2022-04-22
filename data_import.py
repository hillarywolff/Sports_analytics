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

event_types = ['start of period', 'end of period', 'sub', 'timeout', 'unknown']

df = df[df['event_type'].str.contains('|'.join(event_types))==False]
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



################################################################
# create dummies for turnover and final free throw made

df['turnover'] = np.where(df['event_type'].str.contains('turnover'), 1, 0)

conditions = [
    df['event_type'].eq('free throw') & df['result'].eq('made') & df['description'].eq('Free Throw 1 of 1'),
    df['event_type'].eq('free throw') & df['result'].eq('made') & df['description'].eq('Free Throw 2 of 2'),
    df['event_type'].eq('free throw') & df['result'].eq('made') & df['description'].eq('Free Throw 3 of 3')
    ]

choices = [1, 1, 1]

df['final ft made'] = np.select(conditions, choices, default=0)

#############################################################
# dummies for made basket without extra point
# dummies for made basket with extra point? 

# sum possession changes across types: made basket with no and one + final free throw made

df['points'].unique()

conditions = [
    df['points'].eq(2) & df['reason'].ne('s.foul'), 
    df['points'].eq(3) & df['reason'].ne('s.foul')
    ]

choices = [1, 1]
df['basket, no foul'] = np.select(conditions, choices, default=0)




conditions = [
    df['points'].eq(2) & df['reason'].eq('s.foul'), 
    df['points'].eq(3) & df['reason'].eq('s.foul')
    ]

choices = [1, 1]
df['basket, foul'] = np.select(conditions, choices, default=0)

df['sum possession changes'] = df['basket, no foul'] + df['final ft made']



df = df.sort_values(by=['game_id'])
###############################################################
df['game_id'] = df['game_id'].str.replace('(\D+)', '')

df['game_id'].unique()

# df1['end'] = df1.drop_duplicates(subset = ['record', 'start'])['start']\
#    .shift(-1).reindex(index = df1.index, method = 'ffill')


# MISSING: missed shot rebounded by opposing team
# if event type is rebound and team in row one != team in row two

# MISSING: potential possession number within game
# first row of game = 1, second is row 1 + row 2 sum possession



































