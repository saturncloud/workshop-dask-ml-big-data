import s3fs
import pandas as pd
import numpy as np
import dask
import dask.dataframe as dd
from dask.distributed import wait
import warnings
from dask_saturn import SaturnCluster
from dask.distributed import Client

cluster = SaturnCluster(
    scheduler_size='medium',
    worker_size='xlarge',
    n_workers=5,
    nthreads=4,
)
client = Client(cluster)
client.wait_for_workers(3)

s3 = s3fs.S3FileSystem(anon=True)

files_2019 = 's3://nyc-tlc/trip data/yellow_tripdata_2019-*.csv'
taxi = dd.read_csv(
    files_2019,
    parse_dates=['tpep_pickup_datetime', 'tpep_dropoff_datetime'],
    storage_options={'anon': True},
    assume_missing=True,
)

# specify feature and label column names
raw_features = [
    'tpep_pickup_datetime', 
    'passenger_count', 
    'tip_amount', 
    'fare_amount',
]
features = [
    'pickup_weekday', 
    'pickup_weekofyear', 
    'pickup_hour', 
    'pickup_week_hour', 
    'pickup_minute', 
    'passenger_count',
]
label = 'tip_fraction'


def prep_df(taxi_df):
    '''
    Generate features from a raw taxi dataframe.
    '''
    df = taxi_df[taxi_df.fare_amount > 0][raw_features].copy()  # avoid divide-by-zero
    df[label] = df.tip_amount / df.fare_amount
     
    df['pickup_weekday'] = df.tpep_pickup_datetime.dt.weekday
    df['pickup_weekofyear'] = df.tpep_pickup_datetime.dt.isocalendar().week
    df['pickup_hour'] = df.tpep_pickup_datetime.dt.hour
    df['pickup_week_hour'] = (df.pickup_weekday * 24) + df.pickup_hour
    df['pickup_minute'] = df.tpep_pickup_datetime.dt.minute
    df = df[features + [label]].astype(float).fillna(-1)
    
    return df

taxi_feat = prep_df(taxi)