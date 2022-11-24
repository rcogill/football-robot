"""
This module pulls NFL score data, models teams' offensive and defensive
strength and predicts scores for all upcoming games in the current season.
"""

import pandas as pd
import numpy as np

#===============================================================

def pull_score_data():
    """
    This function pulls the NFL schedule and score history from the
    current and previous seasons.
    """

    all_df = pd.read_html(
        'https://www.pro-football-reference.com/years/2022/games.htm'
    )
    df = all_df[0][['Date','Week','Winner/tie','Loser/tie','PtsW','PtsL']]

    #---------------
    # Include past season's data for first weeks

    all_df = pd.read_html(
        'https://www.pro-football-reference.com/years/2021/games.htm'
    )
    df_past = all_df[0][['Date','Week','Winner/tie','Loser/tie','PtsW','PtsL']]

    df_past = df_past.dropna()
    df_past = df_past[df_past['Week'].str.isdigit()]

    # Get max week of current season
    weeks = df.dropna()['Week'].unique()
    max_week = max([int(x) for x in weeks if x.isdigit()])

    #Ensure we have at least five weeks of data
    df_past = df_past[df_past['Week'].astype(int) >= 13+max_week]

    #---------------

    return df.append(df_past)

#===============================================================

def get_future_frame(df_scores):
    """
    This function extracts the schedule of unplayed games from
    the current NLF season.
    """

    df_future = df_scores[df_scores['Week'] != 'Week']
    df_future = df_future[df_future['Week'] == df_future['Week']]
    df_future = df_future[df_future['PtsW'] != df_future['PtsW']]
    df_future = df_future.rename(
        columns={
            'Winner/tie':'Away',
            'Loser/tie':'Home',
            'PtsW':'Predicted Pts - Away',
            'PtsL':'Predicted Pts - Home'
            }
    )
    #---
    return df_future

#===============================================================

def model_teams(df_scores):
    """
    This function computes the current offfensive and defensive strength
    factors for each team using the simple regularized linear regression
    model described in README.md.
    """

    teams = list(df_scores['Winner/tie'])
    teams = teams + list(df_scores['Loser/tie'])
    teams = [
        x for x in list(set(teams)) \
        if x == x \
        and x != 'Winner/tie' \
        and x != 'Loser/tie' \
        and x != 'Home' \
        and x != "Visitor"
    ]

    team_dict = {}
    for i in range(0,len(teams)):
        team_dict[teams[i]] = i

    #----

    X = []
    for row in df_scores[['Winner/tie','Loser/tie','PtsW','PtsL']].values:
        try:
            idx_w = team_dict[row[0]]
            idx_l = team_dict[row[1]]
            pts_w = int(row[2])
            pts_l = int(row[3])
            #---
            x_row = [0]*(2*len(team_dict))
            x_row[idx_w] = 1
            x_row[len(team_dict)+idx_l] = -1*pts_w
            X.append(x_row)
            #---
            x_row = [0]*(2*len(team_dict))
            x_row[idx_l] = 1
            x_row[len(team_dict)+idx_w] = -1*pts_l
            X.append(x_row)
        except:
            # TO DO: log failures
            None

    #--------

    X = np.matrix(X)
    r = [0]*len(team_dict) + [1]*len(team_dict)
    r = np.matrix(r).T
    z = (X.T*X).I*r
    c = float((r.T*r)/(r.T*z))*z

    return (team_dict,c)

#===============================================================

def round_score(mu):
    """
    This function rounds a raw predicted score to produce a more
    plausible football score, as described in README.md.
    """

    m = 7*int(0.8*mu/7) + 3*int(0.2*mu/3)
    diff = mu - m
    if diff <= 1.5:
        return m
    if diff <= 5.0:
        return m+3
    if diff <= 8.5:
        return m+7
    return m+10

#===============================================================

def forecast_scores(team1,team2,team_dict,params):
    """
    This function produces forecasted scores resulting from
    a matchup between team1 and team2.
    """

    idx_1 = team_dict[team1]
    idx_2 = team_dict[team2]

    mu1 = params[idx_1]/params[len(team_dict)+idx_2]
    score1 = round_score(mu1)

    mu2 = params[idx_2]/params[len(team_dict)+idx_1]
    score2 = round_score(mu2)

    # If a tie is predicted, adjust to have a winner
    if score1 == score2:
        if mu1 > mu2:
            score1 += 3
        else:
            score2 += 3

    return (score1,score2)

#===============================================================

def get_team_frame(team_dict,params):
    """
    This function produces a dataframe containing the
    offensive and defensive strength factors for each team.
    """

    df_teams = pd.DataFrame()

    for team in team_dict:

        idx_1 = team_dict[team]
        offense = float(params[idx_1])
        defense = float(params[len(team_dict)+idx_1])

        df_teams = pd.concat(
            [
                df_teams,
                pd.DataFrame([[team,offense,defense]])
            ]
        )

    df_teams.columns = ['Team','Offense','Defense']

    return df_teams
