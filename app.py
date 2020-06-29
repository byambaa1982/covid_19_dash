import pandas as pd
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html

data = pd.read_csv('https://opendata.ecdc.europa.eu/covid19/casedistribution/csv',
                    usecols=list(range(0,11)))


data['dateRep'] = pd.to_datetime(data['dateRep'], dayfirst=True)

data.sort_values(by=['countriesAndTerritories', 'dateRep'],
                 ascending=True, inplace=True)

data = data.reindex()

print(data['countriesAndTerritories'].unique())

world = data[['dateRep', 'cases', 'deaths','popData2019']].groupby(by='dateRep').sum()
              
world['day'] = world.index.day
world['month'] = world.index.month
world['year'] = world.index.year
world['dateRep'] = world.index
world['countriesAndTerritories'] = 'World'
world['geoId'] = 'WD'
world['countryterritoryCode'] = 'WLD'

data = pd.concat([data, world], ignore_index=True)

data['total_cases'] = data.groupby(by='countriesAndTerritories')['cases'].cumsum()
data['total_deaths'] = data.groupby(by='countriesAndTerritories')['deaths'].cumsum()


continents = pd.read_csv('https://raw.githubusercontent.com/LUNDR/covid-19/master/app/assets/continents.csv')

data = pd.merge(data,
                continents[['Continent_Name',
                            'Three_Letter_Country_Code']].drop_duplicates('Three_Letter_Country_Code'),
                how='left',
                left_on='countryterritoryCode',
                right_on='Three_Letter_Country_Code')

colours = {"Asia": "royalblue",
           "Europe": "crimson",
           "Africa": "lightseagreen",
           "Oceania": "orange",
           "North America": "gold",
           "South America": 'mediumslateblue',
           "nan": "peru"}

figure = {
    'data': [],
    'layout': {},
    'frames': [],
}

data['dateRep'] = [pd.to_datetime(str(x)) for x in data['dateRep']]
days_as_dates = data['dateRep'][data['dateRep'] > pd.to_datetime('31-12-2019')].sort_values(ascending=True).unique() 
days = [pd.to_datetime(str(x)).strftime('%d %b') for x in days_as_dates]
data['date'] = [pd.to_datetime(str(x)).strftime('%d %b') for x in data['dateRep']]

day = days[-1]
data_ = []
chart_data = data[data['date'] == day]
for i, cont in enumerate(chart_data['Continent_Name'].unique()[:-1]):
    colour = colours[cont]
    df_sub = chart_data[chart_data['Continent_Name'] == cont].reset_index()
    data_dict = dict(
        type='scattergeo',
        locationmode='ISO-3',                               # set of location used to translate data onto the map
        locations=df_sub['countryterritoryCode'].tolist(),  # column in the dataset whe ISO-3 values are found
        marker=dict(                                        # dictionary defining parameters of each marker on the figure
            size=df_sub['total_cases'] / 200,               # the size of each marker
            color=colour,                                   # the colour of the marker
            line_color='#ffffff',                           # the outline colour of the marker
            line_width=0.5,                                 # the width of the marker outline
            sizemode='area'),                               # how the size parameter should be translated, area/diameter
        name='{}'.format(cont),                             # series name (appears on the legend)
        text=[                                              # list of text values defining what appears on the label for each country in the series
           '{}<BR>Total Cases: {}'.format(                
                df_sub['countriesAndTerritories'][x],
                df_sub['total_cases'][x]) for x in range(
                    len(df_sub))])
    figure['data'].append(data_dict)

#------------for Map------------------------
frames = []
steps = []
for day in days:
    chart_data = data[data['date'] == day]
    frame = dict(data=[], name=str(day))
    for i, cont in enumerate(chart_data['Continent_Name'].unique()[:-1]):
        colour = colours[cont]
        df_sub = chart_data[chart_data['Continent_Name'] == cont].reset_index()
        data_dict = dict(
            type='scattergeo',
            locationmode='ISO-3',
            locations=df_sub['countryterritoryCode'].tolist(),
            marker=dict(
                size=df_sub['total_cases'] / 200,
                color=colour,
                line_color='#ffffff',
                line_width=0.5,
                sizemode='area'),
            name='{}'.format(cont),
            text=[
                '{}<BR>Total Cases: {}'.format(
                    df_sub['countriesAndTerritories'][x],
                    df_sub['total_cases'][x]) for x in range(
                    len(df_sub))])
        frame['data'].append(data_dict)
    figure['frames'].append(frame)

    step = dict(                                    
        method="animate",                          # how the transition should take place - should the chart be redrawn?
        args=[
            [day],                                 # should match the frame name                                                  
            dict(frame=dict(duration=100,          # speed and style of the transitions
                            redraw=True),
                 mode="immediate",
                 transition=dict(duration=100,
                                 easing="quad-in"))
        ],
        label=day,                                  # name of the step

    )

    steps.append(step)
    
    
sliders = [dict(
    y=0,
    active=len(days) - 1,
    currentvalue=dict(prefix="",
                      visible=True,
                      ),
    transition=dict(duration=300),
    pad=dict(t=2),
    steps=steps                                     # the list of steps is included here
)]


title_font_family = 'Arial'
title_font_size = 14


figure['layout'] = dict(
    titlefont=dict(                                  # parameters controlling title font
        size=title_font_size,
        family=title_font_family),
    title_text='<b> COVID-19 Total Cases </b> <BR>', # Chart Title
    showlegend=True,                                 # Include a legend
    geo=dict(                                        # parameter controlling the look of the map itself
        scope='world',
        landcolor='rgb(217, 217, 217)',
        coastlinecolor='#ffffff',
        countrywidth=0.5,
        countrycolor='#ffffff',
    ),
    updatemenus=[                                     # Where a 'play' button is added to enable the user to start the animation
        dict(
            type='buttons',
            buttons=list(
                [
                    dict(
                        args=[
                            None,
                            dict(
                                frame=dict(
                                    duration=200,
                                    redraw=True),
                                mode="immediate",
                                transition=dict(
                                    duration=200,
                                    easing="quad-in"))],
                        label="Play",
                        method="animate")]))],
    sliders=sliders)                                   # Add the sliders dictionary

map1 = go.Figure(figure)



  
app = dash.Dash()
app.layout = html.Div([
    dcc.Graph(figure=map1)
])

app.run_server(debug=True, use_reloader=False)  # Turn off reloader if inside Jupyter 