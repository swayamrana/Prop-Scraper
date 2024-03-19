
import pandas as pd
from time import sleep
from selenium import webdriver
import hashlib
from scrapingbee import ScrapingBeeClient
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.library.parameters import SeasonAll
from nba_api.stats.static import players

# TO WRITE ALL PLAYERS & LINES
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)  
pd.set_option('display.max_colwidth', None) 

# SCRAPING CLIENT
client = ScrapingBeeClient(api_key="R5514J0B7ZHSSUI1GS02PHQRNSULVYHES69CEY58XM1TXCKNMMTA9KFLPUMJ8UP91GHZ2CFF0GHG6BH6")

def get_all():
    for i in range(100):
        r = client.get("https://api.prizepicks.com/projections?league_id=7&per_page=250&single_stat=true")
        if r.status_code != 200:
            sleep(5)
        else:
            break

    response = r.json()
    values1 = [
        "stat_type",
        "line_score",
    ]
    descrips = pd.DataFrame([i["attributes"] for i in response["data"]], columns=values1)
    values2 = [
        "id"
    ]
    rels = pd.DataFrame([i["relationships"]["new_player"]["data"] for i in response["data"]], columns=values2)
    lookups = pd.DataFrame(response["included"])

    props = []
    for (_, x), (_, y), in zip(descrips.iterrows(), rels.iterrows()):
        to_find = y["id"]
        for(_, z) in lookups.iterrows():
            if to_find  == z["id"]:
                add = {"Name" :  z["attributes"]["display_name"], "Team" : z["attributes"]["team"], "Position" : z["attributes"]["position"], "Prop" : x["stat_type"], "Current Line" : x["line_score"]}
                props.append(add)

    current_lines = pd.DataFrame(props)
    return current_lines

last = get_all()
last_hash = None
driver = webdriver.Chrome()

while(1):
    driver.get("https://api.prizepicks.com/projections?league_id=7&per_page=250&single_stat=true")
    ps = driver.page_source 
    hash_value = hashlib.sha256(ps.encode()).hexdigest()
    if hash_value != last_hash:
        new = get_all()
        if last_hash == None:
            last_hash = hash_value 
            # PRINT 5 BEST PROPS
            print("5 BEST PROPS:\n")
            stats = [[]]
            for (_, entry) in new.iterrows():
                i_d = next((x for x in players.get_players() if x is not None and x.get("full_name") == entry["Name"]), None)
                if i_d == None:
                    continue
                else:
                    i_d = i_d.get("id")
                gl = pd.concat(playergamelog.PlayerGameLog(player_id=i_d, season=SeasonAll.all).get_data_frames())
                gl["GAME_DATE"] = pd.to_datetime(gl["GAME_DATE"], format="%b %d, %Y")
                gl = gl.query("GAME_DATE.dt.year in [2023, 2024]")
                select = None

                if entry["Prop"] == "Points":
                    select = "PTS"
                elif entry["Prop"] == "Rebounds":
                    select = "REB"
                elif entry["Prop"] == "Assists":
                    select = "AST"
                elif entry["Prop"] == "Steals":
                    select = "STL"
                elif entry["Prop"] == "Blocks":
                    select = "BLK"
                elif entry["Prop"] == "Turnovers":
                    select = "TOV"
                elif entry["Prop"] == "3PT-Made":
                    select = "FG3M"
                elif entry["Prop"] != "Rebs+Asts" and entry["Prop"] != "Pts+Rebs" and entry["Prop"] != "Pts+Asts":
                    continue
            
                # SPECIAL CASES
                if entry["Prop"] == "Rebs+Asts":
                    cur = [gl["REB"].head(20).tolist()[i] + gl["AST"].head(20).tolist()[i] for i in range(20)]
                elif entry["Prop"] == "Pts+Rebs":
                    cur = [gl["PTS"].head(20).tolist()[i] + gl["REB"].head(20).tolist()[i] for i in range(20)]
                elif entry["Prop"] == "Pts+Asts":
                    cur = [gl["PTS"].head(20).tolist()[i] + gl["AST"].head(20).tolist()[i] for i in range(20)]
                else:
                    cur = gl[select].head(20).tolist()
                
                hits = 0
                line = entry["Current Line"]
                for num in cur:
                    if num >= line:
                        hits += 1

                hit_rate = float(hits / 20)
                db = {
                    'NAME': entry["Name"],
                    'PROP': entry["Prop"],
                    'LINE': entry["Current Line"],
                    'HIT RATE': hit_rate
                }
                stats.append(db)

            stats.pop(0)
            sort = sorted(stats, key=lambda x: x['HIT RATE'], reverse=True)
            for i in range(5):
                print(sort[i]["NAME"] + " " + sort[i]["PROP"] + "  " + "->" + " " + str(sort[i]["LINE"])  + "  " + "->" + " " + str(sort[i]["HIT RATE"]) + " " + "(LAST 20)")
                print('\n')
            sleep(600)
            continue
        else:
            visited = [False] * 1000
            for (_, a) in last.iterrows():
                for (idx, b) in new.iterrows():
                    if a["Name"] == b["Name"] and a["Prop"] == b["Prop"] and a["Current Line"] != b["Current Line"] and visited[idx] == False:
                        # WRITE NEW CHANGE
                        prompt = "CHANGE: " + a["Name"] + " " + a["Prop"] + " " + ":" + " " +  str(a["Current Line"]) + " " + "->" + " " + str(b["Current Line"])
                        print(prompt)
                        print("\n")
                        visited[idx] = True

        # UPDATE DATAFRAME
        last = new
        # UPDATE HASH
        last_hash = hash_value
        # PRINT 5 BEST PROPS
        print("5 BEST PROPS:\n")
        stats = [[]]
        for (_, entry) in new.iterrows():
            i_d = next((x for x in players.get_players() if x is not None and x.get("full_name") == entry["Name"]), None)
            if i_d == None:
                continue
            else:
                i_d = i_d.get("id")
            gl = pd.concat(playergamelog.PlayerGameLog(player_id=i_d, season=SeasonAll.all).get_data_frames())
            gl["GAME_DATE"] = pd.to_datetime(gl["GAME_DATE"], format="%b %d, %Y")
            gl = gl.query("GAME_DATE.dt.year in [2023, 2024]")
            select = None

            if entry["Prop"] == "Points":
                select = "PTS"
            elif entry["Prop"] == "Rebounds":
                select = "REB"
            elif entry["Prop"] == "Assists":
                select = "AST"
            elif entry["Prop"] == "Steals":
                select = "STL"
            elif entry["Prop"] == "Blocked Shots":
                select = "BLK"
            elif entry["Prop"] == "Turnovers":
                select = "TOV"
            elif entry["Prop"] == "3PT-Made":
                select = "FG3M"
            elif entry["Prop"] != "Rebs+Asts" and entry["Prop"] != "Pts+Rebs" and entry["Prop"] != "Pts+Asts":
                continue
        
            # SPECIAL CASES
            if entry["Prop"] == "Rebs+Asts":
                cur = [gl["REB"].head(20).tolist()[i] + gl["AST"].head(20).tolist()[i] for i in range(20)]
            elif entry["Prop"] == "Pts+Rebs":
                cur = [gl["PTS"].head(20).tolist()[i] + gl["REB"].head(20).tolist()[i] for i in range(20)]
            elif entry["Prop"] == "Pts+Asts":
                cur = [gl["PTS"].head(20).tolist()[i] + gl["AST"].head(20).tolist()[i] for i in range(20)]
            elif entry["Prop"] == "Pts+Rebs+Asts":
                cur = [gl["PTS"].head(20).tolist()[i] + gl["AST"].head(20).tolist()[i] + gl["REB"].head(20).tolist()[i] for i in range(20)]
            else:
                cur = gl[select].head(20).tolist()
            
            hits = 0
            line = entry["Current Line"]
            for num in cur:
                if num >= line:
                    hits += 1

            hit_rate = float(hits / 20)
            db = {
                'NAME': entry["Name"],
                'PROP': entry["Prop"],
                'LINE': entry["Current Line"],
                'HIT RATE': hit_rate
            }
            stats.append(db)

        stats.pop(0)
        sort = sorted(stats, key=lambda x: x['HIT RATE'], reverse=True)
        for i in range(5):
            print(sort[i]["NAME"] + " " + sort[i]["PROP"] + "  " + "->" + " " + str(sort[i]["LINE"])  + "  " + "->" + " " + str(sort[i]["HIT RATE"]) + " " + "(LAST 20)")
            print('\n')
       
    # UPDATE EVERY 10 MINUTES TO AVOID OVERKILL & PROCESSING
    sleep(600)

