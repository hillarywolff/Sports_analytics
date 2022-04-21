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

team_crosswalk['team name'] = team_crosswalk['team name'].str.lower()
team_crosswalk = team_crosswalk.set_index('team name').T
team_crosswalk = team_crosswalk.to_dict('list')

blank_df['team'] = blank_df['team_separate'].map(team_crosswalk)

blank_df['team']= blank_df['team'].str.strip()



# df_blank = df[df['event_type'].str.contains('rebound')]

# df_blank = df_blank[df_blank['team']==0]
i = df[~df['team']==0]
i = list(i)
df = df.drop(df.index[[i]])

# create crosswalk for team name and abbreviations to map over the team col




df_blank['team_test'] = df_blank['description']
df_blank['team_test'] = df_blank['team_test'].str.lower()
df_blank['team_test'] = df_blank['team_test'].apply(separate_team)
# successfully separated team name from 'rebound'


crosswalk = pd.read_csv("/Users/hillarywolff/Desktop/nba_crosswalk.csv")

team_crosswalk = crosswalk
team_crosswalk['team'] = team_crosswalk['team'].str.strip()
team_crosswalk['team_name'] = team_crosswalk['team_name'].str.lower()
team_crosswalk = team_crosswalk.set_index('team_name').T
team_crosswalk = team_crosswalk.to_dict('list')

df_blank['team'] = df_blank['team_test'].map(team_crosswalk)

df_blank = df_blank.drop('team_test', axis=1)


df = pd.concat([df, df_blank])
df['team'].unique
################################################################

df.columns


df_FT = df[df['event_type'].str.contains('free throw')]

df_FT['FIX'] = np.where((df_FT['points'] > 1), 1, 0) 
df_FT['FIX_2'] = np.where((df_FT['points'] ==0) & (df_FT['result'].str.contains('made')), 1, 0)


def blah(x):
    if x > 0:
        return '1'
    else:
        return x
    
df_FT['point_fix'] = df_FT['FIX'] + df_FT['FIX_2']
df_FT['points'] = df_FT['point_fix'].apply(blah)    

test_subset = df_FT[df_FT['point_fix'] > 0]


    
# for 

# def filter_race(x):
#     if x in black_list:
#         return 'Black'
#     elif x in (native_american_PI):
#         return 'Native American or Pacific Islander'
#     elif x in (asian_list):
#         return 'Asian'
#     elif x in (white_list):
#         return 'White'
#     elif x in (mid_east):
#         return 'Middle Eastern/Arab'
#     else:
#         return 'Other/Unknown'

# df['filter_patient_race'] = df['patient_race'].apply(filter_race)


#df_FT['FIX_2'] = np.where((df_FT['points'] ==0) & (df_FT['result'].str.contains('made')), 1, 0)

def fix_points(x):
    if x == 1: 
        return x == 1
    elif x ==1:
        return x ==1

df_FT['points'] = df_FT['points'].apply(fix_points)

#############################################################

# create a column with dummies for made basket but no s.foul (and one)
# -points = 2 & no s.foul, points =3 & no s.foul, 

# points = 2 & s.foul & team1=team2 (did not change posssion)
# points = 3 & s.foul & team1=team2
# df['points'], df['reason'], df['team']

def idk(points, reason, team):
    if points == (2|3) and ((reason.str.contains('s.foul')) == False):
        return 1
    elif points == (2|3) and reason.str.contains('s.foul') and team.str.contains(f'{team}'): 
        return 1
    else:
        return 0
    
        
# 
# column with dummies for TO
# column with dummies for missed shot rebounded by opposing team
# column with dummies if final free throw made (1 of 1, 2 of 2, 3 of 3)
# 











































