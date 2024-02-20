import pandas as pd
from math import radians, cos, sin, asin, sqrt

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
    df_clean_full['distance_from_point'] = df_clean_full['distance_from_point'] * 0.621371
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
    
    return result

# Assuming df1, df2, and df3 are your DataFrames
# result_df = aggregate_addresses(df1, df2, df3)
