import numpy as np
import pandas as pd

def join_transactions_with_merchants(transactions_df, merchants_df):
    joined = pd.merge(transactions_df, merchants_df, on='merchant_id', how='left')
    joined_renamed = joined.rename(columns={'category_1_x': 'category_1_transaction',
                                            'category_1_y': 'category_1_merchant',
                                            'merchant_category_id_x': 'merchant_category_id_transaction',
                                            'merchant_category_id_y': 'merchant_category_id_x_merchant',
                                            'subsector_id_x': 'subsector_id_tranaction',
                                            'subsector_id_y': 'subsector_id_merchant'})
    return joined_renamed


if __name__=="__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Join transactions data with merchants data.")
    parser.add_argument('transactions_csv', type=str, help='Filename of the transactions csv')
    parser.add_argument('outfile', type=str, help='Filename of the result csv.')
    args = vars(parser.parse_args())

    merchants_df = pd.read_csv('data/processed/merchants.csv')
    trans_df = pd.read_csv(args['transactions_csv'])

    joined_df = join_transactions_with_merchants(trans_df, merchants_df)
    joined_df.to_csv(args['outfile'])
