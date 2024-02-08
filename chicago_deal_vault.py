import pandas as pd
from mapbox import Geocoder
from math import radians, cos, sin, asin, sqrt

def process():
    df = pd.read_excel('cdv.xlsx',sheet_name='Data',skiprows=11)

    df_criteria_chicago = pd.read_excel('ZIA Buying Criteria - Chicagoland Zips (1).xlsx',sheet_name='Chicago')
    df_criteria_suburbs = pd.read_excel('ZIA Buying Criteria - Chicagoland Zips (1).xlsx',sheet_name='Cook Suburbs')
    df_criteria_dupage = pd.read_excel('ZIA Buying Criteria - Chicagoland Zips (1).xlsx',sheet_name='DuPage County')

    df_criteria_chicago.drop(columns=['Unnamed: 0'],inplace=True)
    df_criteria_suburbs.drop(columns=['Unnamed: 0'],inplace=True)
    df_criteria_dupage.drop(columns=['Unnamed: 0'],inplace=True)

    # to deal with values 12345/78969 in Zip column of Duage County data
    df_criteria_dupage['Zip'] = df_criteria_dupage['Zip'].astype(str).apply(lambda x: x.split('/') if '/' in x else [x])
    df_criteria_dupage = df_criteria_dupage.explode('Zip')
    df_criteria_dupage['Zip'] = df_criteria_dupage['Zip'].astype(int)

    # Transform Balance Columns to Currency Form
    def format_balance(balance):
        return f"${balance:,.2f}"

    # Applying the formatting function
    df['BALANCE_DUE'] = df['BALANCE_DUE'].apply(format_balance)
    df['ZESTIMATE'] = df['ZESTIMATE'].apply(format_balance)
    df['Equity'] = df['Equity'].apply(format_balance)
    df['ORIGINAL_AMOUNT'] = df['ORIGINAL_AMOUNT'].apply(format_balance)

    df = df.sort_values(by=['CITY','ZIP']).reset_index().drop(columns=['index'])

    df_chicago = df[df['CITY']=='Chicago'].reset_index().drop(columns=['index'])
    df_suburbs = df[df['CITY']!='Chicago'].reset_index().drop(columns=['index'])


    df_criteria_suburbs = df_criteria_suburbs[df_criteria_suburbs['Yes/No']=='Yes']

    df_merged_suburbs = df_criteria_suburbs[['City']].merge(df_suburbs,left_on=df_criteria_suburbs['City'].str.lower(), \
                            right_on=df_suburbs['CITY'].str.lower())
    df_merged_suburbs.drop(columns=['key_0','City'],inplace=True)
    df_merged_suburbs = df_merged_suburbs.sort_values(by=['CITY'])

    df_criteria_chicago = df_criteria_chicago[df_criteria_chicago['Yes/No']=='Yes']

    df_merged_chicago = df_criteria_chicago[['Zip']].merge(df_chicago,left_on=['Zip'],right_on=['ZIP'])
    df_merged_chicago.drop(columns=['Zip'],inplace=True)
    df_merged_chicago = df_merged_chicago.sort_values(by=['ZIP'])

    df_merged_dupage = df[df['ZIP'].isin(df_criteria_dupage['Zip'].unique())]

    df_merged = df_merged_chicago.append(df_merged_dupage)
    df_merged = df_merged.append(df_criteria_suburbs)
    df_removed = df[~df['ZIP'].isin(df_merged['ZIP'])]

    df_removed.to_csv('removed.csv',index=False)

    df_merged_chicago['Location'] = 'Chicago'
    df_merged_dupage['Location'] = 'DuPage'
    df_merged_suburbs['Location'] = 'Suburbs'

    df_clean_full = df_merged_chicago.append(df_merged_dupage)
    df_clean_full = df_clean_full.append(df_merged_suburbs)
    df_clean_full['ZIP'] = df_clean_full['ZIP'].astype('str')
    df_clean_full['COMPLETE_ADDRESS'] = df_clean_full['ADDRESS'] +' ' + df_clean_full['CITY'] +', USA '+ df_clean_full['ZIP']


    geocoder = Geocoder(access_token="pk.eyJ1IjoiYWsxMzUyIiwiYSI6ImNscmZzeXY3MDA4MG4yam8yajJmaTYxb24ifQ.ZUeGaita89-L-N_usIhvIg")
    response = geocoder.forward('847 W MONROE ST UNIT 1S Chicago, USA 60607')


    # Initialize the Mapbox Geocoder with your access token
    access_token = "pk.eyJ1IjoiYWsxMzUyIiwiYSI6ImNscmZzeXY3MDA4MG4yam8yajJmaTYxb24ifQ.ZUeGaita89-L-N_usIhvIg"  # Replace with your Mapbox access token
    geocoder = Geocoder(access_token=access_token)

    # Function to geocode an address
    def geocode_address(address):
        print(address)
        try:
            response = geocoder.forward(address)
            # Get the first result (highest relevance)
            coords = str(response.json()['features'][0]['center']).replace(']', '').replace('[', '').split(',')
            return coords[0], coords[1]  # lat, lon
        except IndexError:
            # Return NaN if no result is found
            return float('nan'), float('nan')

    # Apply the function to the COMPLETE_ADDRESS column
    df_clean_full['lat'], df_clean_full['lon'] = zip(*df_clean_full['COMPLETE_ADDRESS'].apply(geocode_address))


    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance in kilometers between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return c * r

    df_clean_full['distance_from_canfield'] = 0.0
    df_clean_full['distance_from_ca_ave'] = 0.0
    df_clean_full['lat'] = df_clean_full['lat'].astype('float')
    df_clean_full['lon'] = df_clean_full['lon'].astype('float')

    canfield_lat_lon = [41.9944459469234, -87.821749488142]
    ca_ave_lat_lon = [41.91362381711367, -87.69729184581809]

    df_clean_full['distance_from_canfield'] = df_clean_full.apply(lambda row: haversine(row['lat'], 
                                                                row['lon'],
                                                                canfield_lat_lon[1],
                                                                canfield_lat_lon[0]), axis=1)
    df_clean_full['distance_from_ca_ave'] = df_clean_full.apply(lambda row: haversine(row['lat'], 
                                                                row['lon'],
                                                                ca_ave_lat_lon[1],
                                                                ca_ave_lat_lon[0]), axis=1)
    df_clean_full.to_csv('df_full_clean.csv',index=False)