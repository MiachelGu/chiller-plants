# General purpose functions for IPython Notebooks..
# They are kind of dirty but get the job done.
import pandas as pd
import numpy as np
import glob
import os

from functools import lru_cache
from sklearn import preprocessing


## load data

@lru_cache(maxsize=None)
def load_df(src, pattern):
    all_files = glob.glob(os.path.join(src, pattern))
    df = pd.concat([pd.read_csv(f, low_memory=False) for f in all_files], ignore_index=True)

    # minor changes
    df = df.rename(columns={"Time Stamp": "timestamp"})
    df = df.replace("\\N", np.nan)

    # update data types. object is taken as default
    dtypes = dict([(col, np.float64) for col in df.columns])
    dtypes["timestamp"] = "datetime64[ns]"
    df = df.astype(dtypes)

    # change the index to timestamp.
    df.index = df.timestamp
    df = df.drop("timestamp", axis=1)
    
    return df


## Data Preprocessing
class Process:
    
    # replace nulls with rolling mean or near ones
    @staticmethod
    def replace_nulls(df, cols=[]):
        cols = cols or df.columns
        mean = df[cols].rolling(5, min_periods=1).mean()
        df[cols] = df[cols].fillna(mean)
        df[cols] = df[cols].fillna(method="pad")
        return df

    # create binary cols. 1 if > thresh, 0 if <= thresh
    @staticmethod
    def create_binary_cols(df, cols=[], thresh=0.1):
        cols = cols or df.columns
        for c in cols:
            binzr = preprocessing.Binarizer(thresh).fit(df[c])
            df[c + "_bin"] = binzr.transform(df[c])
        return df

    # set values < thresh to 0
    @staticmethod
    def replace_with_zero(df, cols=[], thresh=0.1):
        cols = cols or df.columns
        cols = [i for i in cols if not i.endswith("_bin")] # ignore step 2 cols
        for c in cols:
            df.loc[df[c] < thresh, c] = 0
        return df


    # replace values < thresh with near values
    @staticmethod
    def replace_with_near(df, cols=[], thresh=0.1):
        cols = cols or df.columns
        cols = [i for i in cols if not i.endswith("_bin")] # ignore step 2 cols
        for c in cols:
            df.loc[df[c] < thresh, c] = np.nan
        df[cols] = df[cols].fillna(method="pad")
        return df


    # create ctkw total
    @staticmethod
    def set_ctwk_total(df, cols=[]):
        cols = cols or df.columns
        ctkw_cols = [i for i in cols if i.startswith("ct") and i.endswith("kw")]
        df["cwkw_sum"] = df[ctkw_cols].sum(axis=1)
        return df


    # remove random noise. do some soft smoothing.
    @staticmethod
    def smooth_data(df, cols=[]):
        cols = cols or df.columns
        df[cols] = df[cols].rolling(10, min_periods=1).mean()

    @staticmethod
    def get_normalized_df(dataframe, scale=(0.1,1), cols=[]):
        # columns and index
        columns = cols or dataframe.columns
        index = dataframe.index.values

        # fit the scaler
        dataframe = dataframe[columns]
        scaler = preprocessing.MinMaxScaler(scale)
        dataframe = pd.DataFrame(scaler.fit_transform(dataframe), columns=columns, index=index)

        # attach the scaler..
        dataframe.scaler = scaler
        return dataframe


## Feature Processing

# Remove values from the dataframe at beginning so that the
# length is a multiple of batch size. Needed for training.
def equalize_length(arr, batch, where="start"):
    cnt = arr.shape[0]
    return arr[cnt % batch:] if where == "start" else arr[: cnt - (cnt % batch)]
    
# prepare feature vectors. the hypothesis is that
# y(t) can be determined using x1(k), x2(k), x3(k).... for all k = {t-1, t-2, t-3, ... t-N}, where 0 <= N <= t-1
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

# Inverse normalize a particular feature..
def inverse_scale(scaler, col, scaler_idx=0):
    col = col.copy()
    col -= scaler.min_[scaler_idx]
    col /= scaler.scale_[scaler_idx]
    return col

## Keras datasets
def prepare_keras_data(df, features, target, lookback, batch_size):
    # Prepare features and target vectors
    x, y = prepare_features(df, features, target, N=lookback)
 
    # Equalize length
    x = equalize_length(x, batch_size)
    y = equalize_length(y, batch_size)

    # Reshape to Keras requirements
    x = Reshape.x(x)
    y = Reshape.y(y)
    
    return x, y


## Keras shapes
class Reshape:
    @staticmethod
    def x(a):
        return a.reshape((a.shape[0], 1, a.shape[1] * a.shape[2]))
        
    @staticmethod
    def y(a):
        return a.reshape((a.shape[0], 1, 1))
    
    @staticmethod
    def inv_y(a):
        return a.reshape(a.shape[0],)

    
## Metrics
mean_absolute_percent_error = lambda y_true, y_pred: np.mean(np.abs((y_true - y_pred) / y_true)) * 100

def mean_absolute_percent_error_ignore_zero(y_true, y_predict):
    cnt = 0
    tot_err = 0
    for i in range(y_true.shape[0]):
        if y_true[i] != 0:
            tot_err += np.abs((y_true[i] - y_predict[i]) / y_true[i])
            cnt += 1
    return (tot_err / cnt) * 100
