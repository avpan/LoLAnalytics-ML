import requests
import json

api_key = 'RGAPI-AD1044F2-48C3-46D6-A6DD-19D228A21027'
url = 'https://na.api.pvp.net/api/lol/na/v2.5/league/by-summoner/46126088/entry?api_key=%s' % api_key
try:
	r = requests.get(url)
	print r.json()
except:
	print "fail"
	
	
