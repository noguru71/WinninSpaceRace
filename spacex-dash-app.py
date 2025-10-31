# Import required libraries
import pandas as pd
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import plotly.express as px

# Read the airline data into pandas dataframe
spacex_df = pd.read_csv("spacex_launch_dash.csv")
max_payload = spacex_df['Payload Mass (kg)'].max()
min_payload = spacex_df['Payload Mass (kg)'].min()

# --- Preparation for the Dropdown (TASK 1) ---
# Get unique launch sites for the dropdown options
launch_sites = spacex_df['Launch Site'].unique().tolist()
# Create the list of dictionaries for the options, adding 'ALL'
site_options = [{'label': 'All Sites', 'value': 'ALL'}] + \
               [{'label': site, 'value': site} for site in launch_sites]
# ----------------------------------------------


# Create a dash application
app = dash.Dash(__name__)

# Create an app layout
app.layout = html.Div(children=[html.H1('SpaceX Launch Records Dashboard',
                                        style={'textAlign': 'center', 'color': '#503D36',
                                               'font-size': 40}),
                                
                                # TASK 1: Add a dropdown list to enable Launch Site selection
                                # The default select value is for ALL sites
                                dcc.Dropdown(id='site-dropdown',
                                             options=site_options,
                                             value='ALL', # Default value
                                             placeholder="Select a Launch Site",
                                             searchable=True
                                             ),
                                html.Br(),

                                # TASK 2: Add a pie chart to show the total successful launches count for all sites
                                # If a specific launch site was selected, show the Success vs. Failed counts for the site
                                html.Div(dcc.Graph(id='success-pie-chart')),
                                html.Br(),

                                html.P("Payload range (Kg):"),
                                
                                # TASK 3: Add a slider to select payload range
                                dcc.RangeSlider(id='payload-slider',
                                                min=0,
                                                max=10000,
                                                step=1000,
						marks={0:'0',2500:'2500',5000:'5000',7500:'7500',10000:'10000'},
                                                value=[min_payload, max_payload],
                                                # Add tooltip to show selected min/max
                                                tooltip={"placement": "bottom", "always_visible": True}
                                                ),
                                html.Br(),

                                # TASK 4: Add a scatter chart to show the correlation between payload and launch success
                                html.Div(dcc.Graph(id='success-payload-scatter-chart')),
                                
                                # Add a div to display booster success rates, placed under the scatter plot
                                html.Div(id='booster-stats-display',
                                         style={'textAlign': 'center', 'marginTop': '10px'}),
                                ])

# --- Callbacks ---

# TASK 2:
# Add a callback function for `site-dropdown` as input, `success-pie-chart` as output
@app.callback(Output(component_id='success-pie-chart', component_property='figure'),
              Input(component_id='site-dropdown', component_property='value'))
def get_pie_chart(entered_site):
    if entered_site == 'ALL':
        # If 'ALL' is selected, sum successes (class=1) for each site
        fig_df = spacex_df.groupby('Launch Site')['class'].sum().reset_index()
        fig = px.pie(fig_df, 
                     values='class', 
                     names='Launch Site', 
                     title='Total Successful Launches by Site')
        return fig
    else:
        # If a specific site is selected, filter by that site
        filtered_df = spacex_df[spacex_df['Launch Site'] == entered_site]
        # Create the pie chart using the 'class' column (0 or 1) for the segments
        # Plotly will automatically count the occurrences of 0 and 1
        fig = px.pie(filtered_df, 
                     names='class', 
                     title=f'Launch Outcomes (Success/Failure) for {entered_site}')
        return fig

# TASK 4:
@app.callback(
    [Output(component_id='success-payload-scatter-chart', component_property='figure'),
     Output(component_id='booster-stats-display', component_property='children')],
    [Input(component_id='site-dropdown', component_property='value'),
     Input(component_id='payload-slider', component_property='value')]
)
def get_scatter_chart(entered_site, payload_range):
    
    # 1. Filter by Payload range (from the slider)
    low, high = payload_range
    payload_filtered_df = spacex_df[(spacex_df['Payload Mass (kg)'] >= low) & 
                                    (spacex_df['Payload Mass (kg)'] <= high)]
    
    # 2. Determine the dataframe to plot based on the site selection
    if entered_site == 'ALL':
        df_to_plot = payload_filtered_df
        base_title = 'Payload vs. Success Correlation (All Sites)'
    else:
        df_to_plot = payload_filtered_df[payload_filtered_df['Launch Site'] == entered_site]
        base_title = f'Payload vs. Success Correlation for {entered_site}'

    # 3. Calculate *overall* success rate for the title
    if len(df_to_plot) > 0:
        success_rate = df_to_plot['class'].mean() * 100 
        title_suffix = f" - Overall Success: {success_rate:.2f}%"
    else:
        title_suffix = " - (No Data for this selection)"
    final_title = base_title + title_suffix

    # 4. Create the scatter plot
    fig = px.scatter(df_to_plot,
                     x='Payload Mass (kg)',
                     y='class',
                     color='Booster Version Category',
                     title=final_title) # Apply the new title
    
    # 5.Calculate stats for the text div
    if len(df_to_plot) > 0:
        # Calculate success rate PER BOOSTER
        booster_rates = df_to_plot.groupby('Booster Version Category')['class'].mean() * 100
        
        # Create a list of html components for the div
        booster_stats_children = [
            html.H5("Booster Success Rates (Current Selection):", 
                    style={'margin-top': '10px', 'font-weight': 'bold'})
        ]
        
        # Sort by rate (highest first) for readability
        for category, rate in booster_rates.sort_values(ascending=False).items():
            booster_stats_children.append(
                html.P(f"{category}: {rate:.2f}%", style={'margin': '2px'})
            )
    else:
        # If no data, just return an empty list for the children
        booster_stats_children = []

    # 6. Return both the figure and the list of children for the div
    return fig, booster_stats_children


# Run the app
if __name__ == '__main__':
    app.run()
