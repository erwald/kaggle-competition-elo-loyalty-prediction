import pandas as pd
import numpy as np
from fastai.tabular import add_datepart


def add_aggregated_numerical_fields(df, hist_trans_df, aggregators, prefix=''):
    '''This function takes a data frame of card ids and one of historical
    transactions (of which there are multiple for every card), and then
    aggregates the transactions (only the given numerical columns) using the
    given aggregator functions, e.g. mean() or sum() or similar.

    The aggregators argument, iow, is a map of columns as keys and a list of
    aggregator functions as values.

    The given data frame is modified in place (iow, nothing is returned).
    '''
    merged = df.merge(hist_trans_df, how='left', on=['card_id'])
    aggregated = merged.groupby('card_id').agg(aggregators)
    for col, funcs in aggregators.items():
        for f in funcs:
            df[f'{prefix}{col}_{f}'] = aggregated[col][f]


def add_aggregated_categorical_fields(df, hist_trans_df, column_names, prefix=''):
    '''This function takes a data frame of card ids and one of historical
    transactions (of which there are multiple for every card), and then
    aggregates the transactions (only the given categorical columns) by summing
    the number of occurrences for each possible value and category.

    For instance, if we have a categorical column that can be either 'Y' or 'N',
    this would create one 'Y_count' and one 'N_count' column, each of which
    contains the number of occurrences of that value for the given card.

    The given data frame is modified in place (iow, nothing is returned).
    '''
    merged = df.merge(hist_trans_df, how='left', on=['card_id'])
    for col in column_names:
        values = hist_trans_df[col].unique()
        # 0 is not always a good default.
        counts = merged.groupby(['card_id', col]).size().unstack(fill_value=0)
        # Get total occurences of all values for the column.
        total = counts.sum(axis=1)
        for value in values:
            # Ignore nan. We should maybe handle this in a better way.
            if not pd.isnull(value):
                df[f'{prefix}{col}_{value}_ratio'] = counts[value] / total


def add_top_categories(df, hist_trans_df, column_names, prefix=''):
    '''This function takes a data frame of card ids and one of historical
    transactions (of which there are multiple for every card), and then, for
    each card and each given column, picks out the most commonly occurring value
    for that permutation.
    '''
    merged = df.merge(hist_trans_df, how='left', on=['card_id'])
    grouped = merged.groupby('card_id')
    for col in column_names:
        top_vals = grouped[col].apply(lambda x: x.mode().iat[0])
        df[f'{prefix}{col}_top'] = top_vals.astype('category').cat.as_ordered()


