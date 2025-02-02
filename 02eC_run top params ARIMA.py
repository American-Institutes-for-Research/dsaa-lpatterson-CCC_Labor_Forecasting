'''
02eC_ run top params ARIMA.py
run top 10 performing grid search params at each hierarchy level
'''

import pandas as pd
from model_statsmodels_arima_forecast_loop import run_ARIMA_loop

param_df = pd.read_csv("result_logs/batch_ARIMA grid search 12 month test/RMSE summary.csv")
param_df = param_df.drop(['cand_features_num','use_exog'], axis=1).drop_duplicates()
param_cols = ['auto_reg','moving_avg','trend']

param_dicts = []
for i, row in param_df.head(20).iterrows():
    param_dict = {}
    for p in param_cols:
        param_dict[p] = row[p]

    param_dicts.append(param_dict)
offset = 11
#param_dicts = param_dicts[offset:]
param_dicts = param_dicts[:offset]
#for lvl in ['category', 'subcategory', 'skill']:
for lvl in ['skill']:
    print(lvl)
    for n, params in enumerate(param_dicts):
        print('param set', n)
        try:
            run_ARIMA_loop(hierarchy_lvl=lvl, ccc_taught_only=False, max_diffs=0,
                           run_name='ARIMA top grid search runs 2023 #'+str(n), batch_name='ARIMA top grid search runs 2023',
                           analyze_results=True,viz_predictions=False,  test_tvalues=5, **params)
        except Exception as e:
            print('error with params:', p)
            print('error message:', e)
            #err_row = pd.Series(p)
            #err_row['error'] = e
            #error_tracker = error_tracker.append(err_row, ignore_index=True)
            continue
pass
