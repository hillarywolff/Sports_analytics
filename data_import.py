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


####################################################################

def clean_df(df):

    event_types = ['start of period', 'end of period', 'sub', 'timeout', 'unknown', 'ejection', 'nan']
    df = df[df['event_type'].str.contains('|'.join(event_types))==False]
    
    
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
    
    return df

# second chance/off rebounds:
    
def create_dummies(df):
    
    df['second_chance'] = np.where((df['type'].eq('rebound offensive')) |
                                   (df['type'].eq('team rebound')), 1, 0)
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

    return df

###########################################################################
###########################################################################


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


clean_df = clean_df(big_ass_df)
dummy_df = create_dummies(clean_df)



dummy_df['season_possession_number'].max()


# h. unique possession identifier

# string concat game id,  possession number

# how many total unique possessions are in this dataset?
# how many total points are in this dataset?
# how many total possessions per turnover type

turnover_cols = ['made basket, no foul', 'turnover', 'def_rebound', 'final ft made', 'off_foul', 'off_violation']


# 2019-20 team # of plays that start in each turnover

# made basket, no foul    121,121
# turnover                 43,178
# def_rebound             127,798
# final ft made            286,56
# off_violation             1,653
# off_foul                  2,908 <- double counted in turnover

# total possessions       243,769
# total forced TO         173,884
# total points            331,332

test = dummy_df[dummy_df['season_possession_number'].unique()]

dummy_df['season_possession_number'].unique()

total_poss = dummy_df['season_possession_number'].max()
total_points = dummy_df['points'].sum()
made_basket = dummy_df['made basket, no foul'].sum()
turnover = dummy_df['turnover'].sum()
def_reb = dummy_df['def_rebound'].sum()
final_ft = dummy_df['final ft made'].sum()
off_viol = dummy_df['off_foul'].sum()
total_turnover = turnover + def_reb +  off_viol

turnover+def_reb+off_viol

pp_p = total_points/total_poss
pp_FTO = total_points/total_turnover
pp_dfrb = total_points/def_reb
pp_offviol = total_points/off_viol



# dummy_df.to_csv(r"/Users/hillarywolff/Desktop/possession_indicator.csv")

# j. extended description

# if df.shift(1)['period'].ne(df['period']) return 'new quarter'
# if df.shift(1)['unique possession id'].ne(df['unique possession id']), concat df['event_type'], df['type']
# else, df['extended description of start of possession']


# what does the turnouver do in the posession that it occurs
# what does the turnover do to the next possession
# what does the utrnover do two possessions down the road


# chance level data: dummy for offensive rebound within possession








