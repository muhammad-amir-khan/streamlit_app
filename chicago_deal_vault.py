import pandas as pd
from math import radians, cos, sin, asin, sqrt
from mapbox import Geocoder

geocoder = Geocoder(access_token="pk.eyJ1IjoiYWsxMzUyIiwiYSI6ImNsc2Q5dmdzdzBnNGsyanRkY3BmOXIydGIifQ.dVj-_EwangGrP_AClR6cEA")

def geocode_address(address):
    try:
        response = geocoder.forward(address)
        # Get the first result (highest relevance)
        coords = str(response.json()['features'][0]['center']).replace(']', '').replace('[', '').split(',')
        return coords[0], coords[1]  # lat, lon
    except IndexError:
        # Return NaN if no result is found
        return float('nan'), float('nan')


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
        r = 3956 # Radius of earth in kilometers. Use 3956 for miles. Determines return value units.
        return c * r

def convert_address(df):
    df['lon'], df['lat'] = zip(*df['COMPLETE_ADDRESS'].apply(geocode_address))
    return df

def process(df_clean_full,point_lat,point_lon):
    df_clean_full['distance_from_point'] = 0.0
    df_clean_full['lat'] = df_clean_full['lat'].astype('float')
    df_clean_full['lon'] = df_clean_full['lon'].astype('float')

    canfield_lat_lon = [point_lat, point_lon]
    df_clean_full['distance_from_point'] = df_clean_full.apply(lambda row: haversine(row['lon'], 
                                                                row['lat'],
                                                                canfield_lat_lon[1],
                                                                canfield_lat_lon[0]), axis=1)
    
    # km to miles
    #df_clean_full['distance_from_point'] = df_clean_full['distance_from_point'] * 0.621371
    df_clean_full.to_csv('df_filtered.csv',index=False)
    return df_clean_full

def aggregate_addresses(df1, df2, df3):
    """
    Aggregates addresses from three DataFrames and identifies how many and which 
    DataFrames each unique address appears in.
    
    Parameters:
    - df1, df2, df3: DataFrames with an 'address' column.
    
    Returns:
    - DataFrame with columns for each address, the count of DataFrames it appears in,
      and boolean columns for its presence in each DataFrame.
    """
    
    # Ensure a copy of the DataFrames is made to avoid altering the original ones
    df1_copy = df1.copy()
    df2_copy = df2.copy()
    df3_copy = df3.copy()

    # Add a source column to each DataFrame to indicate the original source
    df1_copy['source'] = 'df1'
    df2_copy['source'] = 'df2'
    df3_copy['source'] = 'df3'
    
    # Concatenate addresses from all DataFrames
    all_addresses = pd.concat([
        df1_copy[['ADDRESS', 'source']],
        df2_copy[['ADDRESS', 'source']],
        df3_copy[['ADDRESS', 'source']]
    ])
    
    # Group by address and aggregate to count occurrences and identify source DataFrames
    aggregated = all_addresses.groupby('ADDRESS')['source'].agg([
        ('count', 'size'),  # Count occurrences
        ('source_set', lambda x: set(x))  # Identify source DataFrames
    ]).reset_index()
    
    # Initialize the columns indicating presence in each DataFrame
    aggregated['is_in_preforeclosure'] = aggregated['source_set'].apply(lambda x: 'df1' in x)
    aggregated['is_in_probate'] = aggregated['source_set'].apply(lambda x: 'df2' in x)
    aggregated['is_in_auction'] = aggregated['source_set'].apply(lambda x: 'df3' in x)
    
    # Drop the 'source_set' column as it's no longer needed
    result = aggregated.drop(columns=['source_set'])

    result['sum'] = result['is_in_auction'].astype('int') + result['is_in_preforeclosure'].astype('int') + result['is_in_probate'].astype('int')
    result.reset_index(inplace=True)
    return result

