import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from chicago_deal_vault import process, aggregate_addresses
from io import StringIO

st.set_page_config(page_title="Chicago Deal Vault Data", layout="wide")
st.header('Chicago PreForeClosure Data')
# function to send the email
def send_email():
     st.sidebar.text("Email Sent \U0001F603")


# Load Files
df = pd.read_csv('preforeclosure.csv')
df_probate = pd.read_excel('probate.xlsx',sheet_name='Data',skiprows=11)
df_closed_deals = pd.read_csv('closed_deals.csv')
df_auctions = pd.read_excel('auctions.xlsx',sheet_name='Data',skiprows=11)
df_probate.rename(columns={'Deceased_Address':'ADDRESS'},inplace=True)

################## LIST STACKING STARTS ##############################
def convert_df_to_csv(df):
    # Convert DataFrame to CSV
    output = StringIO()
    df.to_csv(output, index=False)
    return output.getvalue()

# Assuming you have a button or mechanism to upload or select dataframes (df1, df2, df3)
if st.button('Create List Stacking'):
    # Process addresses (replace df1, df2, df3 with actual DataFrames)
    result_df = aggregate_addresses(df[['ADDRESS']],df_probate[['ADDRESS']],df_auctions[['ADDRESS']])
    # Filter out addresses that are in at least two of the files
    result_df = result_df[result_df['count'] >= 2]
    result_df.drop(columns={'count'},inplace=True)
    # Show the filtered DataFrame in the app (optional)
    st.write('Addresses in at Least Two Files:', result_df)

################### LIST STACKING ENDS ######################################
    
df['FILING_DATE_FORECLOSURE'] = pd.to_datetime(df['FILING_DATE_FORECLOSURE']).dt.date
min_date_formatted = df['FILING_DATE_FORECLOSURE'].min().strftime('%m/%d/%Y')
max_date_formatted = df['FILING_DATE_FORECLOSURE'].max().strftime('%m/%d/%Y')

# Display the formatted date range in the sidebar
st.sidebar.info(f"Data is available from {min_date_formatted} to {max_date_formatted}")

# User Input to choose proximity distance
distance_input = st.sidebar.number_input('Enter distance (proximity) in miles', min_value=1, value=5, step=1)

# date input filters
start_date = st.sidebar.date_input('Please select start date',
                                   value=df['FILING_DATE_FORECLOSURE'].min(),
                                   format="MM/DD/YYYY")                              
end_date = st.sidebar.date_input('Please select end date',
                                 value=df['FILING_DATE_FORECLOSURE'].max(),
                                 format="MM/DD/YYYY")
# email sending part
if st.sidebar.button('Send Email'):
    send_email()
else:
    print('')

# User Input to select the County
location = st.sidebar.selectbox(
    'Please select a County',
    ('Chicago', 'Suburbs', 'DuPage'))
df = df[df['Location']==location]


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
            #style="satellite-streets",
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
