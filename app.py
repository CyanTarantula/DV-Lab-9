import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta, date

temp_df = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/03-09-2023.csv')
temp_df_country = temp_df.groupby(['Country_Region']).sum().reset_index()
temp_df_country.replace('US', 'United States', inplace=True)

countries = temp_df_country['Country_Region'].unique()

app = dash.Dash(__name__)
app.title = 'Lab 9: Dashboard'

app.layout = html.Div([
    html.Div([
        html.Div([
            html.Div([
                html.Div([
                        html.H2("COVID-19 Impact")
                    ],
                    className="dashboard-title"
                ),

                html.Div([
                    dcc.Store(id='data-store'),
                    html.Div([
                        html.Span("Toll type: ", className="toll-type-label"),
                        dcc.Dropdown(
                            id="type-selected",
                            options=[
                                {'label': "Confirmed ", 'value': 'Confirmed'},
                                {'label': "Recovered ", 'value': 'Recovered'},
                                {'label': "Deaths ", 'value': 'Deaths'},
                                {'label': "Active ", 'value': 'Active'}
                            ],
                            value='Confirmed',
                            clearable=False,
                            className="toll-type-dropdown")
                    ], className="row"),

                    html.Div([
                        html.Span("Select Date: ", style={"text-align": "right"}),
                        dcc.DatePickerSingle(
                            id='my-date-picker-single',
                            min_date_allowed=date(2020, 2, 1),
                            max_date_allowed=date(2023, 3, 9),
                            initial_visible_month=date(2023, 3, 9),
                            date=date(2023, 3, 9)
                        ),
                    ], className="row"),

                    html.Div([
                        html.Span("Select Country: ", style={"text-align": "right"}),
                        dcc.Dropdown(
                            id="country-selected",
                            options=[{'label': i, 'value': i} for i in countries],
                            value='India',
                            clearable=False,
                            className="country-dropdown"
                        ),
                    ], className="row"),
                ], className="row filters"),
            ], className="title-and-filters"),

            dcc.Graph(id="my-graph"),
        ], className="col left-section"),

        html.Div([
            html.Div([
                dcc.Graph(id="pie-chart"),
            ]),
        ], className="col right-section"),

    ], className="row main-container"),
    
    
    html.H4("Created by: Yash Bhargava (B20AI050)", className="footer"),
], className="container")


def prepare_daily_report(date_value="2023-03-09"):
    current_date = datetime.strptime(
        date_value, '%Y-%m-%d').strftime('%m-%d-%Y')
    print("Current Date:", current_date)

    df = pd.read_csv(
        'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/' + current_date + '.csv')
    df_country = df.groupby(['Country_Region']).sum().reset_index()
    df_country.replace('US', 'United States', inplace=True)
    df_country.replace(0, 1, inplace=True)

    code_df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/2014_world_gdp_with_codes.csv')
    df_country_code = df_country.merge(code_df, left_on='Country_Region', right_on='COUNTRY', how='left')

    df_country_code.loc[df_country_code.Country_Region == 'Congo (Kinshasa)', 'CODE'] = 'COD'
    df_country_code.loc[df_country_code.Country_Region == 'Congo (Brazzaville)', 'CODE'] = 'COG'

    return df_country_code.to_dict('records')


@app.callback(
    Output("my-graph", "figure"),
    [
        Input("type-selected", "value"),
        Input('my-date-picker-single', 'date'),
    ]
)
def update_figure(selected, date):
    df = prepare_daily_report(date)

    dff = pd.DataFrame.from_dict(df)

    dff['hover_text'] = dff["Country_Region"] + ": " + dff[selected].apply(str)

    trace = go.Choropleth(
        locations=dff['CODE'], z=np.log(dff[selected]),
        text=dff['hover_text'],
        hoverinfo="text",
        marker_line_color='white',
        autocolorscale=False,
        reversescale=True,
        colorscale="RdBu", marker={'line': {'color': 'rgb(180,180,180)', 'width': 0.5}},
        colorbar={
            "thickness": 10, "len": 0.3, "x": 1.0, "y": 0.7,
            'title': {"text": 'Persons', "side": "bottom"},
            'tickvals': [2, 10],
            'ticktext': ['100', '100,000']
        }
    )
    return {
        "data": [trace],
        "layout": go.Layout(
            height=500, 
            margin={
                "r": 0, "t": 0, "b": 0
            },
            geo={
                'showframe': False,
                'showcoastlines': False,
                'projection': {'type': "miller"}
            },
            paper_bgcolor='rgba(255,255,255,0.5)',
            plot_bgcolor='rgba(0, 0, 0, 0)',
        )
    }

@app.callback(
    Output("pie-chart", "figure"),
    [
        Input("my-date-picker-single", "date"),
        Input("country-selected", "value"),
    ]
)
def update_pie_chart(date, country):
    current_date = datetime.strptime(
        date, '%Y-%m-%d').strftime('%m-%d-%Y')
    
    df = pd.read_csv(
        'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/' + current_date + '.csv')
    df.replace('US', 'United States', inplace=True)
    df = df[df['Country_Region'] == country]
    df = df.groupby(['Last_Update']).sum().reset_index()
    # create rows with value of confirmed, deaths, recovered and active
    df = pd.melt(df, id_vars=['Last_Update'], value_vars=['Confirmed', 'Deaths', 'Recovered', 'Active'], var_name='Toll-type', value_name='Count')
    print(df)
    
    fig = px.pie(df, values='Count', names='Toll-type', title='Distribution of all the cases in ' + country)
    fig.update_traces(
        textposition='inside',               # set text position to inside of the slices
        sort=False
    )
    fig.update_layout(
        margin=dict(l=20, r=0, t=30, b=0),
        #showlegend = False,
        legend=dict(
            orientation='h',
        ),
        paper_bgcolor='#f9f9f9'
    )
    return fig



if __name__ == '__main__':
    app.run_server(debug=True)
