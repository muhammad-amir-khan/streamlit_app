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