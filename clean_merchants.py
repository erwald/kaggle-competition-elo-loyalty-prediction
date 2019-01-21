import numpy as np
import pandas as pd

def clean_merchants():
    merchants_df = pd.read_csv('data/unzipped/merchants.csv')

    # There are a lot (over 100000) merchants with incomplete city and state data.
    # Since it seems unlikely that the location has an influence on the loyalty, we drop these
    # Also, category_2 is always NaN when the city is unknown, so we drop that, too.
    merchants_df.drop(columns=['city_id', 'state_id', 'category_2'], inplace=True)

    # There are only 15 merchants where some of the lag data is invalid, so let's just drop these.
    merchants_df = merchants_df[np.isnan(merchants_df['avg_sales_lag3']) == False]

    # Category_1 and _4 have only values 'N' and 'Y'. Let's replace this with Booleans False and True
    merchants_df['category_1'] = merchants_df['category_1'].map({'Y': True, 'N': False})
    merchants_df['category_4'] = merchants_df['category_4'].map({'Y': True, 'N': False})

    # The 'most recent' columns measure the size of transactions from 'A' the most to 'E" the least.
    # Let's translate this into 4.0 to 0.0 to make the range continuous.
    range_to_num = {'A': 4, 'B': 3, 'C': 2, 'D': 1, 'E': 0}
    merchants_df['most_recent_sales_range'] = merchants_df['most_recent_sales_range'].map(range_to_num)

    # We need to somehow unify the data for one merchant with several entries.
    # The easiest case is where the all the identifying data is equal.
    # Here we simply aggregate over the features:
    # - numerical_1 and _2: These seem to be measuring some kind of continuous value, let's take the mean.
    # - category_1: This is always True or False, but only 7033 are True. So let's keep True as more special.
    #               max(True, False) = True
    # - most_recent_sales_range,
    #   most_recent_purchases_range: More sales/purchases seems to translate to higher ranges,
    #                                so let's use the maximum b/c we're adding transactions.
    # - average_X_lagY: This one is tricky. Since the average is divided by the value of the last
    #                   active month, it measures how the last active month was worse than the average.
    #                   Maybe we can be more precise by actually analysing the transactions,
    #                   for now I'll take the mean.
    # - active_months_lagX: Take the maximum b/c we're adding transactions.
    # - category_4: False : True is more than 2:1, so let's take True over False
    grouped = merchants_df.groupby(['merchant_id', 'merchant_group_id', 'merchant_category_id', 'subsector_id'])
    aggregated_df = grouped.agg({'numerical_1': np.mean,
                'numerical_2': np.mean,
                'category_1': np.max,
                'most_recent_sales_range': np.max,
                'most_recent_purchases_range': np.max,
                'avg_sales_lag3': np.mean,
                'avg_purchases_lag3': np.mean,
                'active_months_lag3': np.max,
                'avg_sales_lag6': np.mean,
                'avg_purchases_lag6': np.mean,
                'active_months_lag6': np.max,
                'avg_sales_lag12': np.mean,
                'avg_purchases_lag12': np.mean,
                'active_months_lag12': np.max,
                'category_4': np.max})

    return aggregated_df
