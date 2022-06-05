#!/usr/bin/env python
# coding: utf-8

# # Project: Housing Evictions and Fair Market Rents in New York City</h1> <a id=7></a>
# ## Mapping Tests for Eviction and FMR data</h3>
# 

# ##Page Summary:
# This page is meant to draft the mapping of both evictions and FMR datasets.

# ## Data:
# 
# For this project, we are utilizing data from two datasets (evictionlab.org and HUD) that both include zip code geolocators, in order to both map and analyze the data.  In order to make this happen, we needed to utilize a "crosswalk" dataset from HUD.gov in order to connect geographic areas.  Additionally, we will use ACS data for demographic information within each area.
# 
# Our first task is to read in and inspect the merged <b>Eviction Lab</b> and <b>FMR</b> dataset.  In the eviction dataset, there are 8428 unique observations and 7 variables, and in the merged dataset, there are 9744 observations across 21 columns.  

#%%


import pandas as pd         #quick stats       
import numpy as np      #numerical functions
import matplotlib.pyplot as plt    #visualization library
import seaborn as sns    #visualization and stats


#%%


get_ipython().run_line_magic('matplotlib', 'inline')

#%%


#load Evict_FMR_merged dataset
#path = '/Users/ameliaingram/Documents/My_GitHub+Repository/eviction-rent/assets/data/raw/Evict_FMR_merged.csv'

df = pd.read_csv(r'https://raw.githubusercontent.com/amelia-ingram/eviction-rent/main/assets/data/raw/Evict_FMR_merged.csv')            # read eviction data from online


#%%
#check basic summary of dataframe columns and datatypes
df.info()                               

#%%
# There are two main issues we see above. First, we can observe `GEOID` cases are essentially zip codes and a number of `GEOID` cases that are listed as "sealed".  According to the data dictionary from the Eviction Lab website, "A modest portion of filings are reported to us with missing, incorrect, or out-of-bounds addresses. In these cases, we do not assign a Census Tract or Zip code to the case." There were 29 sealed cases excluded for the purposes of merging and mapping.  If we wish to use the sealed sets, we can load the `f_evict` dataset below.<br>
# 
# Secondly, the `HUD Metro Area Name` actually changed for certain zip codes from year to year.  We kept those columns in the data for reference.  Not sure if it's important yet, but they're there.
# 
# The `month` variable includes both month and year data.  Will need to confirm they are usable in Python's date format.  The 'sealed' values from the `GEOID` column now has 896 null entries.  Hopefully this won't be a problem--it is relatively low.

# ### Check for missing values
# Before any initial analysis, we need to check for missing values from each dataset. In the merged dataset, there are no missing values.  However in the Evictions dataset, the controls `GEOID` and `racial_majority` had 896 missing values, and the rest are fine.  In the context of this large dataset these are acceptable missing amounts to continue to use everything. 

#%%


df.isnull().sum()        # confirm the number of NaN values for the df


#%%


#Convert 'GEOID' sealed entries into NaN
df['GEOID'] = df.GEOID.replace('sealed', np.nan)

df.isnull().sum()        # returns the number of NaN values for the df


# I will first rename `race_majority` to `race` in order to ease analysis.  Then, I will also add `counties` to the dataset by assigning zip codes to counties and then applying those as a function to the `GEOID` info for readability in the analysis and plots.

#%%


#rename ZIP and racial_majority column in Eviction dataset here
df = df.rename(columns={'ZIP':'zipcode','race_majority':'Race'})

df.columns

#%%
# Now the variables are ready to perform an initial exploratory analysis.  

# ## 1. Mapping of Eviction Data
# 
# 

#%%


#import packages for mapping
import geopandas as gp
import plotly.express as px
import json
#from urllib.request import urlopen    
import folium as fm
from folium.plugins import HeatMap


#%%


#load geojson dataset
from urllib.request import urlopen

with urlopen('https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/ny_new_york_zip_codes_geo.min.json') as response:
    geojson = json.load(response)
#local version: geojson = json.load(open('/Users/ameliaingram/Documents/My_GitHub+Repository/eviction-rent/assets/data/raw/new_york_zip_codes_geo.min.json'))


#%%


#map eviction filings by zipcode
fig = px.choropleth(df, geojson=geojson, locations='zipcode', color='filings_2020',
                           color_continuous_scale="Viridis", featureidkey='properties.ZCTA5CE10',
                           range_color=(0, 100),
                           scope="usa", center = {"lat": 40.81, "lon": -73.90},
                           labels={'filings_2020':'# Evictions'}
                          )
fig.update_geos(fitbounds="locations")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
fig.show()


#%%



#%%


#map eviction filings by zipcode
fig = px.choropleth(df, geojson=geojson, locations='zipcode', color='SAFMR22 2BR',
                           color_continuous_scale="Viridis",featureidkey='properties.ZCTA5CE10',
                           range_color=(0, 100), 
                           zoom=3, center = {"lat": 40.81, "lon": -73.90},
                           opacity=0.5, title='Fair Market Rent 2 BD 2022',
                           labels={'SAFMR22 2BR':'FMR 2022'}
                          )
fig.update_geos(fitbounds="locations")
fig.update_layout(margin={"r":0,"t":5,"l":0,"b":0})
fig.show()


# ### Map using Folium--Not working yet...

#%%


# Set zipcode type to string (folium)
df['zipcode'] = df['zipcode'].astype('str')

# get the mean value across all data points
zipcode_data = df.groupby('zipcode').aggregate(np.mean)
zipcode_data.reset_index(inplace = True)


#%%


# count number of filings_2020 grouped by zipcode
df['count'] = 1
temp = df.groupby('zipcode').sum('filings_2020')
temp.reset_index(inplace = True)
temp = temp[['zipcode', 'count']]
zipcode_data = pd.merge(zipcode_data, temp, on='zipcode')
# drop count from df dataset
df.drop(['count'], axis = 1, inplace = True)


