import numpy as np
import os.path
from datetime import date, timedelta
import json
import pandas as pd
import time
#checks for whether or not the game is a good match to analyze
#it checks to see if the game has 10 players (no afks)
#it checks if the game is a rank game
def checkGame(matchNum):
    
    teamRed, teamBlue = False,False #blue = teamid 100 and red is 200
    #open match json file
    f = open("./data/real_data/match_%d.json"%matchNum,"r")
    data = json.load(f)
    isTimeline = False
    
    if data['queueType'] != 'TEAM_BUILDER_DRAFT_RANKED_5x5':
        game = False
    else:
        partic_df = pd.DataFrame(data['participants'])
        
        #check if game has 10 players
        if partic_df['participantId'].count() == 10:
            game = True
        else:
            game = False

        for item in data:
            if item == 'timeline':
                game = True
                isTimeline = True
                break
            else:
                game = False
                
        #due to new remake policy games that end before 5min are due to this
        game_length = data['matchDuration']/60.0 
        if game_length > 5.0 and isTimeline:
            game = True
        else:
            game = False
    return game
    
def calc_total_gold(dft,team,gametime):
    goldTotal = 0
    for item in team:
        ID = str(item['ID'])
        goldTotal += dft['participantFrames'][ID]['totalGold']
    return goldTotal  

def calc_total_kills(dft,gametime):
    kill_data = {}
    kill_data['kills'] = 0
    kill_data['killerId'] = []
    try:
        for event in dft['events']:
            if event['eventType'] == 'CHAMPION_KILL':
                #print event
                kill_data['kills'] += 1  
                kill_data['killerId'].append(event['killerId'])
    except:
        pass
    return kill_data

#b_type = TOWER_BUILDING or INHIBITOR_BUILDING
def calc_building_kills(dft,gametime,b_type):
    obj_data = {}
    obj_data['kills'] = 0
    obj_data['killerId'] = []
    obj_data['teamId'] = []
    try:
        for event in dft['events']:
            if event['eventType'] == 'BUILDING_KILL':
                if event['buildingType'] == b_type:
                    obj_data['kills'] += 1
                    obj_data['killerId'].append(event['killerId'])
                    obj_data['teamId'].append(event['teamId'])
    except:
        pass
    return obj_data

#monster = DRAGON, BARON_NASHOR, or RIFTHERALD
def calc_elite_monster_kills(dft,gametime,monster):
    monster_data = {}
    monster_data['kills'] = 0
    monster_data['killerId'] = []
    try:
        for event in dft['events']:
            if event['eventType'] == 'ELITE_MONSTER_KILL':
                if event['monsterType'] == monster:
                    monster_data['kills'] += 1
                    monster_data['killerId'].append(event['killerId'])
    except:
        pass
    return monster_data

def split_kills(team,killerIds):
    kills = 0
    for item in team:
        ID = item['ID']
        kills += killerIds.count(ID)
    return kills

def split_buildings(team, buildings):
    ID = int(team['teamId'])
    return buildings.count(ID)

