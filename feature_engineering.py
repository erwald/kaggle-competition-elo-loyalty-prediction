import pandas as pd
import numpy as np
import seaborn as sns


def add_aggregated_numerical_fields(df, hist_trans_df, column_names, aggregator):
    '''This function takes a data frame of card ids and one of historical
    transactions (of which there are multiple for every card), and then
    aggregates the transactions (only the given numerical columns) using a given
    function, e.g. mean() or sum() or similar.

    The given data frame is modified in place (iow, nothing is returned).
    '''
    merged = df.merge(hist_trans_df, how='left', on=['card_id'])
    aggregated = merged.groupby('card_id')[column_names].agg([aggregator])
    for col in column_names:
        df[f'{col}_{aggregator.__name__}'] = aggregated[col]


def add_aggregated_categorical_fields(df, hist_trans_df, column_names):
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
                df[f'{col}_{value}_count'] = counts[value]
                df[f'{col}_{value}_ratio'] = counts[value] / total
