import pandas as pd
import numpy as np


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
