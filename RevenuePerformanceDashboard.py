from bokeh.io import show, output_file
from bokeh.plotting import figure
from bokeh.models import *

import datetime
import requests
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth1

import pandas as pd

import json
import os
import time
import argparse

# Global Variables for locally stored api keys

def api_keys():
    with open('mopub_api_key.txt') as file:
        mopub_api_key = file.read()
    
    with open('mopub_inventory_report_id.txt') as file:
        mopub_inventory_report_id = file.read()
        
    with open('fyber_video_username.txt') as file:
        fyber_video_username = file.read()
        
    with open('fyber_video_password.txt') as file:
        fyber_video_password = file.read()
        
    with open('fyber_display_publisher_id.txt') as file:
        fyber_display_publisher_id = file.read()
    
    with open('fyber_display_consumer_key.txt') as file:
        fyber_display_consumer_key = file.read()
        
    with open('fyber_display_consumer_secret.txt') as file:
        fyber_display_consumer_secret = file.read()
        
    return (mopub_api_key, mopub_inventory_report_id, fyber_video_username, 
            fyber_video_password, fyber_display_publisher_id, 
            fyber_display_consumer_key, fyber_display_consumer_secret)

# Arg Parsing
parser = argparse.ArgumentParser(description='Enter start date and end date' \
                                 'of the dashboard you want to create')

parser.add_argument('-s', '--start_date', type=str, metavar='', required=True, 
                    help="Enter start date in 'YYYY-MM-DD format")

parser.add_argument('-e', '--end_date', type=str, metavar='', required=True, 
                    help="Enter end date in 'YYYY-MM-DD format'")
args = parser.parse_args()

def fetch_mopub_report(start_date, end_date, mopub_inventory_report_id, 
                       mopub_api_key):
    """
    Selects Data for the specifid time frame from the inventory report id
    that's pre-made in mopub. MoPub's API is interesting 
    because it selects dates one at a time, so if you have multiple
    days, they will be downloaded as individual files. Must be in 
    valid isoformat, meaning 'YYYY-MM-DD', else it won't work.
    """
    start_date = datetime.datetime.fromisoformat(start_date)
    end_date = datetime.datetime.fromisoformat(end_date)

    date_range = end_date - start_date

    days = date_range.days

    single_day = datetime.timedelta(days=1)
    d = start_date
    date_string_container = []
    for num in range(days+1):
        d_string = d.strftime('%Y-%m-%d')
        # print(d_string)
        date_string_container.append(d_string)
        d += single_day
    
    df_container = []
    
    for date in date_string_container:
        print("Fetching MoPub data for {}...".format(date))
        csv_url = 'https://app.mopub.com/reports/custom/api/download_report?report_key={}&api_key={}&date={}'.format(mopub_inventory_report_id, mopub_api_key, date)
        df = pd.read_csv(csv_url)
        df_container.append(df)
        
    df_concat = pd.concat(df_container, axis=0)
    
    return df_concat

def mopub_dataframe_cleaner(dataframe):
    """Cleans MoPub data and puts it in a common format"""
    print("Cleaning Mopub data...")
    df = dataframe
    df['App'] = df.App.map({"IMVU iOS - #1 3D Avatar Social App":'IMVU iOS', 
      "IMVU Android - #1 3D Avatar Social App":"IMVU Android"})
      
    df['Total_Code_Served'] = df['Requests']
    df['Partner'] = 'MoPub'
    
    df = df.rename(columns={'App ID':"App_ID", "AdUnit ID":"AdUnit_ID", 
                            'AdUnit Format':"AdUnit_Format"})

    df_pivot = df.pivot_table(index=['Day', 'App', 'AdUnit', 'AdUnit_Format', 
                                     'Country', 'Partner'],     
                              values=['Total_Code_Served', 'Requests', 
                                      'Impressions', 'Clicks', 'Revenue'],                                       
                              aggfunc='sum')

    df_pivot.to_csv("mopub-pivot.csv")

    df = pd.read_csv("mopub-pivot.csv")

    df = df.rename(columns={
        'AdUnit_Format':'UnitType'})

    df['UnitType'] = df.UnitType.map({'Banner':'banner',
      'Native':'native', 'Rewarded video': 'video'})

    df = df[['Day', 'App', 'AdUnit', 'UnitType', 'Country', 'Total_Code_Served',
           'Requests', 'Impressions', 'Clicks', 'Revenue', 'Partner']]
    
    os.remove("mopub-pivot.csv")

    return df

