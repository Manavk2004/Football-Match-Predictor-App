from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import time
import pandas as pd
from io import StringIO

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")


driver = webdriver.Chrome(options=chrome_options)


try:
    years = list(range(2025, 2022, -1))
    print(years)
    all_matches = []
    for year in years:
        standings_url = f"https://fbref.com/en/comps/9/{year-1}-{year}/{year-1}-{year}-Premier-League-Stats"
        print(year)
        driver.get(standings_url)
        time.sleep(3)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        standings_table = soup.select('table.stats_table')[0]

        links = [l.get('href') for l in standings_table.find_all('a')]
        links = [l for l in links if '/squads/' in l]
        print("The links", links)
        team_urls = [f"https://fbref.com{l}" for l in links]

        previous_season = soup.select("a.prev")[0].get("href")
        

        for team_url in team_urls:
            # print("In for loop")
            team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", "")
            # print(team_name)
            driver.get(team_url)
            time.sleep(3)
            html = driver.page_source
            html_io = StringIO(html)    
            # print("html acquired")
            matches = pd.read_html(html_io, match="Scores & Fixtures ")[0]
            # print(matches)
            soup = BeautifulSoup(html, 'html.parser')
            # print("Soup done")
            links = [l.get("href") for l in soup.find_all('a')]
            # print("initial links")
            links = [l for l in links if l and 'all_comps/shooting/' in l]
            # print("links 2")
            driver.get(f"https://fbref.com{links[0]}")
            # print("Driver got")
            time.sleep(3)
            html = driver.page_source
            html_io = StringIO(html)
            # print("html_io done")
            shooting = pd.read_html(html_io, match="Shooting")[0]
            # print("read shooting")
            # print("The shooting", shooting)
            shooting.columns = shooting.columns.droplevel()
            # print("Dropped columns")

            try:
                # print("In try block")
                # print(type(matches))
                team_data = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
                # print("Success in team_date", team_data)
            except ValueError:
                continue

            team_date = team_data[team_data["Comp"] == "Premier League"]
            team_data["Season"] = year
            team_data["Team"] = team_name
            all_matches.append(team_data)
            time.sleep(1)

    
    match_df = pd.concat(all_matches)
    print(match_df)
    match_df.to_csv("matches.csv")



except Exception as e:
    print(f"Error occurred: {e}")
finally:
    driver.quit()

    
