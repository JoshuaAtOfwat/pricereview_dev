################################################################################
#                   Author: Joshua Thompson
#   O__  ----       Email:  joshua.thompson@ofwat.gov.uk
#  c/ /'_ ---
# (*) \(*) --
# ======================== Script  Information =================================
# PURPOSE: model 3 function
#
# PROJECT INFORMATION:
#   Name: model 3 function
#
# HISTORY:----
#   Date		        Remarks
#	-----------	   ---------------------------------------------------------------
#	 05/12/2024    Created script                                   JThompson (JT)
#===============================  Environment Setup  ===========================
#==========================================================================================

import pandas as pd
import numpy as np

def model3(data, smoothing_dic, company_return_range):

    # get prefix
    prefixes = ('PRABCL', 'PRAECL', 'PRCBLC', 'PRCELC')
    data['prefix'] = data['item number'].apply(
        lambda x: next((prefix for prefix in prefixes if x.startswith(prefix)), None)
    )
    
    # filter and aggregate
    filt_df = data[data['prefix'].notna()]
    filt_df_grp = filt_df.groupby(['company', 'year', 'prefix'])['value'].sum().reset_index()
    filt_df_pvt = filt_df_grp.pivot(index=['company', 'year'], columns='prefix', values='value').reset_index()
    
    # final data
    final_data_list = []
    
    for company_return in company_return_range:
        # company return costs and charges to customers
        filt_df_pvt['company_return_costs'] = (filt_df_pvt['PRABCL'] + filt_df_pvt['PRAECL']) * company_return
        filt_df_pvt['charge_to_customers'] = (
            filt_df_pvt['PRCBLC'] + filt_df_pvt['PRCELC'] + filt_df_pvt['company_return_costs']
        )
        
        # average amp charges
        average_charge_by_company = filt_df_pvt.groupby('company')['charge_to_customers'].mean().reset_index()
        
        # apply smoothing factors
        smoothed_data = []
        for scenario, factors in smoothing_dic.items():
            for year, factor in factors.items():
                for _, row in average_charge_by_company.iterrows():
                    smoothed_charge = row['charge_to_customers'] * factor
                    smoothed_data.append({
                        "company": row['company'],
                        "year": year,
                        "value": smoothed_charge,
                        "scenario_smooth_value": scenario, 
                        "smooth_factor": factor
                    })
        smoothed_df = pd.DataFrame(smoothed_data)
        smoothed_df["item number"] = smoothed_df["company"] + "PRSMCT1"
        
        # format data (smooth)
        smooth_costs = smoothed_df.drop(columns=['scenario_smooth_value'])
        smooth_costs['unit'] = "£m 22-23 FYA CPIH"
        smooth_costs["dp"] = 3
        smooth_costs['company_return'] = company_return
        smooth_costs = smooth_costs[['company', 'item number', 'year', 'unit', 'dp', 'value', 'smooth_factor', 'company_return']]
        
        # format data (company return)
        company_return_data = filt_df_pvt.drop(columns=['PRABCL', 'PRAECL', 'PRCBLC', 'PRCELC', 'charge_to_customers'])
        company_return_data['unit'] = "£m 22-23 FYA CPIH"
        company_return_data["dp"] = 3
        company_return_data["item number"] = company_return_data["company"] + "PRCRCO1"
        company_return_data = company_return_data.rename(columns={'company_return_costs': 'value'})
        company_return_data['smooth_factor'] = None
        company_return_data['company_return'] = company_return
        company_return_data = company_return_data[['company', 'item number', 'year', 'unit', 'dp', 'value', 'smooth_factor', 'company_return']]
        
        # format data (customer charge)
        customers_charge = filt_df_pvt.drop(columns=['PRABCL', 'PRAECL', 'PRCBLC', 'PRCELC', 'company_return_costs'])
        customers_charge['unit'] = "£m 22-23 FYA CPIH"
        customers_charge["dp"] = 3
        customers_charge["item number"] = customers_charge["company"] + "PRCTCU1"
        customers_charge = customers_charge.rename(columns={'charge_to_customers': 'value'})
        customers_charge['smooth_factor'] = None
        customers_charge['company_return'] = company_return
        customers_charge = customers_charge[['company', 'item number', 'year', 'unit', 'dp', 'value', 'smooth_factor', 'company_return']]
        
        # final format
        final_data = pd.concat([smooth_costs, company_return_data, customers_charge], ignore_index=True)
        final_data_list.append(final_data)
    
    # Concatenate all results for different company_return values
    combined_data = pd.concat(final_data_list, ignore_index=True)
    return combined_data
