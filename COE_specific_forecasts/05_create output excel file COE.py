'''
05_create output excel file.py
Luke Patterson, 4-15-2023
Purpose:
'''

import pandas as pd
import numpy as np
import xlsxwriter
import os
basepath = 'C:/AnacondaProjects/CCC forecasting'
os.chdir(basepath)

coe_names = ['Business','Construction','Culinary & Hospitality','Education & Child Development','Engineering & Computer Science',
             'Health Science','Information Technology','Manufacturing','Transportation, Distribution, & Logistics']
for coe in coe_names:
    print(coe)
    scat_title = 'VAR_ARIMA ensemble '+coe+' subcategory level'
    cat_title = 'VAR_ARIMA '+coe+' category level'
    title = 'VAR_ARIMA ensemble '+coe+' skill level'
    min_obs = 50
    model_labels = ['VAR', 'ARIMA']
    output_label = 'VAR_ARIMA ensemble '+coe+' 2023 rerun results 09292023'

    # load ensemble model results for all three hierarchy levels
    cat_ensemble_df = pd.read_csv('output/predicted changes/ensemble results '+cat_title+'.csv', index_col=0)
    cat_ensemble_df.index = [i.replace('Skill cat: ','') for i in cat_ensemble_df.index]
    scat_ensemble_df = pd.read_csv('output/predicted changes/ensemble results '+scat_title+'.csv', index_col=0)
    scat_ensemble_df.index = [i.replace('Skill subcat: ','') for i in scat_ensemble_df.index]
    ensemble_df = pd.read_csv('output/predicted changes/ensemble results '+title+'.csv', index_col=0)
    ensemble_df.index = [i.replace('Skill: ','') for i in ensemble_df.index]

    # fix months to reflect the updated data months


    # load data frame of all skills/cats/subcats in the emsi taxonomy
    cat_df = pd.read_excel('emsi_skills_api/EMSI_skills_with_categories.xlsx')
    # skills = cat_df['name'].dropna().unique()
    # cats = cat_df['category_clean'].dropna().unique()
    # scats = cat_df['subcategory_clean'].dropna().unique()
    # cats_dict = {key:list() for key in cats}
    # scats_dict = {key:list() for key in scats}
    # # create dictionaries of all created categories and the skills within the
    # for label, row in cat_df.iterrows():
    #     # if not pd.isna(row.category_clean):
    #     #     cats_dict[row['category_clean']].append(row['name'])
    #     if not pd.isna(row.subcategory_clean):
    #         scats_dict[row['subcategory_clean']].append(row['name'])
    #     if not pd.isna(row.category_clean) and not pd.isna(row.subcategory_clean) and row['subcategory_clean'] not in \
    #         cats_dict[row['category_clean']]:
    #         cats_dict[row['category_clean']].append(row['subcategory_clean'])

    # create multi indexed dataframe with each unique value of all three levels of the skills hierarchy
    pred_df = cat_df[['category_clean','subcategory_clean','name']].rename(
        {
            'category_clean':'category',
            'subcategory_clean':'subcategory',
            'name':'skill'
        }
        ,axis=1
    )

    # merge in skill-level predictions
    pred_df = pred_df.merge(ensemble_df, left_on = 'skill', right_index= True)
    pred_df = pred_df.rename({'mean': 'Mean Salary'}, axis = 1)
    # add rows for the subcategory predictions
    scat_ensemble_df = scat_ensemble_df.reset_index().rename({'index':'subcategory'}, axis=1)
    # add categories of subcategories
    subcat_xwalk = cat_df[['category_clean','subcategory_clean']].drop_duplicates().rename({'category_clean':'category',
                                                                                            'subcategory_clean':'subcategory'}, axis=1)
    scat_ensemble_df = scat_ensemble_df.merge(subcat_xwalk, left_on = 'subcategory', right_on = 'subcategory')

    pred_df = pd.concat([scat_ensemble_df, pred_df])

    pred_df = pred_df.sort_values(['category','subcategory','skill'])

    # do some tricky sort things to get the subcategory predictions to appear at the top of their groups
    pred_df = pred_df.reset_index()
    pred_df = pred_df.groupby(['category', 'subcategory'], group_keys=False).apply(lambda x: x.sort_values(['index']))


    # add rows for category predictions
    cat_ensemble_df = cat_ensemble_df.reset_index().rename({'index':'category'}, axis=1)

    # add category predictions and sort to make sure they appear at the top of groups
    cat_ensemble_df = cat_ensemble_df.reset_index()
    pred_df = pred_df.drop('index',axis=1).reset_index(drop=True).reset_index()

    pred_df['index'] = pred_df['index'] + cat_ensemble_df.shape[0]
    pred_df = pd.concat([cat_ensemble_df,pred_df])

    # reorder columns
    #pred_df = pred_df[['index','category','subcategory', 'skill', 'July 2022 actual', 'July 2024 predicted',
    #'Percentage change','Percentage Point change', 'Monthly average obs', 'model','Normalized RMSE']]

    # pred_df = pred_df[['index','category','subcategory', 'skill', 'July 2022 actual', 'July 2024 weighted predicted',
    #        'Percentage change','Percentage Point change', 'Mean Salary', 'Monthly average obs', 'Most common occ',
    #        '2nd most common occ', '3rd most common occ',
    #        '4th most common occ', '5th most common occ', 'Most common ind',
    #        '2nd most common ind', '3rd most common ind', '4th most common ind',
    #        '5th most common ind','Prediction std dev']]
    pred_df = pred_df[['category','subcategory','skill'] + [i for i in pred_df.columns if i not in ['skill','subcategory','category']]]
    pred_df = pred_df.rename({'index':'scat_index'}, axis=1)
    pred_df = pred_df.groupby(['category'], group_keys=True).apply(lambda x: x.sort_values(['scat_index']))

    if 'scat_index' in pred_df.index:
        pred_df = pred_df.drop('scat_index')
    pred_df = pred_df.loc[pred_df['Monthly average obs'] > min_obs]

    # keep the name of the model embed                                                                                                                                                                                                                                                                                                                                                               ded in the model name
    if 'model' in pred_df.columns:
        pred_df['model'] = pred_df.model.apply(lambda x: [i for i in x.split(' ') if i in model_labels][0])
    pred_df = pred_df.drop('scat_index',axis=1).reset_index(drop=True).reset_index().rename({'index':'rownum'}, axis=1)
    pred_df['rownum'] = pred_df.rownum + 2

    # identify row numbers of groups for categories and subcategories
    # cat_groups = []
    # scat_groups = []
    # for cat in pred_df.category.unique():
    #     cat_groups.append(pred_df.loc[(pred_df.category == cat)].rownum.values)
    #
    # for scat in pred_df.subcategory.unique():
    #     scat_groups.append(pred_df.loc[pred_df.subcategory == scat].rownum.values)

    # turns out excel groupings need to have summary rows for category and subcategory at the bottom of the group, so we
    # will resort accordingly


    # merge EMSI ID variables onto the data
    id_df = pd.read_excel('emsi_skills_api/EMSI_skills_with_categories.xlsx')
    pred_df = pred_df.merge(id_df[['name','id']], left_on = 'skill', right_on='name', how = 'left')
    pred_df = pred_df.drop('name', axis = 1).rename({'id':'EMSI_id'}, axis = 1)
    pred_df = pred_df[list(pred_df.columns[0:3])+['EMSI_id']+list(pred_df.columns[3:-1])]

    pred_df = pred_df.sort_values(['category','subcategory','skill']).drop('rownum',axis=1)
    writer = pd.ExcelWriter('output/exhibits/'+output_label+'.xlsx', engine='xlsxwriter')
    workbook = writer.book

    pred_df.to_excel(writer, sheet_name='Grouped Skills', index= False)
    worksheet = writer.sheets['Grouped Skills']

    # add groupings
    for n, row in pred_df.iterrows():
        if pd.isna(row.subcategory):
            worksheet.set_row(n, None, None, {'level': 0})
        elif pd.isna(row.skill):
            worksheet.set_row(n, None, None, {'level': 1, 'hidden':True})
        else:
            worksheet.set_row(n, None, None, {'level': 2, 'hidden':True})

    # set summary row of each group as the top row
    #worksheet.outline_settings(True, False, True, False)

    # format columns to be rounded to six decimal places
    #format1 = workbook.add_format({'num_format': '0.000000'})
    #worksheet.set_column('D:I', None, format1)

    # autofit column widths
    for column in pred_df:
        column_length = max(pred_df[column].astype(str).map(len).max(), len(column))
        col_idx = pred_df.columns.get_loc(column)
        writer.sheets['Grouped Skills'].set_column(col_idx, col_idx, column_length)

    # add all predictions for each hierarchy as a separate sheet
    cat_ensemble_df = cat_ensemble_df.drop('index', axis=1)
    cat_ensemble_df = cat_ensemble_df.sort_values('Percentage Point change', ascending = False)

    # merge in category id's
    # transform to dict objects
    cat_ids = pd.DataFrame([eval(i) for i in id_df['category'].unique() if not pd.isna(i)])
    cat_ensemble_df = cat_ensemble_df.merge(cat_ids, left_on = 'category', right_on = 'name')
    cat_ensemble_df = cat_ensemble_df.drop('name', axis = 1).rename({'id':'EMSI_cat_id'}, axis = 1)
    cat_ensemble_df = cat_ensemble_df[list(cat_ensemble_df.columns[0:1])+['EMSI_cat_id']+list(cat_ensemble_df.columns[1:-1])]

    #cat_ensemble_df['model'] = cat_ensemble_df.model.apply(lambda x: [i for i in x.split(' ') if i in model_labels][0])
    cat_ensemble_df.to_excel(writer, sheet_name='Category', index= False)
    worksheet = writer.sheets['Category']
    for column in cat_ensemble_df:
        column_length = max(cat_ensemble_df[column].astype(str).map(len).max(), len(column))
        col_idx = cat_ensemble_df.columns.get_loc(column)
        writer.sheets['Category'].set_column(col_idx, col_idx, column_length)
    #worksheet.set_column('C:H', None, format1)

    # scat_ensemble_df = scat_ensemble_df[['subcategory', 'category', 'July 2022 actual', 'July 2024 predicted',
    #        'Percent change', 'Monthly average obs']]
    # scat_ensemble_df = scat_ensemble_df[['subcategory', 'category', 'July 2022 actual', 'July 2024 weighted predicted',
    #        'Percentage change','Percentage Point change', 'Mean Salary', 'Monthly average obs', 'Most common occ',
    #        '2nd most common occ', '3rd most common occ',
    #        '4th most common occ', '5th most common occ', 'Most common ind',
    #        '2nd most common ind', '3rd most common ind', '4th most common ind',
    #        '5th most common ind','Prediction std dev']]

    scat_ensemble_df = scat_ensemble_df[['subcategory','category'] + [i for i in scat_ensemble_df.columns if i not in ['skill','subcategory','category']]]
    scat_ensemble_df = scat_ensemble_df.sort_values('Percentage Point change', ascending = False)
    #scat_ensemble_df['model'] = scat_ensemble_df.model.apply(lambda x: [i for i in x.split(' ') if i in model_labels][0])

    # merge in subcategory id's
    # transform to dict objects
    scat_ids = pd.DataFrame([eval(i) for i in id_df['subcategory'].unique() if not pd.isna(i)])
    scat_ensemble_df = scat_ensemble_df.merge(scat_ids, left_on = 'subcategory', right_on = 'name')
    scat_ensemble_df = scat_ensemble_df.drop('name', axis = 1).rename({'id':'EMSI_scat_id'}, axis = 1)
    scat_ensemble_df = scat_ensemble_df[list(scat_ensemble_df.columns[0:2])+['EMSI_scat_id']+list(scat_ensemble_df.columns[2:-1])]

    scat_ensemble_df.to_excel(writer, sheet_name='Subcategory', index= False)
    worksheet = writer.sheets['Subcategory']
    for column in scat_ensemble_df:
        column_length = max(scat_ensemble_df[column].astype(str).map(len).max(), len(column))
        col_idx = scat_ensemble_df.columns.get_loc(column)
        writer.sheets['Subcategory'].set_column(col_idx, col_idx, column_length)
    #worksheet.set_column('D:I', None, format1)

    ensemble_df = ensemble_df.merge(cat_df[['category_clean','subcategory_clean','name']], left_index=True, right_on='name')
    ensemble_df = ensemble_df.rename({'category_clean':'category','subcategory_clean':'subcategory','name':'skill'},axis=1)
    # ensemble_df = ensemble_df[['skill','category', 'subcategory', 'July 2022 actual', 'July 2024 predicted', 'Percent change',
    #        'Monthly average obs', 'model', 'Normalized RMSE']]
    # ensemble_df = ensemble_df[['skill','subcategory', 'category', 'July 2022 actual', 'July 2024 weighted predicted',
    #        'Percentage change','Percentage Point change', 'Mean Salary', 'Monthly average obs', 'Most common occ',
    #        '2nd most common occ', '3rd most common occ',
    #        '4th most common occ', '5th most common occ', 'Most common ind',
    #        '2nd most common ind', '3rd most common ind', '4th most common ind',
    #        '5th most common ind','Prediction std dev']]
    ensemble_df = ensemble_df[['skill','subcategory','category'] + [i for i in ensemble_df.columns if i not in ['skill','subcategory','category']]]
    ensemble_df = ensemble_df.sort_values('Percentage Point change', ascending = False)

    ensemble_df = ensemble_df.merge(id_df[['name','id']], left_on = 'skill', right_on='name')
    ensemble_df = ensemble_df.drop('name', axis = 1).rename({'id':'EMSI_id'}, axis = 1)
    ensemble_df = ensemble_df[list(ensemble_df.columns[0:3])+['EMSI_id']+list(ensemble_df.columns[3:-1])]
    #ensemble_df['model'] = ensemble_df.model.apply(lambda x: [i for i in x.split(' ') if i in model_labels][0])
    ensemble_df.to_excel(writer, sheet_name='Skill', index= False)
    worksheet = writer.sheets['Skill']
    for column in ensemble_df:
        column_length = max(ensemble_df[column].astype(str).map(len).max(), len(column))
        col_idx = ensemble_df.columns.get_loc(column)
        writer.sheets['Skill'].set_column(col_idx, col_idx, column_length)
    #worksheet.set_column('C:H', None, format1)

    # close the workbook
    workbook.close()
    pass