def fetch_fyber_video_report(start_date, end_date, fyber_video_username, 
        fyber_video_password):
    """Fectches data from the Fyber video SSP"""
    print(f"Fetching Fyber Video data from {start_date} to {end_date}...")
    url = 'https://api.fyber.com/publishers/v2/reporting/publisher-kpis.json?since={}&until={}'.format(start_date, end_date)
    r = requests.get(url, auth=HTTPBasicAuth(fyber_video_username, fyber_video_password))
    j = json.loads(r.text)
    dataframe = pd.DataFrame(j['data'])
    return dataframe

def fyber_video_dataframe_cleaner(dataframe):
    """Cleans/Normalizes data from the Fyber Video SSP"""
    print("Cleaning Fyber Video...")
    df = dataframe
    df = df.fillna(0)
    
    delete_list = ['application_id', 'completions', 'ecpm_eur', 'ecpm_usd', 
                   'fills', 'revenue_eur', 'unique_impressions']
    
    for entry in delete_list:
        del df[entry]
        
    df['Ad Type'] = 'video'
    df['Partner'] = 'Fyber_Video'
    df['Total_Code_Served'] = 0
    df['Clicks'] = 0
    
    df = df.rename(columns={'date':'Day', 'application_name':'App',
                            "ad_format":"AdUnit",  "Ad Type":"UnitType", 
                            "country":"Country", "requests":"Requests", 
                            "impressions":"Impressions", "clicks":"Clicks", 
                            "revenue_usd":"Revenue"})
    
    df['App'] = df['App'].replace({"IMVU iOS Primary Wall":"IMVU iOS", 
                                   "IMVU iOS External Offer Wall":"IMVU iOS", 
                                   "IMVU Google Play":"IMVU Android"}) 

    df['Impressions'] = df['Impressions'].apply(lambda x:int(x))
    df['Requests'] = df['Requests'].apply(lambda x:int(x))

    df = df[["Day", "App", "AdUnit", "UnitType", "Country", 
             "Total_Code_Served", "Requests", "Impressions", 
             "Clicks", "Revenue", "Partner"]]

    drop_index_list = []
    for num in list(df.index):
        if df.loc[num, 'App'] == 'Blue Bar Bundle ' or df.loc[num, 'App'] == 'NEXT Featured Offers':
            drop_index_list.append(num)

    df = df.drop(drop_index_list, axis=0)

    return df

def fetch_fiber_display_report(start_date, end_date, 
                               fyber_display_publisher_id, 
                               fyber_display_consumer_key, 
                               fyber_display_consumer_secret):
    """Fectches data from the Fyber display (inner-active) SSP"""
    print(f"Fetching Fyber Display data from {start_date} to {end_date}...")
    start_date = datetime.datetime.fromisoformat(start_date)
    end_date = datetime.datetime.fromisoformat(end_date)
    
    #subtraction is for the time difference - MoPub and Fyber Video are on PST    
    start_date_unixtime = int(time.mktime(start_date.timetuple()))-14400 
    end_date_unixtime = datetime.datetime.timestamp(end_date)
    url = 'https://console.inner-active.com/iamp/services/performance/publisher/{}/{}/{}'.format(fyber_display_publisher_id,start_date_unixtime, end_date_unixtime)
    headers = {"Content-type":"application/json","Accept":"application/json"}
    auth = OAuth1(fyber_display_consumer_key, fyber_display_consumer_secret) 
    r = requests.get(url, auth=auth, headers=headers)
    data = json.loads(r.text)
    dataframe = pd.DataFrame(data)
    return dataframe

def fyber_display_dataframe_cleaner(dataframe):
    """Cleans / Normalizes data from the Fyber display (inner-active) SSP"""
    print("Cleaning Fyber Display...")
    df = dataframe
    
    delete_list = ['contentCategories', 'contentId', 'contentName', 'publisherId', 
                   'distributorName', 'ecpm', 'ctr', 'fillRate']
    
    for entry in delete_list:
        del df[entry]

    df['App'] = 'IMVU iOS'
    df['Partner'] = 'Fyber'
    df['Total_Code_Served'] = 0
    df['UnitType'] = 'banner'

    df = df.rename(columns={'adRequests':'Requests', 'applicationName':'AdUnit', 
                            "clicks":"Clicks", "country":"Country", 'date':'Day', 
                            "revenue":"Revenue", "impressions":"Impressions"})

    df = df[['Day', 'App', 'AdUnit', 'UnitType', 'Country', 'Total_Code_Served',
           'Requests', 'Impressions', 'Clicks', 'Revenue', 'Partner']]
    
    df['Day'] = pd.to_datetime(df['Day'], unit='s')
    df['Day'] = df['Day'].apply(lambda x: x.date())
    
    return df

