# Data preprocessing module. 
# Note: Check IPython Notebooks for results on using these..

from sklearn.preprocessing import MinMaxScaler

import numpy as np
import pandas as pd


# replace nulls with rolling mean or near ones
def replace_nulls(df, cols=[]):
    cols = cols or df.columns
    mean = df[cols].rolling(5, min_periods=1).mean()
    df[cols] = df[cols].fillna(mean)
    df[cols] = df[cols].fillna(method="pad")
    return df


# replace values < thresh with near values
def replace_with_near(df, cols=[], thresh=0.1):
    cols = cols or df.columns
    cols = [i for i in cols if not i.endswith("_bin")]
    for c in cols:
        df.loc[df[c] < thresh, c] = np.nan
    df[cols] = df[cols].fillna(method="pad")
    return df


# remove random noise. do some soft smoothing.
def smooth_data(df, cols=[]):
    cols = cols or df.columns
    df[cols] = df[cols].rolling(10, min_periods=1).mean()
    return df


# normalize dataframe
def get_normalized_df(df, scale=(0.1,1), cols=[]):
    if df.shape[0] == 0:
        return df

    # columns and index
    columns = cols or df.columns
    index = df.index.values

    # fit the scaler
    df = df[columns]
    scaler = MinMaxScaler(scale)
    df = pd.DataFrame(scaler.fit_transform(df), columns=columns, index=index)

    # attach the scaler..
    df.scaler = scaler
    return df


# prepare feature vectors for keras
def prepare_features(dataframe, features, target, N=1):
    x, y = [], []
    features_data = dataframe[features].values
    target_data = dataframe[target].values
    
    for i in range(dataframe.shape[0]-N-1):
        x.append(features_data[i:i+N])
        y.append(target_data[i+N])
    
    x = np.array(x)
    y = np.array(y)
    return x, y


class Reshape:
    """Keras shape requirements."""

    @staticmethod
    def x(a):
        """Reshape N-Dim feature vectors into 1D that Keras accepts."""
        return a.reshape((a.shape[0], 1, a.shape[1] * a.shape[2]))
        
    @staticmethod
    def y(a):
        """Reshape target vectors that Keras accepts."""
        return a.reshape((a.shape[0], 1, 1))
    
    @staticmethod
    def inv_y(a):
        """Inverse shape target vectors. Comes handy!"""
        return a.reshape(a.shape[0],)
