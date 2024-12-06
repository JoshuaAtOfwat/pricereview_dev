################################################################################
#                   Author: Joshua Thompson
#   O__  ----       Email:  joshua.thompson@ofwat.gov.uk
#  c/ /'_ ---
# (*) \(*) --
# ======================== Script  Information =================================
# PURPOSE: model 1 as function
#
# PROJECT INFORMATION:
#   Name: model 1 as function 
#
# HISTORY:----
#   Date		        Remarks
#	-----------	   ---------------------------------------------------------------
#	 03/1121/2024    Created script                                   JThompson (JT)
#===============================  Environment Setup  ===========================
#==========================================================================================

import pandas as pd
import numpy as np


def model1(
    data, 
    efficiency_seq, 
    limit_lineincrease_seq, 
    inflation_year, 
    deflation,
    year_exclude):
    # filter inflation data 
    inflation_value = deflation.loc[deflation['Fiscal_Year'] == inflation_year, 'inflation'].values[0]

    # List of APR and BPT item numbers
    item_numbers_APR = ['APRBCL1', 'APRBCL2', 'APRBCL3', 'APRBCL4', 'APRBCL5']
    item_numbers_BPT = ['BPTBCL1', 'BPTBCL2', 'BPTBCL3', 'BPTBCL4', 'BPTBCL5']

    # shell pandas df for reults
    results = pd.DataFrame()

    # loop through input vars for efficiency and line increase lims 
    for efficiency in efficiency_seq:
        for limit_lineincrease in limit_lineincrease_seq:
            input_data = data.copy()

            # inflate APR data with input inflation data and sekected year
            for company in input_data['company'].unique():
                company_data = input_data[(input_data['company'] == company) & (input_data['item number'].isin(item_numbers_APR))]
                input_data.loc[
                    (input_data['company'] == company) & (input_data['item number'].isin(item_numbers_APR)), 
                    'value'
                ] = company_data['value'] * inflation_value

            # aggregate cost per household (APR)
            denominator_APR = 'APRHH1'
            numerator_APRdata = input_data[input_data['item number'].isin(item_numbers_APR)]
            numerator_APRdata = numerator_APRdata[numerator_APRdata['year'] != year_exclude]
            numerator_APRdata_agg = numerator_APRdata.groupby(['company', 'item number'], as_index=False)['value'].sum()

            denominator_APRdata = input_data[input_data['item number'] == denominator_APR]
            denominator_APRdata = denominator_APRdata[denominator_APRdata['year'] != year_exclude]
            denominator_APRdata_agg = denominator_APRdata.groupby(['company', 'item number'], as_index=False)['value'].sum()

            merged_APRdata = pd.merge(
                numerator_APRdata_agg, 
                denominator_APRdata_agg[["company", "value"]], 
                on="company", 
                suffixes=('_numerator', '_denominator')
            )

            merged_APRdata['result'] = (merged_APRdata['value_numerator'] / merged_APRdata['value_denominator']) * 1000000
            cost_per_household_APR = merged_APRdata.drop(columns=['value_numerator', 'value_denominator'])

            # aggregate cost per household (BPT)
            denominator_BPT = 'BPTHH1'
            numerator_BPTdata = input_data[input_data['item number'].isin(item_numbers_BPT)]
            numerator_BPTdata = numerator_BPTdata[~numerator_BPTdata['year'].isin(['2023-24', '2024-25'])]
            numerator_BPTdata_agg = numerator_BPTdata.groupby(['company', 'item number'], as_index=False)['value'].sum()

            denominator_BPTdata = input_data[input_data['item number'] == denominator_BPT]
            denominator_BPTdata = denominator_BPTdata[~denominator_BPTdata['year'].isin(['2023-24', '2024-25'])]
            denominator_BPTdata_agg = denominator_BPTdata.groupby(['company', 'item number'], as_index=False)['value'].sum()

            merged_BPTdata = pd.merge(
                numerator_BPTdata_agg, 
                denominator_BPTdata_agg[["company", "value"]], 
                on="company", 
                suffixes=('_numerator', '_denominator')
            )

            merged_BPTdata['result'] = (merged_BPTdata['value_numerator'] / merged_BPTdata['value_denominator']) * 1000000
            cost_per_household_BPT = merged_BPTdata.drop(columns=['value_numerator', 'value_denominator'])

            #  merge cost per household (APR and BPT) and adjust future costs
            cost_per_household = cost_per_household_APR.copy()
            cost_per_household['item number BPT'] = cost_per_household_BPT['item number']
            cost_per_household['result_BPT'] = cost_per_household_BPT['result']
            cost_per_household = cost_per_household.rename(columns={'item number': 'item number APR', 'result': 'result_APR'})

            cost_per_household['div'] = ((cost_per_household['result_BPT'] / cost_per_household['result_APR'])*100)
            cost_per_household['int'] = (cost_per_household['div'] > (limit_lineincrease*100)).astype(int)

            cost_per_household['increase APR'] = cost_per_household.apply(
                lambda row: row['result_APR'] * (limit_lineincrease) if row['int'] == 1 else None, 
                axis=1)

            cost_per_household['increase BPT'] = cost_per_household.apply(
                lambda row: row['increase APR']/row['result_BPT'] if row['int'] == 1 else None, 
                axis=1)

            # accepted costs
            accepted_costs = input_data[input_data['item number'].isin(item_numbers_BPT)]
            accepted_costs = accepted_costs[~accepted_costs['year'].isin(['2023-24', '2024-25'])]
            accepted_costs = accepted_costs.merge(
                cost_per_household[['company', 'item number BPT', 'int', 'increase BPT']], 
                left_on=['company', 'item number'],  
                right_on=['company', 'item number BPT'],  
                how='left'
            )
            accepted_costs['calculated_value'] = np.where(
                accepted_costs['int'] == 0,  
                accepted_costs['value'],     
                np.where(
                    accepted_costs['increase BPT'].isna() | (accepted_costs['increase BPT'] == ''),  
                    accepted_costs['value'],  
                    accepted_costs['value'] * accepted_costs['increase BPT']  
                )
            )
            accepted_costs['customer_calculated_value'] = accepted_costs['calculated_value'] * efficiency

            # format data for export 
            limited_costs = accepted_costs[['company', 'item number BPT', 'year', 'unit', 'dp', 'calculated_value']]
            limited_costs['item number BPT'] = limited_costs['item number BPT'].str.replace('BPT', 'PRA')
            limited_costs.rename(columns={'item number BPT': 'item number', 'calculated_value': 'value'}, inplace=True)

            customer_costs = accepted_costs[['company', 'item number BPT', 'year', 'unit', 'dp', 'customer_calculated_value']]
            customer_costs['item number BPT'] = customer_costs['item number BPT'].str.replace('BPTBCL', 'PRCBLC')
            customer_costs.rename(columns={'item number BPT': 'item number', 'customer_calculated_value': 'value'}, inplace=True)

            final_data = pd.concat([limited_costs, customer_costs], ignore_index=True)
            final_data['efficiency'] = efficiency
            final_data['limit_lineincrease'] = limit_lineincrease-1

            # Append to results
            results = pd.concat([results, final_data], ignore_index=True)

    return results