def bokeh_dashboard_creator(dataframe):
    """
    This creates the charts / graphs based off the data we pulled from the
    various APIs and writes the data to csv files for further analysis, if 
    needed. Bokeh makes JavaScript charts that are interactive and look much 
    slicker than, say, matplotlib. It's also a lot more complicated
    and with many more lines of code. This func. makes three charts:
    
    1. Revenue, Impressions by Day by Partner
    2. Revenue by Day by Ad Unit Type 
    3. Revenue by App
    
    The code for each is seperated by number-sign boxes. 
    """
    ############################################
    # Revenue, Impressions by Day by Partner
    ############################################
    
    output_file("dashboard.html")
    
    df = dataframe
    df['Day'] = pd.to_datetime(df['Day'])
    df = df.fillna(0)
    
    impressions_list = df.groupby('Day').Impressions.sum().tolist()
    revenue_list = df.groupby('Day').Revenue.sum().tolist()

    df_pivot = df.pivot_table(index=['Day'], columns='Partner', 
                              values=['Revenue'], aggfunc='sum')

    df_pivot = df_pivot.fillna(0)

    df_pivot['Impressions'] = impressions_list
    df_pivot['Total_Revenue'] = revenue_list
    
    df_pivot.to_csv("revenue-by-day-by-partner.csv")
    df2 = pd.read_csv("revenue-by-day-by-partner.csv", skiprows=2)
    
    df2['Day'] = pd.to_datetime(df2['Day'])
    df2 = df2.fillna(0)
    spectral_switch = ['#2b83ba', '#abdda4', '#fdae61']

    df2.columns = ['Day', 'Fyber', 'Fyber_Video', 'MoPub', 
                   'Impressions', 'Total_Revenue']

    df2['Day'] = pd.to_datetime(df2['Day'])

    source = ColumnDataSource(df2)

    colors=spectral_switch

    partners = ["Fyber", "Fyber_Video", "MoPub"]

    hover = HoverTool(tooltips=
                     [
                         ('Date','@Day{ %F }'),
                         ('MoPub','@MoPub{$0,0.00}'),
                         ('Fyber Video','@Fyber_Video{$0,0.00}'),
                         ('Fyber','@Fyber{$0,0.00}'),                     
                         ('Total Revenue','@Total_Revenue{$0,0.00}'),
                         ('Impressions', '@Impressions{0,}'),
                     ],

                      formatters={'Day':'datetime'},


                     )

    p = figure(plot_width=1000, plot_height=400, x_axis_type='datetime', 
               toolbar_location = 'above', tools=[hover], 
               y_range = (0, df2['Total_Revenue'].max()+500))

    #Title
    p.title.text = 'IMVU Mobile Ad Revenue by Date, Impressions'
    p.title.text_font = 'arial'
    p.title.text_color = 'gray'

    #Y-Axis
    p.yaxis.axis_label = 'Revenue'
    p.yaxis.axis_label_text_font = 'arial'
    p.yaxis.axis_label_text_font_style = 'bold'
    p.yaxis[0].formatter = NumeralTickFormatter(format="$0,00.00")

    #X-Axis
    p.xaxis.axis_label = 'Date'
    p.xaxis.axis_label_text_font = 'arial'
    p.xaxis.axis_label_text_font_style = 'bold'
    p.xaxis.major_label_text_color = 'black'

    #Removes X-Grid Line
    p.xgrid.grid_line_color = None

    #Tools
    p.add_tools(PanTool())
    p.add_tools(BoxZoomTool())
    p.add_tools(WheelZoomTool())
    p.add_tools(ZoomInTool())
    p.add_tools(ZoomOutTool())
    p.add_tools(ResetTool())
    p.add_tools(SaveTool())
    p.toolbar.logo = None

    #Misc
    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None

    p.vbar_stack(stackers=partners, x='Day', width=36000000, color=colors, 
                 source=source,  legend=[value(x) for x in partners], 
                 name=partners)

    p.extra_y_ranges = {"Impression_Range": 
        Range1d(start=0, end=df2['Impressions'].max()+5000000)}
    
    p.add_layout(LinearAxis(y_range_name='Impression_Range', 
                            axis_label="Impressions", 
                            axis_label_text_font = 'arial', 
                            axis_label_text_font_style = 'bold', 
                            minor_tick_line_color = None, 
                            formatter = NumeralTickFormatter(format="000,000")), "right")
    
    p.line(x='Day', y='Impressions', source=source, line_width=2, 
           color='navy', y_range_name = 'Impression_Range', 
           legend='Impression')

    #Legend Formatting
    # p.legend.location = "top_left"
    p.legend.location = 'top_center'
    p.legend.orientation = "horizontal"
    p.legend.click_policy = 'hide'
    
    ############################################
    # Revenue by Day by Ad Unit Type
    ############################################

    df_unittype_pivot = df.pivot_table(index='Day', columns='UnitType', 
                                       values='Revenue', aggfunc='sum')

    df_unittype_pivot['Total_Revenue'] = revenue_list

    df_unittype_pivot.to_csv("revenue-by-day-by-adtype.csv")

    df3 = pd.read_csv("revenue-by-day-by-adtype.csv")

    df3['Total_Revenue'].max()

    df3['Day'] = pd.to_datetime(df3['Day'])

    source2 = ColumnDataSource(df3)
    ad_type = ["banner", "native", "video"]
    pastel_colors = ["#a8e6cf", "#ffd3b6", "#ffaaa5"]

    df3.head(1)

    hover2 = HoverTool(
        tooltips=
        [
          ('Video','@video{$0,0.00}'),
          ('Native','@native{$0,0.00}'),
          ('Banner','@banner{$0,0.00}'),
          ('Total Revenue', '@Total_Revenue{$0,0.00}'),
          ('Date','@Day{ %F }'),
        ],

        formatters={'Day':'datetime'}

    )

    p2 = figure(plot_width = 1000, plot_height=400, x_axis_type='datetime', 
                title="Ads By Day", toolbar_location='above', 
                tools=[hover2], y_range=(0,df3['Total_Revenue'].max()+500))

    p2.vbar_stack(stackers=ad_type, x='Day', width=36000000, color=pastel_colors,
                  source=source2, legend=[value(x) for x in ad_type], 
                  name=ad_type)

    #Title
    p2.title.text = 'IMVU Mobile Ad Revenue by Type, Date'
    p2.title.text_font = 'arial'
    p2.title.text_color = 'gray'
    #p.title.text_font_style = 'bold'

    #Y-Axis
    p2.yaxis.axis_label = 'Revenue'
    p2.yaxis.axis_label_text_font = 'arial'
    p2.yaxis.axis_label_text_font_style = 'bold'
    p2.yaxis[0].formatter = NumeralTickFormatter(format="$0,00.00")

    #X-Axis
    p2.xaxis.axis_label = 'Date'
    p2.xaxis.axis_label_text_font = 'arial'
    p2.xaxis.axis_label_text_font_style = 'bold'
    p2.xaxis.major_label_text_color = 'black'

    #Removes X-Grid Line
    p2.xgrid.grid_line_color = None

    #Tools
    p2.add_tools(PanTool())
    p2.add_tools(BoxZoomTool())
    p2.add_tools(WheelZoomTool())
    p2.add_tools(ZoomInTool())
    p2.add_tools(ZoomOutTool())
    p2.add_tools(ResetTool())
    p2.add_tools(SaveTool())
    p2.toolbar.logo = None

    #Misc
    p2.y_range.start = 0
    p2.x_range.range_padding = 0.1
    p2.axis.minor_tick_line_color = None
    p2.outline_line_color = None

    #Legend Formatting
    p2.legend.location = 'top_center'
    p2.legend.orientation = "horizontal"
    p2.legend.click_policy = 'hide'

    ############################################
    # Revenue by Day by App
    ############################################

    df_app_pivot = df.pivot_table(index='Day', columns='App', 
                                  values=['Revenue', 'Impressions'], 
                                  aggfunc='sum')

    df_app_pivot.to_csv("revenue-by-day-by-app.csv")

    df4 = pd.read_csv("revenue-by-day-by-app.csv", skiprows=2)

    df4 = df4.fillna(0)

    col_idx = 0
    bad_column_list = []

    for c in list(df4.columns):
        if df4.loc[0, c] == 0.0:
            bad_column_list.append(col_idx)
        col_idx += 1

    columns_to_delete = [list(df4.columns)[num] for num in bad_column_list]

    for c in columns_to_delete:
        del df4[c]

    df4.columns = ["Day", "IMVU_Android_Impressions", "IMVU_iOS_Impressions", 
                   "IMVU_Android_Revenue", "IMVU_iOS_Revenue"]

    df4['Day'] = pd.to_datetime(df4['Day'])

    # turn impressions to integer?

    df4["Total_Revenue"] = df4["IMVU_Android_Revenue"] + df4["IMVU_iOS_Revenue"]
    df4["Total_Impressions"] = df4["IMVU_Android_Impressions"] + df4["IMVU_iOS_Impressions"]

    os_colors = ["#ff5d5d", "#84b9ef"]
    ad_type = ['IMVU_Android_Revenue', 'IMVU_iOS_Revenue']

    source3 = ColumnDataSource(df4)

    hover3 = HoverTool(
        tooltips=
        [
          ('iOS Revenue','@IMVU_iOS_Revenue{$0,0.00}'),
          ('Android Revenue','@IMVU_Android_Revenue{$0,0.00}'),
          ('Total Revenue', '@Total_Revenue{$0,0.00}'),
          ('Date','@Day{ %F }'),
        ],

        formatters={'Day':'datetime'}

    )

    p3 = figure(plot_width = 1000, plot_height=400, x_axis_type='datetime', 
                title="Ads By Day", toolbar_location='above', 
                tools=[hover3], y_range=(0,df4['Total_Revenue'].max()+500))

    p3.vbar_stack(stackers=ad_type, x='Day', width=36000000, color=os_colors, 
                  source=source3, alpha=0.6, legend=[value(x) for x in ad_type], 
                  name=ad_type)

    #Title
    p3.title.text = 'IMVU Mobile Ad Revenue by App, Date'
    p3.title.text_font = 'arial'
    p3.title.text_color = 'gray'
    #p.title.text_font_style = 'bold'

    #Y-Axis
    p3.yaxis.axis_label = 'Revenue'
    p3.yaxis.axis_label_text_font = 'arial'
    p3.yaxis.axis_label_text_font_style = 'bold'
    p3.yaxis[0].formatter = NumeralTickFormatter(format="$0,00.00")

    #X-Axis
    p3.xaxis.axis_label = 'Date'
    p3.xaxis.axis_label_text_font = 'arial'
    p3.xaxis.axis_label_text_font_style = 'bold'
    p3.xaxis.major_label_text_color = 'black'

    #Removes X-Grid Line
    p3.xgrid.grid_line_color = None

    #Tools
    p3.add_tools(PanTool())
    p3.add_tools(BoxZoomTool())
    p3.add_tools(WheelZoomTool())
    p3.add_tools(ZoomInTool())
    p3.add_tools(ZoomOutTool())
    p3.add_tools(ResetTool())
    p3.add_tools(SaveTool())
    p3.toolbar.logo = None

    #Misc
    p3.y_range.start = 0
    p3.x_range.range_padding = 0.1
    p3.axis.minor_tick_line_color = None
    p3.outline_line_color = None

    #Legend Formatting
    # p3.legend.location = "top_left"
    p3.legend.location = 'top_center'
    p3.legend.orientation = "horizontal"
    p3.legend.click_policy = 'hide'    

    from bokeh.layouts import column
    
    show(column(p, p2, p3))

