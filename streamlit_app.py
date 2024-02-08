import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def send_email():
     st.sidebar.text("Email Sent \U0001F603")
# Load the augmented CSV file
df = pd.read_csv('df_full_clean.csv')
df_closed_deals = pd.read_csv('closed_deals.csv')
df_closed_deals = df_closed_deals[(df_closed_deals['Address']!= '6231 N Canfield Ave') & 
                                  (df_closed_deals['Address']!= '1746 N California Ave')]

# User Input to choose proximity distance
distance_input = st.sidebar.number_input('Enter distace (proximity) in miles', min_value=1, value=5, step=1)

# User Input to select the County
location = st.sidebar.selectbox(
    'Please select a County',
    ('Chicago', 'Suburbs', 'DuPage'))

df = df[df['Location']==location]

if st.sidebar.button('Send Email'):
    send_email()
else:
    print('')


# KM to Miles
df['distance_from_canfield'] = df['distance_from_canfield'] * 1.6
df['distance_from_ca_ave'] = df['distance_from_ca_ave'] * 1.6

# Define criteria for highlighting points
close_to_canfield = df['distance_from_canfield'] <= distance_input
close_to_ca_ave = df['distance_from_ca_ave'] <= distance_input

# Define the two specific locations
canfield_lat_lon = [41.9944459469234, -87.821749488142]
ca_ave_lat_lon = [41.91362381711367, -87.69729184581809]

# Create figure
fig = go.Figure()

# Plot Canfield Point on map
fig.add_trace(go.Scattermapbox(
    lat=[canfield_lat_lon[0]],
    lon=[canfield_lat_lon[1]],
    mode='markers+text',
    marker=go.scattermapbox.Marker(
        size=18,
        color='black',
        opacity=0.5  # Distinct color for Canfield
    ),
    text=['Canfield'],
    textposition='bottom right',
    name='Canfield'
))
# Add scatter plot for points within 5 miles of Canfield
fig.add_trace(go.Scattermapbox(
    lat=df[close_to_canfield]['lat'],
    lon=df[close_to_canfield]['lon'],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=10,
        color='red',  # Color for Canfield proximity
    ),
    text=df[close_to_canfield]['FILING_DATE_FORECLOSURE'],
    name='Close to Canfield'
))

# Add scatter plot for CA Ave location
fig.add_trace(go.Scattermapbox(
    lat=[ca_ave_lat_lon[0]],
    lon=[ca_ave_lat_lon[1]],
    mode='markers+text',
    marker=go.scattermapbox.Marker(
        size=18,
        color='purple',  # Distinct color for CA Ave
    ),
    text=['CA Ave'],
    textposition='bottom right',
    name='CA Ave'
))

# Add scatter plot for points within 5 km of CA Ave
fig.add_trace(go.Scattermapbox(
    lat=df[close_to_ca_ave]['lat'],
    lon=df[close_to_ca_ave]['lon'],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=10,
        color='green',
        opacity=0.5  # Color for CA Ave proximity
    ),
    text=df[close_to_ca_ave]['FILING_DATE_FORECLOSURE'],
    name='Close to CA Ave'
))

# Add scatter plot for the remaining points
fig.add_trace(go.Scattermapbox(
    lat=df[~(close_to_canfield | close_to_ca_ave)]['lat'],
    lon=df[~(close_to_canfield | close_to_ca_ave)]['lon'],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=10,
        color='blue',  # Default color for other points
    ),
    text=df[~(close_to_canfield | close_to_ca_ave)]['FILING_DATE_FORECLOSURE'],
    name='Out of Proximity'
))


# Add Closed deals to the map
fig.add_trace(go.Scattermapbox(
    lat=df_closed_deals['lat'],
    lon=df_closed_deals['lon'],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=10,
        color='orange',  # Default color for closed deals
    ),
    text=df_closed_deals['Address'],
    name='Closed Deals'
))

# Update layout
fig.update_layout(
    autosize=True,
    height = 700,
    width = 900,
    hovermode='closest',
    mapbox=dict(
        accesstoken='pk.eyJ1IjoiYWsxMzUyIiwiYSI6ImNscmZzeXY3MDA4MG4yam8yajJmaTYxb24ifQ.ZUeGaita89-L-N_usIhvIg',  # Make sure this is your correct Mapbox Access Token
        bearing=0,
        center=dict(
            lat=df['lat'].mean(),
            lon=df['lon'].mean()
        ),
        pitch=0,
        zoom=10
    ),
)

# Display the map
st.plotly_chart(fig)