#%%


# Get geojson data file path
geo_data_file = '/Users/ameliaingram/Documents/My_GitHub+Repository/eviction-rent/data/nyc-zip-code-tabulation-areas-polygons.geojson'
#load GEOJSON
with open(geo_data_file, 'r') as jsonFile:
    geo_data = json.load(jsonFile)

tmp = geo_data


#%%


#visualize distribution of evictions
def count_dist(df, location, filings_2020):
    group_counts = pd.DataFrame(df.groupby([location, filings_2020]).size().unstack(1))
    group_counts.reset_index(inplace = True)
    return group_counts

#function to return % racial distribution in each zip code...don't think this is accurate
def subgroup_distribution(df, location, racial_majority):
    group = df.groupby([location, racial_majority]).size()
    group_pcts = group.groupby(level=0).apply(lambda x: 100 * x/float(x.sum()))
    group_pcts = pd.DataFrame(group_pcts.unstack(1))
    group_pcts.reset_index(inplace=True)
    return group_pcts


#%%


def map_feature_by_zipcode(zipcode_data, col):
    """
    Generates a folium map of NYC
    :param zipcode_data: zipcode dataset
    :param col: feature to display
    :return: m
    """

    # Initialize Folium Map with NYC latitude and longitude
    m = folium.Map(location=[40.81, -73.90], zoom_start=9,
                   detect_retina=True, control_scale=False)

    # Create choropleth map
    m.choropleth(
        geo_data=geo_data,
        name='choropleth',
        data=zipcode_data,
        # col: feature of interest
        columns=['zipcode', 'group_counts', 'group_pcts'],
        key_on='feature.properties.ZIPCODE',
        fill_color='OrRd',
        fill_opacity=0.9,
        line_opacity=0.2,
        legend_name='Evictions' + col
    )

    folium.LayerControl().add_to(m)

    # Save map based on feature of interest
    m.save(col + '.html')

    return m


# Ended Here
# ==============================
# 
# ### Variable:  Evictions (filings_2020)
# `filings_2020` is the independent variable in this study.  The Eviction Lab data reports both filings_2020 which is a reported number per month since 2020 and filings_avg which is the average per month.  We are exploring both versions in this project.]

#%%


df2.filings_2020.describe()                          


# According to the preliminary descriptive statistics, evictions were on average 17.075 per zipcode, with a minimum of zero and a maximum of 550.  The interquartile range varied from 0 to 15 for the middle 50% of zipcodes.  

# In order to refine the evictions into a recognizable pattern, I will divide into five categorical levels of evictions (0, 1-9, 10-29, 30-59, 60-99, and >100). This will give a more detailed attention to the extreme ranges of evictions, in order to isolate these groups from the lower rates.

#%%


def evict_b(y):                                 
    '''
    INPUT: 
    y: int, from -1 to 550, the inputs of the int variable `filings_2020`
    
    OUTPUT:
    0 recoded to '<1'
    1-9 recoded to '1-9'
    10-29 recoded to '10-29'
    30-59 recoded to '30-59'
    60-99 recoded to '60-99'
    >100 recoded to '>100'
    '''
    if y == 0:
        return '0'
    if y >0 and y<10:
        return '1-9'
    elif y >= 10 and y<30:
        return '10-29'
    elif y >= 30 and y<60:
        return '30-59'
    elif y>=60 and y<100:
        return '60-99'
    elif y>=100:
        return '>100'
    else:
        return np.nan                        # missing is coded as nan 

# apply the function to `filings_2020`

df2['filings_cat'] = df2.filings_2020.apply(evict_b)


#%%


# double check whether the transformation is successful:

df2[['filings_cat']]


# Now that we have groups `filings_2020` into groups, let's see the resulting distribution. 

#%%


with plt.style.context('fast'):
    df2.groupby('filings_cat').size().plot(kind='bar')   #bar graph in order
plt.title('Eviction Rates by Groups (Eviction Lab 2020-2022)')
plt.xlabel('Eviction by Groups')
plt.ylabel('# Evictions')

#%%
# ## 6. References <a id=6></a>
# 
# ### Programming References:
# Matplotlib Style Sheets Reference.  https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html
# 
# Legend in Matplotlib.  https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html
# 
# Stats t-test in Scipy.  https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html

# 
# ### Datasets:
# Crosswalk Dataset of Zip to Tract. U.S. Department of Housing and Urban Development. Office of Policy Development and Research.  https://www.huduser.gov/portal/datasets/usps_crosswalk.html#data
# 
# "Fair Market Rents: 40th Percentile." U.S. Department of Housing and Urban Development. Office of Policy Development and Research. Datasets.  https://www.huduser.gov/portal/datasets/fmr.html#2022_data
# 
# Peter Hepburn, Renee Louis, and Matthew Desmond. Eviction Tracking System: Version 1.0. Princeton: Princeton University, 2020. www.evictionlab.org.
# 
# ### General Reference
# "Summary: Fair Market Rents." U.S. Department of Housing and Urban Development. Office of Policy Development and Research. Blog.  https://www.huduser.gov/periodicals/ushmc/winter98/summary-2.html 
# 
# U.S. Commission on Civil Rights. Racial Discrimination and Eviction Policies and Enforcement in New York. 10 Mar 2022.  https://www.usccr.gov/reports/2022/racial-discrimination-and-eviction-policies-and-enforcement-new-york
# 
# Zaveri, Mihir.  After a Two-Year Dip, Evictions Accelerate in New York. The New York Times. 2 May 2022. https://www.nytimes.com/2022/05/02/nyregion/new-york-evictions-cases.html
# 


# In[ ]:




