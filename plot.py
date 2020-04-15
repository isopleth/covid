#!/usr/bin/env python3
#
# Plot course of Covid-19 in the UK
#
# Copyright 2020  Jason Leake
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
 
import numpy as np
import pandas as pd
import subprocess
import io
import matplotlib.pyplot as plt
import urllib.request

inputFile = 'Historic COVID-19 Dashboard Data.xlsx'

def parseDate(date):
    """
    Converts a string from the format MM-DD-YY in datetime format.
    Example: parseDate("02-12-20") returns datetime(2020, 12, 2)
    """
    return pd.to_datetime(date, format='%m-%d-%y')

def getAverage(series, count):
    # For each element in the frame
    ## Look back for the <count> elements
    retvals = []
    vals = []
    for item in series.iteritems():
        vals.append(item[1])

    for index in range(len(vals)):
        contributions = []
        for index1 in range(index - 5, index + 1):
            if index1 >= 0:
                contributions.append(vals[index1])
        sum = 0
        for val1 in contributions:
            sum += val1
        mean = sum / count
        retvals.append(mean)
    return retvals


def convertToTextArray(string):
    # convert to text array to allow non-data lines to be removed
    out = []
    buffer = []
    text = string.decode(encoding='utf-8', errors='ignore')
    for char in text:
        if char == '\n':
            out.append(''.join(buffer))
            out.append('\n')
            buffer = []
        else:
            buffer.append(char)
    else:
        if buffer:
            out.append(''.join(buffer))
    return out

def plotCases(startDate):
    """Plot cases recorded in the Government's rather dodgy statistics.
        Only seems to be hospital cases, so not very reliable

    """
    # Remove the garbage from Public Health England CSV file
    # This consists of lines of text, blank lines etc    
    result = subprocess.run(['xlsx2csv', inputFile, '-s 2'],
                            stdout=subprocess.PIPE)

    out = convertToTextArray(result.stdout)

    # Remove non-data lines
    dataLines = ''
    started = False
    for line in out:
        if line.startswith('Date,Cases,Cumulative Cases'):
            started = True
        if started:
            dataLines += line

    df = pd.read_csv(io.StringIO(dataLines),
                     parse_dates=['Date'], 
                     date_parser=parseDate)
    df.fillna(value=0,inplace=True)
    # Remove empty columns
    df.drop(df.columns[[3,4]], axis=1, inplace=True)

    startDateArray = []
    for count in range(len(df.index)):
        startDateArray.append(startDate)
    startDateSeries = pd.Series(startDateArray)
    df['Day'] = (df['Date'] - startDateSeries) / np.timedelta64(1, 'D')

    df['AveCases'] = getAverage(df['Cases'], 5)

    ax = df.plot(kind='line', x='Day', y='AveCases', color='red')
    ax.set_title('Rolling average cases over five days')
    ax.legend(['5 day mean cases'])
    ax.figure.savefig('avecases.png')
    ax1 = df.plot(kind='line', x='Day', y='Cases', color='red')
    ax1.set_title('Reported cases')
    ax1.legend(['Cases'])
    ax1.figure.savefig('cases.png')
    plt.show()


        
def plotDeaths():
    """Plot deaths recorded in the Government's rather dodgy statistics.
    Only seems to be hospital deaths, and dates from when reported, so
    not very reliable

    """
    # Remove the garbage from Public Health England CSV file
    # This consists of lines of text, blank lines etc    
    result = subprocess.run(['xlsx2csv', inputFile, '-s 3'],
                            stdout=subprocess.PIPE)

    out = convertToTextArray(result.stdout)

    # Remove non-data lines
    dataLines = ''
    started = False
    for line in out:
        if line.startswith('Date,Deaths,UK'):
            started = True
        if started:
            dataLines += line

    df = pd.read_csv(io.StringIO(dataLines),
                     parse_dates=['Date'], 
                     date_parser=parseDate)
    df.fillna(value=0,inplace=True)
    # Remove empty columns
    df.drop(df.columns[[7,8]], axis=1, inplace=True)

    average = getAverage(df['Deaths'], 5)

    days = []
    day = 0
    for index, row in df.iterrows():
        if row['Deaths'] != 0:
            startDate = row['Date']
            break
        day =- 1

    for index, row in df.iterrows():
        days.append(day)
        day += 1

    df['AveDeaths'] = average
    df['Day'] = days

    ax = df.plot(kind='line', x='Day', y='AveDeaths', color='red')
    ax.set_title('Rolling average deaths over five days')
    ax.legend(['Reported hospital deaths'])
    ax.figure.savefig('avedeaths.png')
    
    ax1 = df.plot(kind='line', x='Day', y='Deaths', color='red')
    ax1.set_title('Reported hospital deaths')
    ax1.legend(['Deaths'])
    ax1.figure.savefig('deaths.png')
    plt.show()
    return startDate


url = 'https://fingertips.phe.org.uk/documents/Historic%20COVID-19%20Dashboard%20Data.xlsx'
response = urllib.request.urlopen(url)
data = response.read()

with open(inputFile, 'wb') as outfile:
    outfile.write(data)

# Start date is Day 0 - the date of the first reported death
startDate = plotDeaths()
plotCases(startDate)


