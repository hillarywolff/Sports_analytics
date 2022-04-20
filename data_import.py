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
    df.append(csv)


big_ass_df = pd.concat(df)

big_ass_df.columns

df = big_ass_df
####################################################################


df['event_type'].unique()
event_types = ['start of period', 'end of period', 'sub', 'timeout', 'unknown']

df = df[df['event_type'].str.contains('|'.join(event_types))==False]

df = df.fillna(0)
df_blank = df[df['event_type'].str.contains('rebound')]

df_blank = df_blank[df_blank['team']==0]
df_blank.head()
# create crosswalk for team name and abbreviations to map over the team col


crosswalk = pd.read_csv("/Users/hillarywolff/Desktop/nba_crosswalk.csv")

# if df_blank[description]str.contains(crosswalk['team_name'], df[team]replace(crosswalk[team])

def separate_team(x):
    if search(r'rebound', x):
        return x.split(' ')[0]



df_blank['team_test'] = df_blank['description']
df_blank['team_test'] = df_blank['team_test'].str.lower()
df_blank['team_test'] = df_blank['team_test'].apply(separate_team)
# successfully separated team name from 'rebound'



team_crosswalk = crosswalk
team_crosswalk['team'] = team_crosswalk['team'].str.strip()
team_crosswalk['team_name'] = team_crosswalk['team_name'].str.lower()
team_crosswalk = team_crosswalk.set_index('team_name').T
team_crosswalk = team_crosswalk.to_dict('list')

df_blank['team'] = df_blank['team_test'].map(team_crosswalk)
df_blank['team']

df_blank = df_blank.drop('team_test', axis=1)


df = pd.concat([df, df_blank])














