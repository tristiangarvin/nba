import pandas as pd

shots = pd.read_csv('shot-chart.csv')
box_score = pd.read_csv('box-score.csv')

df  = pd.merge(left=shots, right=box_score, on=['Player_ID','Game_ID'], how='inner')

df.to_csv('data.csv', sep=',', index=False)