def main(matchNum):
    print "Working on match %d" % matchNum
    f = open("./data/real_data/match_%d.json"%matchNum,"r")
    data = json.load(f)
    gameDuration = data['timeline']['frames'][-1]['timestamp']/1000/60 
    df1 = pd.DataFrame(data['participants'])
    df2 = pd.DataFrame(data['teams'])
    
    #determine basic stats of winning team
    victory_team = None
    defeat_team = None
    for i in range(2):
        df = df2.iloc[i]
        if df['winner']:
            victory_team = df2.iloc[[i]]
        else:
            defeat_team = df2.iloc[[i]]
            
    #separate winners and losers
    winners, losers = [],[]
    for i in range(10):
        df = df1.iloc[i]
        item = df['stats']
        playerId = df['participantId']
        rank = df['highestAchievedSeasonTier'] 
        if item['winner']:
            item['ID'] = playerId
            item['rank'] = rank
            item['teamId'] = int(victory_team['teamId'])
            winners.append(item)
        else:
            item['ID'] = playerId
            item['rank'] = rank
            item['teamId'] = int(defeat_team['teamId'])
            losers.append(item)
 
    #go through each match's timestamps/minutes   
    timeseries =[]
    df3 = pd.DataFrame(data['timeline']['frames'])
    length = df3.shape[0]
    firstBlood,firstTower, firstInhib, firstBaron,firstDragon,firstRift = False, False, False, False, False, False
    winFirstBlood,loseFirstBlood = False,False
    winFirstTower,loseFirstTower = False, False
    winFirstInhib,loseFirstInhib = False, False
    winFirstDragon,loseFirstDragon = False, False
    winFirstBaron,loseFirstBaron = False, False
    winFirstRift,loseFirstRift = False, False     
    winChampKills,loseChampKills,winTowerKills,loseTowerKills,winInhibKills, loseInhibKills = 0,0,0,0,0,0
    winDragonKills,loseDragonKills,winBaronKills,loseBaronKills = 0,0,0,0
    victory = True
    defeat = False        
    for i in range(1,length):
        df = df3.iloc[i]
        gametime = df['timestamp']/1000/60
        #for each timestamp find: kills, objectives, elitemonsters, gold
        champion = calc_total_kills(df,gametime)
        tower = calc_building_kills(df,gametime,'TOWER_BUILDING')
        inhibitor = calc_building_kills(df,gametime,'INHIBITOR_BUILDING')
        dragon = calc_elite_monster_kills(df,gametime,'DRAGON')
        baron = calc_elite_monster_kills(df,gametime,'BARON_NASHOR')
        riftherald = calc_elite_monster_kills(df,gametime,'RIFTHERALD')
        
        #find total gold
        winGoldTotal = calc_total_gold(df,winners,gametime)
        loseGoldTotal = calc_total_gold(df,losers,gametime)
        goldDiff = winGoldTotal-loseGoldTotal
        
        #win and lose kills
        winChampKills += split_kills(winners,champion['killerId'])
        loseChampKills += split_kills(losers,champion['killerId'])
        killDiff = winChampKills - loseChampKills
        
        #win and lose towers/inhibs, careful the teamid that loses a tower is what is defined
        winTowerKills += split_buildings(defeat_team, tower['teamId'])
        loseTowerKills += split_buildings(victory_team,tower['teamId'])
        towerDiff = winTowerKills - loseTowerKills
        
        winInhibKills += split_buildings(defeat_team,inhibitor['teamId'])
        loseInhibKills += split_buildings(victory_team,inhibitor['teamId'])
        inhibitorDiff = winInhibKills - loseInhibKills
        
        #win and lose elite monsters
        winDragonKills += split_kills(winners,dragon['killerId'])
        loseDragonKills += split_kills(losers,dragon['killerId'])
        dragonDiff = winDragonKills - loseDragonKills
        
        winBaronKills += split_kills(winners,baron['killerId'])
        loseBaronKills += split_kills(losers,baron['killerId'])
        baronDiff = winBaronKills - loseBaronKills
        
        winRiftKills = split_kills(winners,riftherald['killerId'])
        loseRiftKills = split_kills(losers,riftherald['killerId'])
        
        
        #find first bloods,towers,inhibs,dragons,barons,riftheralds
        if not firstBlood and champion['kills'] != 0:
            firstBlood = True
            firstBId = champion['killerId'][0]
         
            for item in winners:
                if firstBId == item['ID']:
                    winFirstBlood = True
                    loseFirstBlood = False
                    break
                else:
                    winFirstBlood = False
                    loseFirstBlood = True
         
        if not firstTower and tower['kills'] != 0:
            firstTower = True
            firstId = tower['teamId'][0]
            #print firstId, int(defeat_team['teamId']) 
            if int(defeat_team['teamId']) == firstId:
                winFirstTower = True
                loseFirstTower = False
            else:
                winFirstTower = False
                loseFirstTower = True
         
        
        if not firstInhib and inhibitor['kills'] != 0:
            firstInhib = True
            firstId = inhibitor['teamId'][0]
             
            if int(defeat_team['teamId']) == firstId:
                winFirstInhib = True
                loseFirstInhib = False
            else:
               winFirstInhib = False
               loseFirstInhib = True
         
        
        if not firstDragon and dragon['kills'] != 0:
            firstDragon = True
            firstId = dragon['killerId'][0]
            for item in winners:
                if firstId == item['ID']:
                    winFirstDragon = True
                    loseFirstDragon = False
                    break
                else:
                    winFirstDragon = False
                    loseFirstDragon = True
         
        
        if not firstBaron and baron['kills'] != 0:
            firstBaron = True
            firstId = baron['killerId'][0]
            for item in winners:
                if firstId == item['ID']:
                    winFirstBaron = True
                    loseFirstBaron = False
                    break
                else:
                    winFirstBaron = False
                    loseFirstBaron = True
        
        
        if not firstRift and riftherald['kills'] != 0:
            firstRift = True
            firstId = riftherald['killerId'][0]
            for item in winners:
                if firstId == item['ID']:
                    winFirstRift = True
                    loseFirstRift = False
                    break
                else:
                    winFirstRift = False
                    loseFirstRift = True
        
        timeseries.append((matchNum,victory,gametime,winGoldTotal,goldDiff,winChampKills,killDiff,winTowerKills, towerDiff, winInhibKills, inhibitorDiff,winDragonKills,dragonDiff,winBaronKills,baronDiff,winRiftKills,winFirstBlood,winFirstTower,winFirstInhib,winFirstDragon,winFirstBaron,winFirstRift))
        timeseries.append((matchNum,defeat,gametime,loseGoldTotal,-goldDiff,loseChampKills,-killDiff,loseTowerKills,-towerDiff,loseInhibKills,-inhibitorDiff,loseDragonKills,-dragonDiff,  loseBaronKills,-baronDiff,loseRiftKills,loseFirstBlood,loseFirstTower,loseFirstInhib,loseFirstDragon,loseFirstBaron,loseFirstRift))
        
        #For Spectator/Esports watching, specific features one can infer from watching a match
        #timeseries.append((matchNum,victory,gametime,winGoldTotal,goldDiff,winChampKills,killDiff,winTowerKills, towerDiff, winInhibKills, inhibitorDiff,winDragonKills,dragonDiff,winBaronKills,baronDiff))#,winFirstBlood,winFirstTower))
        #timeseries.append((matchNum,defeat,gametime,loseGoldTotal,-goldDiff,loseChampKills,-killDiff,loseTowerKills,-towerDiff,loseInhibKills,-inhibitorDiff,loseDragonKills,-dragonDiff,  loseBaronKills,-baronDiff))#,loseFirstBlood,loseFirstTower))
        
    
    #make dataframe
    #match_df = pd.DataFrame(timeseries,columns=['matchId','winner','time','goldTotal','goldDiff','champKills','killDiff','towerKills','towerDiff',                                                                          'inhibKills','inhibDiff','dragonKills','dragonDiff','baronKills','baronDiff'])#,'firstBlood','firstTower'])
    match_df = pd.DataFrame(timeseries,columns=['matchId','winner','time','goldTotal','goldDiff','champKills','killDiff','towerKills','towerDiff',                                                                          'inhibKills','inhibDiff','dragonKills','dragonDiff','baronKills','baronDiff','riftKills','firstBlood','firstTower','firstInhib','firstDragon','firstBaron','firstRift'])
                     
    #write to file
    if matchNum == 1:
        with open("./data/full_data/fulltimedata.csv",'wb') as f:
            match_df.to_csv(f,header=True)
    else:
        with open("./data/full_data/fulltimedata.csv",'a') as f:
            match_df.to_csv(f,header=False)
                   
if __name__ == "__main__":
    N_matches = int(raw_input("How many matches to convert?"))
    for n in range(N_matches+1):
        filepath = "./data/real_data/match_%d.json" % n
        if os.path.isfile(filepath):
            if checkGame(n):
                main(n)
            else:
                continue