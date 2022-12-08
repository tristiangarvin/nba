from dash import Dash, Input, Output, dcc, html
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import pandas as pd
import numpy as np
from dash.dependencies import Input
from dash.dependencies import Output

app = Dash(__name__, external_stylesheets=[dbc.themes.SLATE, 'https://codepen.io/chriddyp/pen/bWLwgP.css'],  # bootstrap theme settings
           meta_tags=[
    {"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1.2, minimum-scale=0.5,"}
]
)

data = pd.read_csv('shot-chart.csv')
box_score = pd.read_csv('box-score.csv')


data['SHOT_MADE_STRING'] = data['SHOT_MADE_FLAG'].astype(str)
data['shot_count'] = data.groupby('PLAYER_ID')['PLAYER_ID'].transform('count')

data = data[data['shot_count'] > 10]
data = data[data['LOC_Y'] < 420]


conditions = [
    (data['SHOT_TYPE'] == '3PT Field Goal') & (data['SHOT_MADE_FLAG'] == 1),
    (data['SHOT_TYPE'] == '2PT Field Goal') & (data['SHOT_MADE_FLAG'] == 1),
    (data['SHOT_MADE_FLAG'] == 0)]
choices = [3, 2, 0]

threes_made = len(
    data.loc[(data['SHOT_TYPE'] == '3PT Field Goal') & (data['SHOT_MADE_STRING'] == '1')])

###########     Player Stats    #####################
player_df = pd.read_csv('box-score.csv')
player_df['PPG'] = player_df.groupby('PLAYER_ID')['PTS'].transform('mean')
player_df['ASTPG'] = player_df.groupby('PLAYER_ID')['AST'].transform('mean')
player_df['TFGA'] = player_df.groupby('PLAYER_ID')['FGA'].transform('sum')
player_df['TFGM'] = player_df.groupby('PLAYER_ID')['FGM'].transform('sum')
player_df['Total FG Percentage'] = player_df['TFGM']/player_df['TFGA']


df = pd.merge(left=data, right=player_df, on=[
              'PLAYER_ID', 'GAME_ID'], how='inner')

df.to_csv('data.csv', sep=',', index=False)

team_dropdown = dcc.Dropdown(
    id="filter-team",
    options=[{"label": team, "value": team}
             for team in sorted(df.TEAM_NAME.unique())],
    placeholder="-Select a Team-",
    multi=False,
    value='Dallas Mavericks',
    clearable=False,
)

player_dropdown = dcc.Dropdown(
    id="filter-player",
    placeholder="-Select a Player-",
    clearable=False,
)

dropdowngame = dcc.Dropdown(
    id="filter_dropdown_game",
    placeholder="-Select a Game (Clear for All)-",
    value=[],
    multi=True,
)

app.layout = dbc.Container([
    html.H1("Visualizing the 22-23 NBA Season"),
    dbc.Row([
        dbc.Col([
            html.H3("Shot Chart Statistics"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Team"),
                    team_dropdown,
                ], lg=6, className="pt-3 my-auto",),
                dbc.Col([
                    dbc.Label("Player"),
                    player_dropdown,
                ], lg=6, className="pt-3 my-auto",),
            ], className='pt-3'),
            dbc.Label("Game", className='pt-4'),
            dropdowngame,
        ], lg=3,),
        dbc.Col([
            dcc.Graph(id='shot-chart', figure={}, responsive=True,
                      config={'displayModeBar': False, }),
        ], lg=3),
        dbc.Col([
            dcc.Graph(id='violin-chart')
        ], lg=5, className="mx-auto"),
    ], id='row1',),
    dbc.Row([
        dbc.Col([
            html.Div([
                html.P("PTS", className="pt-3"),
                html.P(id='points', className="stat")
            ], className="col-bg"),
        ], className="my-auto text-center", ),
        dbc.Col([
            html.Div([
                html.P("FG %", className="pt-3"),
                html.P(id='player-percentage', className="stat")
            ], className="col-bg"),
        ], className="my-auto text-center", ),
        dbc.Col([
            html.Div([
                html.P("3PT %", className="pt-3"),
                html.P(id="three-percentage", className="stat")
            ], className="col-bg"),
        ], className=" my-auto text-center",),
        dbc.Col([
            html.Div([
                html.P("FT %", className="pt-3"),
                html.P(id="ft-percentage", className="stat")
            ], className="col-bg"),
        ], className="my-auto text-center",),
        dbc.Col([
            html.Div([
                html.P("TS %", className="pt-3"),
                html.P(id="ts-percentage", className="stat")
            ], className="col-bg"),
        ], className="my-auto text-center",),
    ]),
    dbc.Row([
        dbc.Col([
            html.H3("Season Data")
        ],),
    ],),
], fluid=True)


