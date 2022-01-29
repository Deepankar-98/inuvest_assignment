from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.offline as offline

# Declaring global variables which holds the CSV file once it is uploaded
df_processed = pd.DataFrame([])

# Create views here.
def index(request):
    global df_processed
    data = None
    
    try:
        if request.method == 'POST' and request.FILES['myfile']:
            # Read the uploaded CSV file
            global df_processed
            data = request.FILES['myfile']
            df = pd.read_csv(data)
            df_processed = manipulate_csv(df)
            download_url = reverse('download-page')
            return HttpResponseRedirect(download_url)
        
        # Render's the index page
        return render(request, 'index.html', context={'processed_data': "No data!!!"})

    except Exception as e:
        return render(request, 'index.html', context={'error': e})


def download(request):
    global df_processed
    # Functionality on clicking download button
    if request.method == 'POST':
        if df_processed.empty: 
            return render(request, 'download.html', context={'is_empty': True})

        else:
            # Code for downloading dataframe
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="output.csv"'
            df_processed.to_csv(response, index=False)
            df_processed = pd.DataFrame([])
            fig, graph_div = None, None
            return response

    if not df_processed.empty: 
        # Plotly Graph construction
        cols = df_processed.columns
        x = cols[0]
        y = [cols[11], cols[12], cols[-1]]

        fig = px.line(df_processed, x=x, y=y)
        graph_div = offline.plot(fig, auto_open = False, output_type="div")

        # Render the download page
        return render(request, 'download.html', context={'is_empty': False, 'graph_div': graph_div})
    else:
        return render(request, 'download.html', context={'is_empty': True})


# Data Transformation functions:
def transform (data_row):
    global c, d, e, i, j, k, q, sumf14, sumg14, sumh14, sum27       
    curr_index = data_row.name                      
    
    if curr_index == 0:
        f, g, h, i, j, k, l, m, n, o, p, q = (np.nan,)*12
        a, b, c, d, e = data_row
        sumf14, sumg14, sumh14, sum27 = 0, 0, 0, 0
        
    else:
        c1, d1, e1 = c, d, e
        a, b, c, d, e = data_row
        
        # Logic for TR column
        f = max((c-d), abs(c-e1),abs(d-e1)) 
        
        # Logic for +DM 1
        g = max(c-c1, 0) if (c-c1)>(d1-d) else 0
        
        # Logic for -DM 1
        h = max(d1-d, 0) if (d1-d)>(c-c1) else 0
        
        
    # Logic for TR14/ +DM14/ -DM14/ +DI14/ -DI14/ DI 14 Diff/ DI 14 Sum/ DX
    if curr_index < 14 and curr_index > 0:
        i, j, k, l, m, n, o, p, q = (np.nan,)*9
        sumf14 += f
        sumg14 += g
        sumh14 += h

    elif curr_index == 14:
        i = sumf14 + f
        j = sumg14 + g
        k = sumh14 + h
        l = round((100*j)/i, 8)
        m = round((100*k)/i, 8)
        n = round(abs(l-m), 8)
        o = round(l+m, 8)
        p = round((100*n)/o, 8)
        
    else:
        i1, j1, k1 = i, j, k
        i = round(i1 - (i1/14.0) + f, 8)
        j = round(j1 - (j1/14.0) + g, 8)
        k = round(k1 - (k1/14.0) + h, 8)
        l = round((100*j)/i, 8)
        m = round((100*k)/i, 8)
        n = round(abs(l-m), 8)
        o = round(l+m, 8)
        p = round((100*n)/o, 8)
       
    
    # Logic for ADX
    if curr_index < 27 and curr_index >= 14:
        q = np.nan
        sum27 += p
        
    elif curr_index == 27:
        q = round((sum27+p)/14, 9)
        
    else:
        q1 = q 
        q = round((q1*13+p)/14, 9)

    return [f, g, h, i, j, k, l, m, n, o, p, q]


def manipulate_csv (df):
    
    # Converting object to datetime dtype
    df.rename(columns = {df.columns[0]: 'Date'}, inplace = True)
    df['Date'] = pd.to_datetime(df['Date'])

    # Note adding space before cols containing +/ - sysmbol so that column names are displayed properly in excel
    cols = ['TR', ' +DM 1', ' -DM 1', 'TR14', ' +DM14', ' -DM14', ' +DI14', ' -DI14', 'DI 14 Diff', 'DI 14 Sum', 'DX', 'ADX']

    # Since iterrows & itertuples are very slow, I am opting to use apply instead
    res = df.apply(transform, axis=1)
    new_df = pd.DataFrame(res.tolist(), columns=cols)
    df = pd.concat([df, new_df], axis=1)

    # Removing header of 1st column
    df.rename(columns = {'Date': ' '}, inplace = True)

    # Decreasing the precision according to the excel sheet output
    round_2_cols = list(df.columns[8: -1])
    df[round_2_cols] = df[round_2_cols].round(2)
    df['ADX'] = df['ADX'].round(8)

    return df
