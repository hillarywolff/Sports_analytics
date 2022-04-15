#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 14 19:20:31 2022

@author: hillarywolff
"""
import pandas as pd
import glob


PATH = r"/Users/hillarywolff/Desktop/basketball_data"
all_files = glob.glob(PATH+ "/*.csv")


fields = ['game_id', 'data_set', 'team', 'period', 'away_score', 'home_score', 
          'remaining_time','elapsed', 'event_type', 'points', 'reason', 
          'result', 'steal', 'type', 'description']

big_ass_df = pd.DataFrame()

df = []
for f in all_files:
    csv = pd.read_csv(f, usecols=fields)
    df.append(csv)


big_ass_df = pd.concat(df)

big_ass_df.to_csv(r'/Users/hillarywolff/Desktop/2019-2020_data.csv')



















