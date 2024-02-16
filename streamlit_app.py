import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from chicago_deal_vault import process

st.set_page_config(page_title="Chicago Deal Vault Data", layout="wide")
st.header('Chicago PreForeClosure Data')
# function to send the email
def send_email():
     st.sidebar.text("Email Sent \U0001F603")

# Load CSV file
df = pd.read_csv('df_full_clean.csv')
df_closed_deals = pd.read_csv('closed_deals.csv')
df['FILING_DATE_FORECLOSURE'] = pd.to_datetime(df['FILING_DATE_FORECLOSURE']).dt.date
# User Input to choose proximity distance
distance_input = st.sidebar.number_input('Enter distance (proximity) in miles', min_value=1, value=5, step=1)

start_date = st.sidebar.date_input('Please select start date',value=df['FILING_DATE_FORECLOSURE'].min())                              
end_date = st.sidebar.date_input('Please select end date',value=df['FILING_DATE_FORECLOSURE'].max())



if st.sidebar.button('Send Email'):
    send_email()
else:
    print('')
# User Input to select the County
location = st.sidebar.selectbox(
    'Please select a County',
    ('Chicago', 'Suburbs', 'DuPage'))
df = df[df['Location']==location]
st.sidebar.info(f"Date is available from {df['FILING_DATE_FORECLOSURE'].min()} to {df['FILING_DATE_FORECLOSURE'].max()}")
df = df[(df['FILING_DATE_FORECLOSURE'] >= start_date) & (df['FILING_DATE_FORECLOSURE'] <= end_date)]
if len(df) < 1:
    st.sidebar.info('No data found for the dates selected')
else:
    df = df[df['Location']==location]
    
    df = df[(df['FILING_DATE_FORECLOSURE'] >= start_date) & (df['FILING_DATE_FORECLOSURE'] <= end_date)]
    first_location = st.selectbox(f'Select an Address for {location}', df_closed_deals['Address'].unique(),key='First Location')
    first_location_coords = df_closed_deals[df_closed_deals['Address'] == first_location].reset_index()
    df_closed_deals = df_closed_deals[df_closed_deals['Address'] != first_location]
    df_new = process(df,first_location_coords.loc[0,'lat'],first_location_coords.loc[0,'lon'])
    close_to_point = df_new['distance_from_point'] <= distance_input
    point_lat_lon = [first_location_coords.loc[0,'lat'],first_location_coords.loc[0,'lon']]



# Create figure
    fig = go.Figure()
 ########################## User Selected Location Mapping ##########################
    # Plot user selected Point on map
    fig.add_trace(go.Scattermapbox(
        lat=[point_lat_lon[0]],
        lon=[point_lat_lon[1]],
        mode='markers+text',
        marker=go.scattermapbox.Marker(
            size=18,
            color='green',
            opacity=0.8  # Distinct color for Canfield
        ),
        text=first_location_coords['Address'],
        textposition='bottom right',
        name=first_location_coords.loc[0,'Address']
    ))

    # Add scatter plot for points within 5 miles of Canfield
    fig.add_trace(go.Scattermapbox(
        lat=df[close_to_point]['lat'],
        lon=df[close_to_point]['lon'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=10,
            color='green',  # Color for Canfield proximity
        ),
        text="<b>Filing Date:</b> " + df[close_to_point]['FILING_DATE_FORECLOSURE'].astype('str') + "<br>"  + "<b>Address: </b>" +df[close_to_point]['ADDRESS'] ,
        name=f"Within {distance_input} miles from {first_location_coords.loc[0,'Address']}"
    ))

    # Add Closed deals to the map 
    fig.add_trace(go.Scattermapbox(
        lat=df_closed_deals['lat'],
        lon=df_closed_deals['lon'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=10,
            color='blue',  # Default color for closed deals
        ),
        text= "<b>Address: </b>" + df_closed_deals['Address'],
        name='Closed Deals'
    ))

    # Update layout
    fig.update_layout(
        autosize=True,
        height = 700,
        width = 900,
        hovermode='closest',
        mapbox=dict(
            accesstoken='pk.eyJ1IjoiYWsxMzUyIiwiYSI6ImNsc2Q5dmdzdzBnNGsyanRkY3BmOXIydGIifQ.dVj-_EwangGrP_AClR6cEA',  # Make sure this is your correct Mapbox Access Token
            bearing=0,
            style="satellite-streets",
            center=dict(
                lat=first_location_coords['lat'].mean(),
                lon=first_location_coords['lon'].mean()
            ),
            pitch=0,
            zoom=10
        ),
    )

    # Display the map
    st.plotly_chart(fig)