def process_data(df, hist_trans_df, merch_trans_df):
    # Extract more useful information from the `first_active_month` date field.
    add_datepart(df, 'first_active_month')
    df.drop(['first_active_monthDay',
             'first_active_monthDayofweek',
             'first_active_monthDayofyear',
             'first_active_monthIs_month_end',
             'first_active_monthIs_month_start',
             'first_active_monthIs_quarter_end',
             'first_active_monthIs_year_end'],
            axis=1, inplace=True)

    # Do feature engineering by aggregating data from the transactions tables.

    aggs = {
        'purchase_amount': ['sum', 'mean', 'min', 'max', 'std'],
        'installments': ['sum', 'mean', 'min', 'max', 'std'],
        'month_lag': ['mean', 'min', 'max'],
        'merchant_id': ['nunique'],
        'state_id': ['nunique'],
        'city_id': ['nunique'],
    }

    # First up we aggregate the data in the `historical_transactions` table.
    hist_trans_aggs = {
        'merchant_category_id': ['nunique'],
        'subsector_id': ['nunique'],
        'elapsed_since_last_purchase': ['sum', 'mean', 'min', 'max', 'std'],
        'elapsed_since_last_merch_purchase': ['sum', 'mean', 'min', 'max', 'std'],
    }
    print('Aggregating numerical fields from the historical transactions ...')
    add_aggregated_numerical_fields(df,
                                    hist_trans_df,
                                    aggregators={**aggs, **hist_trans_aggs})

    # For the categorical fields, we can't aggregate by taking the mean or sum
    # values, so let's count the occurences of each possible categorical value
    # instead. (Iow, for a category that can be either YES or NO, we count the
    # number of YESes and the number of NOs and use those values.)
    print('Aggregating categorical fields from the historical transactions ...')
    add_aggregated_categorical_fields(df,
                                      hist_trans_df,
                                      column_names=['authorized_flag',
                                                    'category_1',
                                                    'category_2',
                                                    'category_3'])
    add_top_categories(df,
                       hist_trans_df,
                       column_names=['authorized_flag',
                                     'category_1',
                                     'subsector_id',
                                     'city_id',
                                     'state_id',
                                     'purchase_Year',
                                     'purchase_Month',
                                     'purchase_Week',
                                     'purchase_Day',
                                     'purchase_Dayofweek'])

    # Next we aggregate the data in the `new_merchants_transactions` table.
    merch_trans_aggs = {
        'category_1_transaction': ['nunique'],
        'category_2': ['nunique'],
        'category_3': ['nunique'],
        'category_4': ['nunique'],
        'merchant_category_id_transaction': ['nunique'],
        'merchant_category_id_merchant': ['nunique'],
        'merchant_group_id': ['nunique'],
        'subsector_id_merchant': ['nunique'],
        'category_1_merchant': ['nunique'],
        'state_id': ['nunique'],
        'elapsed_since_last_purchase': ['sum', 'mean', 'min', 'max', 'std'],
        'numerical_1': ['sum', 'mean', 'min', 'max', 'std'],
        'numerical_2': ['sum', 'mean', 'min', 'max', 'std'],
        'avg_sales_lag3': ['sum', 'mean', 'min', 'max', 'std'],
        'avg_purchases_lag3': ['sum', 'mean', 'min', 'max', 'std'],
        'active_months_lag3': ['sum', 'mean', 'min', 'max', 'std'],
        'avg_sales_lag6': ['sum', 'mean', 'min', 'max', 'std'],
        'avg_purchases_lag6': ['sum', 'mean', 'min', 'max', 'std'],
        'active_months_lag6': ['sum', 'mean', 'min', 'max', 'std'],
        'avg_sales_lag12': ['sum', 'mean', 'min', 'max', 'std'],
        'avg_purchases_lag12': ['sum', 'mean', 'min', 'max', 'std'],
        'active_months_lag12': ['sum', 'mean', 'min', 'max', 'std'],
    }
    print('Aggregating numerical fields from the new merchant transactions ...')
    add_aggregated_numerical_fields(df,
                                    merch_trans_df,
                                    aggregators={**aggs, **merch_trans_aggs},
                                    prefix='merch_')

    # These ones don't work for the new_merchant_transactions for some reason
    # (missing data?), so let's skip them for now ...
    # add_aggregated_categorical_fields(df,
    #                                   merch_trans_df,
    #                                   column_names=['category_1_transaction', 'merchant_category_id_transaction',
    #                                                 'state_id', 'purchase_Year', 'month_lag'],
    #                                   prefix='merch_')

    # add_top_categories(df,
    #                    merch_trans_df,
    #                    column_names=['category_1_transaction', 'merchant_category_id_transaction',
    #                                  'state_id', 'purchase_Year', 'month_lag'],
    #                    prefix='merch_')


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Join transactions data with merchants data.")
    parser.add_argument('train_df', type=str,
                        help='Filename of the train (or test) csv.')
    parser.add_argument('hist_trans_df', type=str,
                        help='Filename of the historical transactions csv.')
    parser.add_argument('merch_trans_df', type=str,
                        help='Filename of the new merchant transactions csv.')
    parser.add_argument('outfile', type=str,
                        help='Filename of the result csv.')
    args = vars(parser.parse_args())

    # Load csv files.
    train_df = pd.read_csv(args['train_df'],
                           index_col='card_id',
                           parse_dates=['first_active_month'])
    hist_trans_df = pd.read_csv(args['hist_trans_df'])
    merch_trans_df = pd.read_csv(args['merch_trans_df'])

    process_data(train_df, hist_trans_df, merch_trans_df)

    train_df.to_csv(args['outfile'])