def revenue_performance_dashboard(start_date, end_date):
    if 'add_key_here' not in api_keys():
        (mopub_api_key, mopub_inventory_report_id, fyber_video_username, 
        fyber_video_password, fyber_display_publisher_id, 
        fyber_display_consumer_key, fyber_display_consumer_secret) = api_keys()
        
        now = datetime.datetime.now()
        now_string = now.strftime('%Y-%m-%d')
        
        if end_date != now_string:
            ## End date can't be "today" -- else it won't work--MoPub doesn't do same-day reporting.
            mopub_df = fetch_mopub_report(start_date, end_date, 
                                          mopub_inventory_report_id, 
                                          mopub_api_key)
            
            mopub_df = mopub_dataframe_cleaner(mopub_df)
            
            fyber_video_df = fetch_fyber_video_report(start_date, end_date, 
                                                      fyber_video_username, 
                                                      fyber_video_password)
            
            fyber_video_df = fyber_video_dataframe_cleaner(fyber_video_df)
            
            fyber_display_df = fetch_fiber_display_report(start_date, end_date,
                                                          fyber_display_publisher_id,
                                                          fyber_display_consumer_key, 
                                                          fyber_display_consumer_secret)
            
            fyber_display_df = fyber_display_dataframe_cleaner(fyber_display_df)
            print("Data is collected / cleaned!")
            df_concat = pd.concat([mopub_df, fyber_video_df, fyber_display_df], axis=0)
            df_concat.to_csv('revenue_performance_data.csv', index=False)
            bokeh_dashboard_creator(df_concat)
            print("Your data / dashboard is done!")
    
        else:
            print("End date can't be 'today', MoPub doesn't give same-day data via the API.")
            
    else:
        print("You need all valid API keys to use this program." \
              " So the program is probably not going to work for you. Sorry!")

if __name__ == '__main__':
    revenue_performance_dashboard(args.start_date, args.end_date)