@app.callback(
    Output('filter-player', 'options'),
    Output('filter-player', 'value'),
    Input('filter-team', 'value')
)
def update_options(team):
    dff = df[df['TEAM_NAME'] == team]
    dff = dff.sort_values('shot_count', ascending=False)
    players = [{"label": player, "value": player}
               for player in dff.PLAYER_NAME.unique()]
    value = players[0]["value"]

    return players, value


@app.callback(
    Output('filter_dropdown_game', 'options'),
    Output('shot-chart', 'figure'),
    Output('violin-chart', 'figure'),
    Output('points', 'children'),
    Output('player-percentage', 'children'),
    Output('three-percentage', 'children'),
    Output('ft-percentage', 'children'),
    Output('ts-percentage', 'children'),
    Input('filter-player', "value"),
    Input('filter_dropdown_game', "value"),
)
def update_options(player, game):
    dff = df[df['PLAYER_NAME'] == player]
    games = [{"label": game, "value": game}
             for game in dff.MATCHUP.unique()]

    game_percentage = ''
    three_percentage = ''

    if player:
        try:
            dff = df[df['PLAYER_NAME'] == player]
            df_nodup = dff.drop_duplicates(subset=['GAME_ID'])
            points = df_nodup['PTS'].sum()
            shots_taken = len(dff)
            shots_made = len(dff.loc[dff['SHOT_MADE_STRING'] == '1'])
            threes_taken = len(dff.loc[dff['SHOT_TYPE'] == '3PT Field Goal'])
            threes_made = len(dff.loc[(dff['SHOT_TYPE'] == '3PT Field Goal') & (
                dff['SHOT_MADE_STRING'] == '1')])
            three_percentage = threes_made/threes_taken
            three_percentage = "{:.1%}".format(three_percentage)
            game_percentage = dff.loc[dff.index[0], 'Total FG Percentage']
            game_percentage = "{:.1%}".format(game_percentage)
            fta = df_nodup['FTA'].sum()
            ftm = df_nodup['FTM'].sum()
            ft_percentage = ftm/fta
            ft_percentage = "{:.1%}".format(ft_percentage)

            tsa = shots_taken + .44 * fta
            ts_percentage = points/(2 * tsa)
            ts_percentage = "{:.1%}".format(ts_percentage)
        except:
            dff = df[df['PLAYER_NAME'] == player]
            df_nodup = dff.drop_duplicates(subset=['GAME_ID'])
            points = df_nodup['PTS'].sum()
            shots_taken = len(dff)
            shots_made = len(dff.loc[dff['SHOT_MADE_STRING'] == '1'])
            game_percentage = shots_made/shots_taken
            game_percentage = "{:.1%}".format(game_percentage)
            three_percentage = "N/A"

            fta = df_nodup['FTA'].sum()
            ftm = df_nodup['FTM'].sum()
            ft_percentage = ftm/fta
            ft_percentage = "{:.1%}".format(ft_percentage)

            tsa = shots_taken + .44 * fta
            ts_percentage = points/(2 * tsa)
            ts_percentage = "{:.1%}".format(ts_percentage)

    if game:
        try:
            dff = dff[dff['MATCHUP'].isin(game)]
            df_nodup = dff.drop_duplicates(subset=['GAME_ID'])
            points = df_nodup['PTS'].sum()
            shots_taken = len(dff)
            shots_made = len(dff.loc[dff['SHOT_MADE_STRING'] == '1'])
            threes_taken = len(dff.loc[dff['SHOT_TYPE'] == '3PT Field Goal'])
            threes_made = len(dff.loc[(dff['SHOT_TYPE'] == '3PT Field Goal') & (
                dff['SHOT_MADE_STRING'] == '1')])
            three_percentage = threes_made/threes_taken
            three_percentage = "{:.1%}".format(three_percentage)
            game_percentage = shots_made/shots_taken
            game_percentage = "{:.1%}".format(game_percentage)
            game = []

            fta = df_nodup['FTA'].sum()
            ftm = df_nodup['FTM'].sum()
            ft_percentage = ftm/fta
            ft_percentage = "{:.1%}".format(ft_percentage)

            tsa = shots_taken + .44 * fta
            ts_percentage = points/(2 * tsa)
            ts_percentage = "{:.1%}".format(ts_percentage)

        except:
            dff = dff[dff['MATCHUP'].isin(game)]
            df_nodup = dff.drop_duplicates(subset=['GAME_ID'])
            points = df_nodup['PTS'].sum()
            shots_taken = len(dff)
            shots_made = len(dff.loc[dff['SHOT_MADE_STRING'] == '1'])
            game_percentage = shots_made/shots_taken
            game_percentage = "{:.1%}".format(game_percentage)
            three_percentage = "N/A"

            fta = df_nodup['FTA'].sum()
            ftm = df_nodup['FTM'].sum()
            ft_percentage = ftm/fta
            ft_percentage = "{:.1%}".format(ft_percentage)

            tsa = shots_taken + .44 * fta
            ts_percentage = points/(2 * tsa)
            ts_percentage = "{:.1%}".format(ts_percentage)

    violin = px.violin(dff, y="SHOT_DISTANCE", color="EVENT_TYPE", color_discrete_sequence=[
        "#FE4B44", "#FEFDA0"], category_orders={"EVENT_TYPE": ['Missed Shot', 'Made Shot']}, violinmode='overlay', title="Shot Distance Distribution", labels={"SHOT_DISTANCE": "Distance"},)

    violin.update_layout(
        {
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)',
        },
        autosize=False,
        margin={'t': 50, 'l': 20, 'b': 0, 'r': 20},
        font_color="white",
        hovermode="x",
        legend_title="",
    )

    violin.update_xaxes(gridcolor='#61707D')
    violin.update_yaxes(gridcolor='#61707D', range=[0, 40], fixedrange=True)

    violin.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=.99,
        xanchor="right",
        x=1
    ))

    violin.add_hline(y=dff['SHOT_DISTANCE'].mean(),
                     line_width=2, line_dash="dash", line_color="white")

    player_chart = px.scatter(dff, x="LOC_X", y="LOC_Y", color="SHOT_MADE_STRING", color_discrete_sequence=[
        "#FE4B44", "#FEFDA0"], category_orders={"SHOT_MADE_STRING": ['0', '1']}, symbol=dff['SHOT_MADE_STRING'], symbol_sequence=['x', 'hexagon'],)
    player_chart.update_xaxes(
        range=[250, -250], visible=False, fixedrange=True)
    player_chart.update_yaxes(range=[-55, 420], visible=False, fixedrange=True)

    player_chart.update_layout(
        showlegend=False,
        autosize=False,
        height=1000,
        margin={'t': 0, 'l': 0, 'b': 5, 'r': 0}
    )

    player_chart.update_layout({
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
    })

    player_chart.update_yaxes(
        scaleanchor="x",
        scaleratio=2,
    )

    player_chart.update_xaxes(
        scaleanchor="y",
        scaleratio=1,
    )

    player_chart.add_layout_image(
        dict(
            # source="https://i.ibb.co/HCZ3m50/nba-court.png",
            source="https://i.ibb.co/2jQwW3L/nba-court-1.png",
            xref="x",
            yref="y",
            x=250,
            y=415,
            sizex=500,
            sizey=470,
            sizing="stretch",
            opacity=1,
            layer="below",
        )
    )

    player_chart.update_traces(marker=dict(size=10, opacity=1,
                                           line=dict(width=1,
                                                     color='darkslategrey')),
                               selector=dict(mode='markers'))
    return games, player_chart, violin, points, game_percentage, three_percentage, ft_percentage, ts_percentage


server = app.server

if __name__ == "__main__":
    while True:
        app.run_server(debug=True)
