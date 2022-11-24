"""
This script implements the AWS lambda function that:
- Pulls up-to-date NFL scores for the current season
- Models teams' offensive and defensive strength from current
  season performance.
- Produces predicted scores for all upcoming game in the current season.
- Re-writes the static website source containing predictions
- Archives historical scores, team ratings, and predictions in S3.
"""

from io import StringIO
from datetime import datetime
import boto3

import predict as pr

#===============================================================

def store_outputs(s3_resource, df, prefix, date):
    """
    This function archives a given dataframe in S3 for later analysis.
    """

    data = StringIO()
    df.to_csv(data, index=False)
    key = '{}/run_date={}/{}.csv'.format(prefix, date, prefix)
    s3_resource.Bucket('football-robot-data').put_object(Key=key, Body=data.getvalue())

    return True

#===============================================================

def generate_template(df_pred):
    """
    This function generates the static source for the
    football-robot.com website, given a dataframe containing
    current predictions.
    """

    with open('template.html', 'r', encoding='utf8') as f:
        template = f.read()

    return template.format(table=df_pred.to_html(index=False, table_id="scores"))

#===============================================================

def lambda_handler(event, context):
    """
    This function implements the lambda function handler
    that is invoked daily to update predictions.
    """

    df_scores = pr.pull_score_data()

    (team_dict, params) = pr.model_teams(df_scores)

    df_team = pr.get_team_frame(team_dict, params)
    df_team['Rating'] = df_team.apply(
        lambda x: x['Offense']*x['Defense'],
        axis=1
    )

    df_f = pr.get_future_frame(df_scores)

    df_f['Predicted Pts - Away'] = df_f.apply(
        lambda x: pr.forecast_scores(x['Away'], x['Home'], team_dict, params)[0],
        axis=1
    )
    df_f['Predicted Pts - Home'] = df_f.apply(
        lambda x: pr.forecast_scores(x['Away'], x['Home'], team_dict, params)[1],
        axis=1
    )

    #---

    s3 = boto3.resource('s3')

    # Store backup date
    date = datetime.now().strftime('%Y-%m-%d')

    store_outputs(s3, df_scores, 'scores', date)
    store_outputs(s3, df_f, 'predictions', date)
    store_outputs(s3, df_team, 'ratings', date)

    # Write output HTML
    s3.Bucket('football-robot.com').put_object(
        Key='index.html',
        Body=generate_template(df_f),
        ContentType='text/html',
        ACL='public-read'
    )

    return True
