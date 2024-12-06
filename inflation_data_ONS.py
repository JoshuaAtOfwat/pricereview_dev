################################################################################
#                   Author: Joshua Thompson
#   O__  ----       Email:  joshua.thompson@ofwat.gov.uk
#  c/ /'_ ---
# (*) \(*) --
# ======================== Script  Information =================================
# PURPOSE: Gather ONS inflation data 
#
# PROJECT INFORMATION:
#   Name: Gather ONS inflation data 
#
# HISTORY:----
#   Date		        Remarks
#	-----------	   ---------------------------------------------------------------
#	 29/11/2024    Created script                                   JThompson (JT)
#===============================  Environment Setup  ===========================
#==========================================================================================



import pandas as pd
import requests
from io import StringIO
import numpy as np

# url to ons data 
url = "https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/l522/mm23"

# user-agent as csv can't be directly read
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}

# get request for the data 
response = requests.get(url, headers=headers)

# check request code
if response.status_code == 200:
    # data to pandas 
    csv_data = StringIO(response.text)
    ONS_Data = pd.read_csv(csv_data, skiprows=7)  # Skip the first 7 rows

    # rename collumns
    ONS_Data = ONS_Data.rename(columns={
        "Important notes": "Period",
        "Unnamed: 1": "CPIH INDEX"
    })

    # subset on period where format is 'YYYY MMM'
    ONS_Data_filtered = ONS_Data[ONS_Data['Period'].str.match(r"^\d{4} [A-Z]{3}$", na=False)]

    # mutate period into 'Year' and 'Month'
    ONS_Data_filtered_split = ONS_Data_filtered.copy()
    ONS_Data_filtered_split[['Year', 'Month']] = ONS_Data_filtered_split['Period'].str.split(' ', expand=True)
    ONS_Data_filtered_split['Month'] = ONS_Data_filtered_split['Month'].str.title()

    # month to numeric values
    month_to_numeric = {month: i for i, month in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                                            'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 1)}
    ONS_Data_filtered_split['Month_numeric'] = ONS_Data_filtered_split['Month'].map(month_to_numeric)

    # change data type
    ONS_Data_filtered_split['Year'] = ONS_Data_filtered_split['Year'].astype(int)
    ONS_Data_filtered_split['CPIH INDEX'] = pd.to_numeric(ONS_Data_filtered_split['CPIH INDEX'], errors='coerce')

    # get fiscal year and calculate the average CPIH INDEX
    deflation = (
        ONS_Data_filtered_split
        .assign(Fiscal_Year=lambda df: np.where(df['Month_numeric'] >= 4, df['Year'] + 1, df['Year']))
        .query("Fiscal_Year >= 2016 and Fiscal_Year < 2025")
        .groupby('Fiscal_Year', as_index=False)
        .agg(FiscalYear_CPIH_INDEX=('CPIH INDEX', 'mean'))
    )

    # fiscal yaer format change to match fountain
    deflation['Fiscal_Year'] = deflation['Fiscal_Year'].apply(lambda x: f"{x-1}-{x % 100:02d}")

    # deflation relative to fiscal yr 2017-18
    base_cpi = deflation.loc[deflation['Fiscal_Year'] == "2017-18", 'FiscalYear_CPIH_INDEX'].values[0]
    deflation['deflation'] = base_cpi / deflation['FiscalYear_CPIH_INDEX']
    deflation['inflation'] = deflation['FiscalYear_CPIH_INDEX']/base_cpi

    # subset to >= 2017-18
    deflation = deflation[deflation['Fiscal_Year'] >= "2017-18"]
    
    def get_deflation():
        return deflation

else:
    print(f"Failed to fetch data. HTTP Status Code: {response.status_code}")
    def get_deflation():
        return None

