import numpy as np
from datetime import date, timedelta
import json

def main():
	f = open("./data/match.json","r")
	data = f.read().split('\n')
	
	N = len(data)-1
	for i in range (0,N):
		k = open('./data/Real/match_%d.json' % (i+1), 'w')
		k.write(data[i])
		k.close()
	f.close()	
	
if __name__ == "__main__":
	main()
