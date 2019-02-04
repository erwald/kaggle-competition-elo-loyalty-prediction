import numpy as np
import pandas as pd
from fastai.tabular import add_datepart


def add_time_since_last_purchase(transactions_df):
    '''This function calculates, for each purchase, the time passed since the
    time elapsed since the last purchase with that card.

    The given data frame is mutated in place.
    '''
    print('Computing and adding `elapsed_since_last_purchase` column ...')

    filtered = transactions_df[['card_id', 'purchase_Elapsed']]
    grouped = filtered.groupby(['card_id'], sort=False)
    transactions_df['elapsed_since_last_purchase'] = grouped.agg(
        {'purchase_Elapsed': 'diff'})


def add_time_since_last_purchase_with_merchant(transactions_df):
    '''This function calculates, for each purchase, the time passed since the
    last purchase for that card and merchant combination, e.g. for a transaction
    of me buying toilet paper at Rewe (true story, by the way), it would be the
    time passed since I last bought anything at Rewe, or `nan` had I never
    bought anything there.

    The given data frame is mutated in place.
    '''
    print('Computing and adding `elapsed_since_last_merch_purchase` column.\n' +
          'This takes a hell of a long time ...')

    # Since `merchant_id` can be nan, we need to treat those as non-nan
    # temporarily in order not to drop rows when grouping. We also filter the
    # data frame, since we are only interested in these three columns.
    filtered = transactions_df[['card_id', 'merchant_id', 'purchase_Elapsed']]
    filtered['merchant_id'] = filtered['merchant_id'].cat.add_categories(
        'temp_nan').fillna('temp_nan')
    grouped = filtered.groupby(['card_id', 'merchant_id'], sort=False)

    # This takes a hell of a long time.
    transactions_df['elapsed_since_last_merch_purchase'] = grouped.agg(
        {'purchase_Elapsed': 'diff'})


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Join transactions data with merchants data.")
    parser.add_argument('transactions_csv', type=str,
                        help='Filename of the transactions csv.')
    parser.add_argument('outfile', type=str,
                        help='Filename of the result csv.')
    parser.add_argument('--calculate_time_since_purchase_with_merchant', action='store_true',
                        help='Whether or not to calculate time passed since card owner\'s last purchase with merchant.')
    parser.set_defaults(calculate_time_since_purchase_with_merchant=True)
    args = vars(parser.parse_args())

    trans_df = pd.read_csv(args['transactions_csv'],
                           parse_dates=['purchase_date'])

    # Suppress an annoying warning.
    pd.options.mode.chained_assignment = None  # default='warn'

    # Treat categorical fields as categorical.
    for v in ['authorized_flag', 'category_1', 'category_2', 'category_3',
              'merchant_id', 'merchant_category_id', 'subsector_id', 'city_id',
              'state_id']:
        trans_df[v] = trans_df[v].astype('category').cat.as_ordered()

    # This function takes a date field and turns it into a bunch of useful
    # columns, such as "day of week", "is month end", etc.
    add_datepart(trans_df, 'purchase_date')

    # Sort by date.
    trans_df.sort_values(by=['purchase_Elapsed'], inplace=True)

    # Add new column: time since last purchase (in general or per merchant).
    add_time_since_last_purchase(trans_df)
    if args['calculate_time_since_purchase_with_merchant']:
        add_time_since_last_purchase_with_merchant(trans_df)

    trans_df.to_csv(args['outfile'])
