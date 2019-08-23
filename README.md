# Revenue Performance Dashboard 

![alt text](https://raw.githubusercontent.com/wrny/revenue_dashboard_example/master/example-image.png
 "Revenue Dashboard Example")

A Python-based revenue / performance dashboard made using Pandas, Requests, and Bokeh. 

## About

If you work in online advertising, you're likely no stranger to data visualization tools like Tableau, Looker or Qlik. These services make slick, interactive chats that make sense of increasingly big "Big Data." Those tools of course need data to visualize, and the data usually comes from services like TapClicks, Ad-Juster and STAQ or from the various ad company APIs.

But as great as those services are, they're also really expensive! We're talking thousands, if not tens of thousands of dollars per month when added together, plus even more when you factor in the amount of time / effort in on-boarding and effort to get the products to work the way you want them. And if you don't have big budgets, then you're stuck downloading charts into Excel Spreadsheets, pasting into more Spreadsheets, which might even be read by another spreadsheet! Heck, you might be doing that anyway. I've done it a lot in my career, and it's a tough way to live.

A middle-way here is to use Python to extract data from reporting APIs from the necessary platforms, edit (or transform) the data so you're only displaying that you want and then use an open-source library such as Matplotlib, Plotly, Bokeh or Dash to make the data look great. A graph like is of course not as robust as something like STAQ / Tableau, but cheaper, faster, generally more easy to customize, letting you focus more on making it look perfect.

Attached is a project I did for a client. It:

1.  Accepts start date and end date arguments via the commandline (via argparser) to give a date range and pull data from that range.
2. Collects data via API from various sources, such as MoPub, InMobi, Google AdMob (the code here uses MoPub, Fyber and Fyber Video). This was mostly done via the Requests model (and sub modules such as requests_oauth and requests_auth) and Pandas. This was tricky, because each service has different authentication methods to get the data, services will have columns that others don't have, the data is in in different formats (CSV vs JSON), and column names often didn't match from platform to platform. 
3. Cleans the data, deleting superfluous columns, and edited the remaining ones so all of the various placement names matched (so an Android 300x250 placement named one thing in InMobi was named the same way as an Android 300x250 in MoPub). This was exclusively done using Pandas.
4. Concatenates all of the data together. Again, Pandas. On another version of this program, I ran this every day via cron tab and pushed the data to a SQL db.
5. Output necessary data into CSV files for deeper Excel dives, if necessary. Pandas, again.
6. Displayed the reports in Bokeh, a Python data visualization library that outputs charts in slick Interactive JS environments. From there, viewers could get a good sense of revenue trends, zoom in, or highlight certain elements. Bokeh is verbose, to put it mildly, but the output looks great and writes to its own HTML page, which comes in handy when deploying it to a server.

From here, this program is done, but the natural next step is to display the data on an internal website made with Django or Flask, so everyone on a team (managers, colleagues, accounting) can see revenue and make projections or pronouncements.

The project saved dozens (maybe hundreds) of hours of Excel work and instead, time could be spent on optimizing price floors, coming up with new ad units and selling!

While this is a sell-side example, the general principle be applied the buy-side, where you can pull spending numbers across various DSPs, Networks or Buying platforms and see how much ad spend you're doing per day, as well as the performance of said ads.

Below is a link where you can download the HTML file, and watch a video of the program in action:

[dashboard.html](https://drive.google.com/open?id=1-qRoa9V7IeSmBuLqUWjk1mFq8IR-EHsJ)

[Video of Program in Action](https://drive.google.com/file/d/14GfVJxMm9pKLDFwhB8S93UcQMrcUkK-W/view)

Note: The program requires API keys and report IDs from the various SSPs and that’s sensitive information. You won’t see any real API keys in this repo, as they’re saved to my local machine. The code / video are here just to show what’s possible. If you download the repo and try to run it, you’ll likely get an error right off the bat telling you that you don’t have the right API keys. But the attached dashboard.html file is a good representation of what the data might look like and the video shows what the program is like in action.
