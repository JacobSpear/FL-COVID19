from bs4 import BeautifulSoup as bs
from splinter import Browser
import os
import pandas as pd
import csv



def fetch_data():
    url = 'http://www.floridahealth.gov/diseases-and-conditions/COVID-19/index.html'

    case_table = pd.read_html(url,header=1)[0].rename(columns={'Unnamed: 0':'ID'}).set_index('ID')
    
    executable_path = {"executable_path":"chromedriver.exe"}
    browser = Browser('chrome',**executable_path,headless=False)

    browser.visit(url)

    html = browser.html

    soup = bs(html,'lxml')
    cov_info = soup.find('block')
    browser.quit()
    update_date = str(cov_info.find('sup')).split('ET ')[1].split("<")[0]
    update_time = str(cov_info.find('sup')).split('as of ')[1].split(' ET')[0]
    
    results = {'Date':update_date,'Time':update_time}
    categories = ['Positive Cases of COVID-19',
                  'Deaths',
                  'Number of Negative Test Results',
                  'Number of Pending Test Results',
                  'Number of People Under Public Health Monitoring']


    for category in categories:
        info = str(cov_info).split(category,maxsplit=1)[1].split('<strong>',maxsplit=1)[0]
        data = info.split("<div style=\"text-align: center;\">")
        results_list = []
        for i in range(1,len(data)):
            results_list.append(data[i].split("<")[0])
        results[category]=results_list

    output = {}
    
    output['Date'] = results['Date'].split("/")[2]+'-'+results['Date'].split("/")[0]+'-'+results['Date'].split("/")[1]
    output['Time'] = (results['Time'].split(' ')[0]
                      + " " 
                      + results['Time'].split(' ')[1].split('.')[0].upper()
                      + results['Time'].split(' ')[1].split('.')[1].upper())
    
    #Unpacks positive cases, totals all categories
    positive_cases = results['Positive Cases of COVID-19']
    total_cases = 0
    for string in positive_cases:
        info = string.split(' ',maxsplit=2)
        val = int(info[0])
        output[f'{info[2]} - Positive'] = val
        total_cases += val
    output['Total - Positive'] = total_cases
    
    #Unpacks monitored cases
    monitored = results['Number of People Under Public Health Monitoring']
    currently_monitored = monitored[0]
    total_monitored = monitored[1]
    output['People Monitored - Current'] = int(currently_monitored.split(' ',maxsplit=2)[0])
    output['People Monitored - Total'] = int(total_monitored.split(' ',maxsplit=2)[0])
    
    #Unpacks deaths, totals all categories
    total_deaths = 0
    for string in results['Deaths']:
        val = int(string.split(' ')[0])
        label = string.split(' ',maxsplit=2)[2]+" - Deaths"
        total_deaths += val
        output[label] = val
    output['Total - Deaths'] = total_deaths
    
    #Unpacks Test Results
    output['Negative Tests'] = int(results['Number of Negative Test Results'][0])
    output['Pending Tests'] = int(results['Number of Pending Test Results'][0])
    
    return [output,case_table]
    

# # Writes to csv file for first time
# file_path = os.path.join('..','docs','static','data','daily_updates.csv')
# with open(file_path, 'w') as csvfile:
#     writer = csv.writer(csvfile, delimiter=',')
#     writer.writerow(list(new_row.keys()))
#     writer.writerow(list(new_row.values()))

def update_data():
    data_dir = os.path.join('..','docs','static','data')
    file_path = os.path.join(data_dir,'daily_updates.csv')
    old_table_dir = os.path.join(data_dir,'old_tables')
    table_path = os.path.join(data_dir,'current_patient_table.csv')
    
    data = fetch_data()
    new_row = data[0]
    datetime = new_row['Date']+ " " + new_row['Time'].split(":")[0] +"-"+new_row['Time'].split(":")[1]
    new_table = data[1]
    
    
    def up_to_date():
        df = pd.read_csv(file_path)
        result = df.iloc[len(df)-1,slice(0,2)]
        return (result['Date']==new_row['Date'] and result['Time']==new_row['Time'])
    
    if (not up_to_date()):
        #Writes new_row into file
        with open(file_path, 'a') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerow(list(new_row.values()))

        #Writes table into old_tables for storage
        old_table_path = os.path.join(old_table_dir,f'{datetime}_patient_table')
        new_table.to_csv(old_table_path)

        #Overwrites current table
        new_table.to_csv(table_path)
        
        return 'updated successfully'
    
    return 'already up to date' 

print(update_data())