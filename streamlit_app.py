import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from chicago_deal_vault import process, aggregate_addresses, process_new_data
from io import StringIO
import os, time

st.set_page_config(page_title="Chicago Deal Vault Data", layout="wide")
st.header('Chicago Deal Vault Data')

def convert_df_to_csv(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

# Load Files
df = pd.read_csv('pfc.csv')
df_probate = pd.read_csv('probate.csv')
df_closed_deals = pd.read_csv('closed_deals.csv')
df_auctions = pd.read_csv('auction.csv')

if 'Deceased_Address' in df_probate.columns:
    df_probate.rename(columns={'Deceased_Address':'ADDRESS'},inplace=True)
if 'Deceased_City' in df_probate.columns:
    df_probate.rename(columns={'Deceased_City':'CITY'},inplace=True)
if 'Deceased_Zip' in df_probate.columns:
    df_probate.rename(columns={'Deceased_Zip':'ZIP'},inplace=True)

message = st.empty()
##################### FILE UPLOADING STARTS ###########################
st.warning('The file to be uploaded must be named as pfc.xlsx for preforeclosure, auct.xlsx for auctions, prob.xlsx for probate \
           and criteria.xlsx for Criteria file (no CSV format). Please upload one file at a time')
uploaded_file = st.sidebar.file_uploader("Upload File")

if uploaded_file is not None:
    # Check the file name
    if uploaded_file.name.lower() == 'pfc.xlsx':
        # Save the file to the current directory
        with open(os.path.join(os.getcwd(), uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        message.success("Perforeclosure File uploaded successfully!")
        time.sleep(2)
        message.text('')
        df_pfc_new = pd.read_excel('pfc.xlsx',sheet_name='Data',skiprows=11)
        process_new_data(df_pfc_new,data='pfc')
        
        df = pd.read_csv('pfc.csv')

    elif uploaded_file.name.lower() == 'auct.xlsx':
        with open(os.path.join(os.getcwd(), uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        message.success("Auctions File uploaded successfully!")
        time.sleep(2)
        message.text('')
        df_auctions_new = pd.read_excel('auct.xlsx',sheet_name='Data',skiprows=11)
        message.text('Processing uploaded data...')
        process_new_data(df_auctions_new,data='auct')
        message.text('All good!')

    elif uploaded_file.name.lower() == 'prob.xlsx':
        with open(os.path.join(os.getcwd(), uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        message.success("Probate File uploaded successfully!")
        time.sleep(2)
        message.text('')
        df_probate_new = pd.read_excel('prob.xlsx',sheet_name='Data',skiprows=11)
        if 'Deceased_Address' in df_probate_new.columns:
            df_probate_new.rename(columns={'Deceased_Address':'ADDRESS'},inplace=True)
        if 'Deceased_City' in df_probate_new.columns:
            df_probate_new.rename(columns={'Deceased_City':'CITY'},inplace=True)
        if 'Deceased_Zip' in df_probate_new.columns:
            df_probate_new.rename(columns={'Deceased_Zip':'ZIP'},inplace=True)
        message.text('Processing uploaded data...')
        process_new_data(df_probate_new,data='prob')
        message.text('All good!')
        
    else:
        # Inform the user that the file name is different
        st.error("The file name is different. Please upload a file named 'pfc.xlsx'.")

##################### FILE UPLOADING ENDS ###############################

################## LIST STACKING STARTS ###############################
if st.button('Create List Stacking'):
    df_pf = pd.read_csv('pfc.csv')
    df_pr = pd.read_csv('probate.csv')
    df_au = pd.read_csv('auction.csv')
    df_pr.rename(columns={'Deceased_Address':'ADDRESS'},inplace=True)

    all_data = pd.concat([df_pf,df_pr,df_au],axis=0)
    # Process addresses (replace df1, df2, df3 with actual DataFrames)
    result_df = aggregate_addresses(df_pf[['ADDRESS']],df_pr[['ADDRESS']],df_au[['ADDRESS']])
    # Filter out addresses that are in at least two of the files
    result_df = result_df[result_df['sum'] >= 2]
    result_df = result_df.drop_duplicates(subset=['ADDRESS'],keep='first')
    result_df = result_df.merge(all_data[['ADDRESS','CITY']],on=['ADDRESS'])
    result_df = result_df.drop_duplicates(subset=['ADDRESS'],keep='first')
    result_df.drop(columns = ['index','sum','count'],inplace=True)
    result_df.drop_duplicates(subset=['ADDRESS'],keep='first',inplace=True)
    result_df.reset_index(inplace=True)#
    result_df.drop(columns=['index'],inplace=True)

    df_au = df_au[df_au['ADDRESS'].isin(list(result_df['ADDRESS']))]
    df_pr = df_pr[df_pr['ADDRESS'].isin(list(result_df['ADDRESS']))]
    df_pf = df_pf[df_pf['ADDRESS'].isin(list(result_df['ADDRESS']))]
    list_stacked_address = pd.concat([df_pf,df_au,df_pr])
    list_stacked_address.drop_duplicates(subset=['ADDRESS','Type'],keep='first',inplace=True)
    st.download_button(
    label="Download list stacking results",
    data=convert_df_to_csv(list_stacked_address),
    file_name='list_stacking_export.csv',
    mime='text/csv',
    )

    # Show the filtered DataFrame in the app (optional)
    st.write('Addresses in at Least Two Files:', result_df)
################### LIST STACKING ENDS ######################################
    
# Assuming df, df_probate, and df_auctions are your DataFrames
df['FILING_DATE_FORECLOSURE'] = pd.to_datetime(df['FILING_DATE_FORECLOSURE'])
df_probate['Filing_Date'] = pd.to_datetime(df_probate['Filing_Date'])
df_auctions['AUCTION_DATE'] = pd.to_datetime(df_auctions['AUCTION_DATE'])

# Concatenate the Date columns from all three DataFrames without converting to date
dates = pd.concat([df['FILING_DATE_FORECLOSURE'], df_probate['Filing_Date'], df_auctions['AUCTION_DATE']])

# Now, find the minimum and maximum date
min_date = dates.min().date()
max_date = dates.max().date()


min_date_formatted = min_date.strftime('%m/%d/%Y')
max_date_formatted = max_date.strftime('%m/%d/%Y')

# Display the formatted date range in the sidebar
st.sidebar.info(f"Data is available from {min_date_formatted} to {max_date_formatted}")

# User Input to choose proximity distance
distance_input = st.sidebar.number_input('Enter distance (proximity) in miles', min_value=1, value=1, step=1)

# date input filters
start_date = pd.Timestamp(st.sidebar.date_input('Please select start date',
                                   value=df['FILING_DATE_FORECLOSURE'].min(),
                                   format="MM/DD/YYYY"))                          
end_date = pd.Timestamp(st.sidebar.date_input('Please select end date',
                                 value=df['FILING_DATE_FORECLOSURE'].max(),
                                 format="MM/DD/YYYY"))

# User Input to select the County
location = st.sidebar.selectbox(
    'Please select a County',
    ('Chicago', 'Suburbs', 'DuPage'))

########## Combine Data for Mapping Starts ##########
# df['FILING_DATE_FORECLOSURE'] = pd.to_datetime(df['FILING_DATE_FORECLOSURE'])
# df_probate.rename(columns={'Filing_Date':'FILING_DATE_FORECLOSURE'},inplace=True)
# df_auctions.rename(columns={'AUCTION_DATE':'FILING_DATE_FORECLOSURE'},inplace=True)

# df.columns = df.columns.str.upper()
# df_probate.columns = df_probate.columns.str.upper()
# df_auctions.columns = df_auctions.columns.str.upper()

# df.reset_index(inplace=True)
# df_probate.reset_index(inplace=True)
# df_auctions.reset_index(inplace=True)

# df = pd.concat([df,df_probate,df_auctions])
######### Combine Data for Mapping Ends ##########

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

    ################ Download Map Data as CSV Starts ##########################################
    


    st.download_button(
    label="Download data as CSV",
    data=convert_df_to_csv(df_new[df_new['distance_from_point'] <= distance_input]),
    file_name='map_data.csv',
    mime='text/csv',
    )
    
    ################ Download Map Data as CSV Ends   ###########################################


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
            color='red',
            opacity=0.9  # Distinct color for User selected location
        ),
        text=first_location_coords['Address'],
        textposition='bottom right',
        name=first_location_coords.loc[0,'Address']
    ))

    # Add scatter plot for points within X User selected location
    fig.add_trace(go.Scattermapbox(
        lat=df[close_to_point]['lat'],
        lon=df[close_to_point]['lon'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=10,
            color='green',  # Color for User selected location proximity
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
