import csv

total = 0
tap = 1

with open('taps.csv', 'rb') as csvfile:
  tapsReader = csv.reader(csvfile, delimiter=',', quotechar='|')
  for row in tapsReader:
	  print row[0]
	  print tap
	  if row[0] == str(tap):
		  print 'got here'
		  total = row[5]


print total
