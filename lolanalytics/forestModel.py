import numpy as np
import pandas as pd
import time
import dill
from sklearn.ensemble import RandomForestClassifier
from sklearn import cross_validation, grid_search

df = pd.read_csv("./data/full_data/fulltimedata.csv",index_col=0)
df = df.astype(int)

feature =['goldTotal','goldDiff','champKills','killDiff','towerKills','towerDiff','inhibKills','inhibDiff','dragonKills', 'dragonDiff','baronKills','baronDiff','riftKills','firstBlood','firstTower','firstInhib','firstDragon','firstBaron','firstRift']
#feature =['goldTotal','goldDiff','champKills','killDiff','towerKills','towerDiff','inhibKills','inhibDiff','dragonKills', 'dragonDiff','baronKills','baronDiff']#,'firstBlood','firstTower']
parameters = {'max_features': ['auto'],#range(1,len(feature)),
              'n_estimators' :  [100],
              'min_samples_leaf': [50],
              'n_jobs': [-1],
              'oob_score': [True,False]}

maxtime = df['time'].max()
timeline = []
for timestamp in range(maxtime+1):
    dft = df[df['time']==timestamp]
    if dft.shape[0] < 50:
        continue
    else:
        timeline.append(timestamp)
        
maxtime = len(timeline)    
forest = RandomForestClassifier()    
rvc = RandomForestClassifier(n_estimators=100,max_features='auto',min_samples_leaf=50,n_jobs=-1,oob_score=True)
featureImportances = np.zeros([len(timeline),len(feature)])
scores = []
for i in range(len(timeline)):
    timestamp = timeline[i]
    dft = df[df['time']==timestamp]
    if dft.shape[0] < 50:
        continue
    X = dft.iloc[:,3:df.shape[1]]
    y = dft['winner']
    #cv = cross_validation.ShuffleSplit(dft.shape[0], n_iter=20, test_size=0.2, random_state=50)
    #forest_model = grid_search.GridSearchCV(forest,param_grid=parameters,cv=cv)
    #forest_model.fit(X,y)
    X_train, X_test, y_train, y_test = cross_validation.train_test_split(X, y, test_size=.2)
    rvc.fit(X_train,y_train)
    dill.settings['recurse']=True
    #with open('./data/full_data/models/randomforestmodel_esports_%d.pkl'%timestamp,'wb') as outfile:
        #dill.dump(rvc,outfile)
    featureImportances[i] = rvc.feature_importances_
    #print featureImportances[i]
    modelScore = rvc.score(X_test,y_test)
    scores.append((timestamp,modelScore))

#dill.settings['recurse']=True
#with open('randomforestmodel_esports.pkl','wb') as outfile:
    #dill.dump(rvc,outfile)

score_df = pd.DataFrame(scores,columns=['time','accuracyScore'])
with open('./data/full_data/predictionaccuracy.csv','wb') as outfile:
    score_df.to_csv(outfile,header=True)

feature_df = pd.DataFrame(featureImportances,columns=feature) 
feature_df['time'] = timeline
with open('./data/full_data/feature_importances.csv','wb') as outfile:
    feature_df.to_csv(outfile,header=True)

    