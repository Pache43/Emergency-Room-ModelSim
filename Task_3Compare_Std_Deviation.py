import math
import simpy
import random
import os
import csv
import pandas as pd
import matplotlib.pyplot as plt

"""
    This part of the program is to compare the standard version of the different versions
    of Task 3 and produces graphic output
"""

#Loading raw patient from different Versions to dataframes
df_v0 = pd.read_csv(
        r'results\raw_Task1.csv',
        engine='python', sep=';', header=0)

df_v1 = pd.read_csv(
        r'results\raw_Task3.csv',
        engine='python', sep=';', header=0)
df_v2 = pd.read_csv(
        r'results\raw_Task3v2.csv',
        engine='python', sep=';', header=0)
df_v3 = pd.read_csv(
        r'results\raw_Task3v3.csv',
        engine='python', sep=';', header=0)
df_v4 = pd.read_csv(
        r'results\raw_Task3v4.csv',
        engine='python', sep=';', header=0)

version =[df_v0, df_v1, df_v2 ,df_v3 ,df_v4]
mean = []
std = []
#calculate mean and standard Deviation for the raw patient data
for dataframe in version:
        mean.append(dataframe["Total Time"].mean())
        std.append(dataframe["Total Time"].std())

#Name of different Version
version_name = ["No Priority","Priority 2nd Time CW","Priority CW always","Priority by Arrival Time in CW","Priority 2nd Time CW conditional"]

#barpolt for average Time per Version
plt.figure(figsize=(12, 9))
plt.grid(axis = "y", alpha = 0.5)
plt.title(label= "Average Time by Version",fontsize=20, pad=30)
plt.bar(version_name,height = mean,color="red", width= 0.5)
plt.xlabel(xlabel="Version",fontsize=20,labelpad = -5)
plt.xticks(rotation=12)
plt.ylabel(ylabel="Time(min)",fontsize=20, labelpad = 20)
plt.show()

#barplot for Standard Deviation per Verion
plt.figure(figsize=(12, 9))
plt.grid(axis = "y", alpha = 0.5)
plt.title(label= "Standard Deviation by Version",fontsize=20, pad=30)
plt.bar(x= version_name,height = std,label="Bars 1",color="blue", width = 0.5)
plt.xlabel(xlabel="Version",fontsize=20,labelpad = -5)
plt.xticks(rotation=12)
plt.ylabel(ylabel="Time(min)",fontsize=20, labelpad = 20)
plt.show()

#showing Table for Barplots
tmp_df =pd.DataFrame({'Version' : version_name,
                                'Mean' : mean,
                                'Standard Deviation' : std },
                                columns=['Version','Mean', 'Standard Deviation'])
tmp_df.set_index("Version", inplace= True)
print(tmp_df.to_string())