import numpy as np
import pandas as pd
from pandas.api.types import CategoricalDtype

# A category that can take 'Y' and 'N' values and in addition a value 'Both'
# to indicate the we've seen both values for this merchant.
cat_triple = CategoricalDtype(categories = ['Y', 'N', 'Both'])


# The features 'most_recent_sales_range' and 'most_recent_purchases_range' take values
# 'A' to 'E' where 'A' represents the highest amounts. We encode them as categrical data
# 'A' < 'B' < ...< 'E'.
cat_most_recent = CategoricalDtype(categories=['E', 'D', 'C', 'B', 'A'], ordered=True)


# Takes a series of cat_triple values and returns
# 'N' if all are 'N',
# 'Y' if all are "Y',
# 'Both' otherwise
def sum_triples(triples):
    uniques = triples.unique()
    if 'Both' in uniques:
        return 'Both'
    elif 'Y' in uniques:
        if 'N' in uniques:
            return 'Both'
        else:
            return 'Y'
    else:
        return 'N'


def clean_merchants():
    merchants_df = pd.read_csv('data/unzipped/merchants.csv')

    # There are a lot (over 100000) merchants with incomplete city and state data.
    # Since it seems unlikely that the location has an influence on the loyalty, we drop these
    # Also, category_2 is always NaN when the city is unknown, so we drop that, too.
    merchants_df.drop(columns=['city_id', 'state_id', 'category_2'], inplace=True)

    # There are only 15 merchants where some of the lag data is invalid, so let's just drop these.
    merchants_df = merchants_df[np.isnan(merchants_df['avg_sales_lag3']) == False]

    # Category_1 and _4 have only values 'N' and 'Y'. Let's replace this with Booleans False and True
    merchants_df['category_1'] = merchants_df['category_1'].astype(cat_triple)
    merchants_df['category_4'] = merchants_df['category_4'].astype(cat_triple)

    # The 'most recent' columns measure the size of transactions from 'A' the most to 'E" the least.
    merchants_df['most_recent_sales_range'] = merchants_df['most_recent_sales_range'].astype(cat_most_recent)
    merchants_df['most_recent_purchases_range'] = merchants_df['most_recent_purchases_range'].astype(cat_most_recent)

    # We need to somehow unify the data for one merchant with several entries.
    # The easiest case is where the all the identifying data is equal.
    # Here we simply aggregate over the features:
    # - numerical_1 and _2: These seem to be measuring some kind of continuous value, let's take the mean.
    # - category_1: This is always 'Y' or 'N', but only 7033 are True.
    # - most_recent_sales_range,
    #   most_recent_purchases_range: More sales/purchases seems to translate to higher ranges,
    #                                so let's use the maximum b/c we're adding transactions.
    # - average_X_lagY: This one is tricky. Since the average is divided by the value of the last
    #                   active month, it measures how the last active month was worse than the average.
    #                   Maybe we can be more precise by actually analysing the transactions,
    #                   for now I'll take the mean.
    # - active_months_lagX: Take the maximum b/c we're adding transactions.
    # - category_4: 'N' : 'Y' is more than 2:1.
    grouped = merchants_df.groupby(['merchant_id', 'merchant_group_id', 'merchant_category_id', 'subsector_id'])

    # In this grouping the catgory_1 and _4 groups never contain both 'N' and 'Y', but let's accumulate them
    # with sum_triples to remember it later.
    aggregated_df = grouped.agg({'numerical_1': np.mean,
                                 'numerical_2': np.mean,
                                 'category_1': sum_triples,
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
                                 'category_4': sum_triples})

    # I don't know how to keep the cat_triple type through sum_triples.
    aggregated_df['category_1'] = aggregated_df['category_1'].astype(cat_triple)
    aggregated_df['category_4'] = aggregated_df['category_4'].astype(cat_triple)

    # I especially don't understand why np.max on the values in cat_most_recent transforms
    # them into str again, but here we go:
    aggregated_df['most_recent_sales_range'] = aggregated_df['most_recent_sales_range'].astype(cat_most_recent)
    aggregated_df['most_recent_purchases_range'] = aggregated_df['most_recent_purchases_range'].astype(cat_most_recent)

    return aggregated_df
