################################################################################
#                   Author: Joshua Thompson
#   O__  ----       Email:  joshua.thompson@ofwat.gov.uk
#  c/ /'_ ---
# (*) \(*) --
# ======================== Script  Information =================================
# PURPOSE: model 1:3 execute
#
# PROJECT INFORMATION:
#   Name: model 1:3 execute
#
# HISTORY:----
#   Date		        Remarks
#	-----------	   ---------------------------------------------------------------
#	 05/12/2024    Created script                                   JThompson (JT)
#===============================  Environment Setup  ===========================
#==========================================================================================
import pandas as pd
import numpy as np
import sys

# set file path for inflation function
sys.path.append(r"C:\Users\Joshua.Thompson\OneDrive - OFWAT\Documents\Python Scripts")
from inflation_data_ONS import get_deflation
from model1_function import model1
from model2_function import model2
from model3_function import model3

# model 1 
# read in model data (need to change this eventually to work with fabric)
data_file_path_model1 = r"C:\Users\Joshua.Thompson\OneDrive - OFWAT\Platform Modelling\models\models\model1.xlsx"
deflation = get_deflation()
inputData_model1 = pd.read_excel(data_file_path_model1, sheet_name="input Data", header=1).drop(columns=['Unnamed: 0'])

model1_result = model1(
    data=inputData_model1, 
    efficiency_seq=np.arange(0.970, 0.991, 0.001), # trim now for desktop testing: original - arange(0.985, 0.99, 0.001),
    limit_lineincrease_seq=np.arange(1.190, 1.211, 0.001), # trim now for desktop testing: original - arange(1.120, 1.205, 0.001)
    inflation_year='2022-23', 
    deflation=deflation,
    year_exclude = '2017-18'
)

# model 2
# read in model data (need to change this eventually to work with fabric)
data_file_path_model2 = r"C:\Users\Joshua.Thompson\OneDrive - OFWAT\Platform Modelling\models\models\model2.xlsx"
inputData_model2 = pd.read_excel(data_file_path_model2, sheet_name="input Data", header=1).drop(columns=['Unnamed: 0'])

model2_result = model2(
    data=inputData_model2, 
    efficiency_seq=np.arange(0.74, 0.76, 0.001), # trim now for desktop testing: original - arange(0.75, 0.76, 0.001)
    limit_lineincrease_seq=np.arange(1.110, 1.130, 0.001), # trim now for desktop testing: original - np.arange(1.120, 1.130, 0.001)
    inflation_year='2022-23', 
    deflation=deflation,
    year_exclude = '2017-18'
)


# model 3
company_return_range=np.arange(0.08, 0.12, 0.001)
#smoothing_dic = {  # trim for desktop test
#    1: {"2025-26": 0.95, "2026-27": 0.975, "2027-28": 1, "2028-29": 1.025, "2029-30": 1.05},
#    2: {"2025-26": 0.96, "2026-27": 0.98, "2027-28": 1, "2028-29": 1.02, "2029-30": 1.04}}

smoothing_dic = {
    1: {"2025-26": 0.95, "2026-27": 0.975, "2027-28": 1, "2028-29": 1.025, "2029-30": 1.05},
    2: {"2025-26": 0.96, "2026-27": 0.98, "2027-28": 1, "2028-29": 1.02, "2029-30": 1.04},
    3: {"2025-26": 0.97, "2026-27": 0.985, "2027-28": 1, "2028-29": 1.015, "2029-30": 1.03},
    4: {"2025-26": 0.98, "2026-27": 0.99, "2027-28": 1, "2028-29": 1.01, "2029-30": 1.02},
}  

model1_result['model'] = "model1"
model2_result['model'] = "model2"

model1_combinations = model1_result[['efficiency', 'limit_lineincrease']].drop_duplicates()
model2_combinations = model2_result[['efficiency', 'limit_lineincrease']].drop_duplicates()

# empty for store of data
model3results = []
n = 1
# cartesian pdt of m1 and m2 
for _, row1 in model1_combinations.iterrows():
    efficiency1 = row1['efficiency']
    limit_lineincrease1 = row1['limit_lineincrease']
    
    # filter model1
    subset_data1 = model1_result[
        (model1_result['efficiency'] == efficiency1) &
        (model1_result['limit_lineincrease'] == limit_lineincrease1)
    ]
    
    for _, row2 in model2_combinations.iterrows():
        n=n+1
        print(f"simulation: {n-1}")
        efficiency2 = row2['efficiency']
        limit_lineincrease2 = row2['limit_lineincrease']
        
        # filter model2
        subset_data2 = model2_result[
            (model2_result['efficiency'] == efficiency2) &
            (model2_result['limit_lineincrease'] == limit_lineincrease2)
        ]
        
        # combine data from model1 and model2
        combined_data = pd.concat([subset_data1, subset_data2], ignore_index=True)
        
        # execute model3
        final_dataset = model3(
            data=combined_data,
            smoothing_dic=smoothing_dic,
            company_return_range=company_return_range
        )
        
        final_dataset['model1_efficiency'] = efficiency1
        final_dataset['model1_limit_lineincrease'] = limit_lineincrease1
        final_dataset['model2_efficiency'] = efficiency2
        final_dataset['model2_limit_lineincrease'] = limit_lineincrease2
        
        # append 
        model3results.append(final_dataset)


mod3_results = pd.concat(model3results, ignore_index=True)
#mod3_results.to_csv('model3_output.txt', sep='\t', index=False)