# Assuming df1, df2, and df3 are your DataFrames
# result_df = aggregate_addresses(df1, df2, df3)
def process_new_data(df_pfc,convert_address=True,data='pfc'):
     #read new preforeclosure file
     df = df_pfc
     df = df.sort_values(by=['CITY','ZIP']).reset_index().drop(columns=['index'])

     df_criteria_chicago = pd.read_excel('ctiretia.xlsx',sheet_name='Chicago')
     df_criteria_suburbs = pd.read_excel('ctiretia.xlsx',sheet_name='Cook Suburbs')
     df_criteria_dupage = pd.read_excel('ctiretia.xlsx',sheet_name='DuPage County')

     df_criteria_chicago.drop(columns=['Unnamed: 0'],inplace=True)
     df_criteria_suburbs.drop(columns=['Unnamed: 0'],inplace=True)
     df_criteria_dupage.drop(columns=['Unnamed: 0'],inplace=True)

     # to deal with values 12345/78969 in Zip column of Duage County data
     df_criteria_dupage['Zip'] = df_criteria_dupage['Zip'].astype(str).apply(lambda x: x.split('/') if '/' in x else [x])
     df_criteria_dupage = df_criteria_dupage.explode('Zip')
     df_criteria_dupage['Zip'] = df_criteria_dupage['Zip'].astype(int)
     
     df_chicago = df[df['CITY']=='Chicago'].reset_index().drop(columns=['index'])

     #Comparing Suburbs
     df_suburbs = df[df['CITY']!='Chicago'].reset_index().drop(columns=['index'])

     df_criteria_suburbs = df_criteria_suburbs[df_criteria_suburbs['Yes/No']=='Yes']

     df_merged_suburbs = df_criteria_suburbs[['City']].merge(df_suburbs,left_on=df_criteria_suburbs['City'].str.lower(), \
                          right_on=df_suburbs['CITY'].str.lower())
     df_merged_suburbs.drop(columns=['key_0','City'],inplace=True)
     df_merged_suburbs = df_merged_suburbs.sort_values(by=['CITY'])

     # Comparing Chicago
     df_criteria_chicago = df_criteria_chicago[df_criteria_chicago['Yes/No']=='Yes']
     df_merged_chicago = df_criteria_chicago[['Zip']].merge(df_chicago,left_on=['Zip'],right_on=['ZIP'])
     df_merged_chicago.drop(columns=['Zip'],inplace=True)
     df_merged_chicago = df_merged_chicago.sort_values(by=['ZIP'])

     # Comparing DuPage County
     df_merged_dupage = df[df['ZIP'].isin(df_criteria_dupage['Zip'].unique())]

     # Combine All
     #df_merged = df_merged_chicago.append(df_merged_dupage)
     df_merged = pd.concat([df_merged_chicago,df_merged_dupage])
     #df_merged = df_merged.append(df_criteria_suburbs)
     df_merged = pd.concat([df_merged,df_criteria_suburbs])

     # Preparing Clean Data For Mapping
     df_merged_chicago['Location'] = 'Chicago'
     df_merged_dupage['Location'] = 'DuPage'
     df_merged_suburbs['Location'] = 'Suburbs'

     #df_clean_full = df_merged_chicago.append(df_merged_dupage)
     df_clean_full = pd.concat([df_merged_chicago,df_merged_dupage])
     #df_clean_full = df_clean_full.append(df_merged_suburbs)
     df_clean_full = pd.concat([df_clean_full,df_merged_suburbs])

     # Address to Lat, Lon
     df_clean_full['ZIP'] = df_clean_full['ZIP'].astype('str')
     df_clean_full['COMPLETE_ADDRESS'] = df_clean_full['ADDRESS'] +' ' + df_clean_full['CITY'] +', USA '+ df_clean_full['ZIP']
     
     if convert_address:
        df_clean_full['lat'], df_clean_full['lon'] = zip(*df_clean_full['COMPLETE_ADDRESS'].apply(geocode_address))
     else:
         df_clean_full['lat'] = 0.0
         df_clean_full['lon'] = 0.0

     df_clean_full = pd.concat([df_pfc,df_clean_full])
     df_clean_full = df_clean_full.drop_duplicates(subset=['ADDRESS'],keep='last')

     if data == 'auct':
        df_clean_full.to_csv('auctions.csv',index=False)
     elif data == 'prob':
         df_clean_full.to_csv('probates.csv',index=False)
     else:
         df_clean_full.to_csv('preforeclosure.csv',index=False)

     return None
