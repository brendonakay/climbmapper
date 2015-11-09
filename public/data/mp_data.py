import json, requests, psycopg2, collections

class MPData:
	
	def init(self):
		print "init"
		#DB connection properties
		conn = psycopg2.connect(dbname = 'climbmapper', host= 'localhost', port= 5432, user = 'postgres',password= '29just29')
		cur = conn.cursor()  ## open a cursor
		
		cur.execute("TRUNCATE route;")
		cur.execute("TRUNCATE tick;")
		cur.execute("TRUNCATE todo;")
		conn.commit()
		conn.close()	
		print "cleaned db"
		
	def getToDos(self):
		#DB connection properties
		conn = psycopg2.connect(dbname = 'climbmapper', host= 'localhost', port= 5432, user = 'postgres',password= '29just29')
		cur = conn.cursor()  ## open a cursor
		
		urlRoot = "http://www.mountainproject.com/data?action=getToDos"
		urlPropId = "&userId=106251374"
		urlPropStartPos = "&startPos="
		urlPropStartPosList = [0, 200, 400]
		mpKey = "&key=106251374-a0e6d43518505bec412a547956f25216"
		toDoList = []
		
		
		toDoCt = 1
		for pos in urlPropStartPosList:
			url = urlRoot + urlPropId + urlPropStartPos + str(pos) + mpKey
			resp = requests.get(url=url)
			toDos = json.loads(resp.text)								
			
			for toDoId in toDos["toDos"]:
				toDoList.append(toDoId)
				query = cur.mogrify("INSERT INTO todo(id,routeid,climberid) VALUES (%s, %s, %s)", (str(toDoId), str(toDoId), str(1)))
						
				cur.execute(query)
				conn.commit()
				
				toDoCt += 1
		
		conn.close()
		return toDoList
	
	
	def getTicks(self):
		
		#DB connection properties
		conn = psycopg2.connect(dbname = 'climbmapper', host= 'localhost', port= 5432, user = 'postgres',password= '29just29')
		cur = conn.cursor()  ## open a cursor
		
		root = "http://www.mountainproject.com/data?action=getTicks"
		uid = "&userId=106251374"
		key = "&key=106251374-a0e6d43518505bec412a547956f25216"
		
		
		# the api returns a max of 200 ticks in a request so we have to do this in chunks
		reqChunks = 0
		ticks = {}
		ticksArr = []
		while reqChunks < 600:
			reqStartPos = "&startPos=" + str(reqChunks)
			url = root + uid + key + reqStartPos

			resp = requests.get(url=url)
			ticksResp = json.loads(resp.text)
			
			if reqChunks == 0:
				hardestTick = ticksResp["hardest"]
				#print hardestTick
			
			# {"date": "2015-10-16", "notes": "pretty ok", "routeId": 106360348}
			for tick in ticksResp["ticks"]:
				ticksArr.append(tick["routeId"])
				query = cur.mogrify("INSERT INTO tick(id,routeid,climberid,notes,date) VALUES (%s, %s, %s, %s, %s)", (str(tick["routeId"]), str(tick["routeId"]), str(1), tick["notes"], str(tick["date"])))
						
				cur.execute(query)
				conn.commit()

			reqChunks = reqChunks + 200
			
		conn.close()	
		return ticksArr
		
	# @contentType can be 'todo' or 'tick'	
	def getRoutes(self, idsList, contentType):
		
		#DB connection properties
		conn = psycopg2.connect(dbname = 'climbmapper', host= 'localhost', port= 5432, user = 'postgres',password= '29just29')
		cur = conn.cursor()  ## open a cursor
		
		root = "http://www.mountainproject.com/data?action=getRoutes&routeIds="
		ids = ''
	 	key = "&key=106251374-a0e6d43518505bec412a547956f25216"
		
		
		cur.execute("SELECT id, usa, hueco FROM grade;")
		global gradesLookup
		gradesLookup = cur.fetchall()	
		
		cur.execute("SELECT id, type FROM route_type;")	
		global typeLookup
		typeLookup = cur.fetchall()	
		
		cur.execute("SELECT a.id as areaId, a.name as areaName, c.id as cragId, c.name as cragName FROM area a INNER JOIN crag c ON a.id = c.area;")	
		global cragLookup
		cragLookup = cur.fetchall()	
		
		cur.execute("SELECT a.id as areaId, a.name as areaName FROM area a;")	
		global areaLookup
		areaLookup = cur.fetchall()	
		
		cur.execute("SELECT id FROM route;")	
		global routeLookup
		routeLookup = cur.fetchall()	
		
		idCt = 1
		rows = []
		idTracking = []
	 	for id in idsList:
			ids += str(id)
			ids += ","
	
			if idCt % 100 == 0 or idCt == len(idsList):		
				ids = ids.rstrip(",")	
				url = root + ids + key			
					
				if idCt == 100:
					resp = requests.get(url=url)
					routes = json.loads(resp.text)
				else:
					resp = requests.get(url=url)
					for rt in json.loads(resp.text)["routes"]:
						
						# Check if the route exists in the db
						routeExists = self.routeExists(rt["id"])
						
						# Check if this is a duplicate route
						# Could be caused by duplicate Ticks
						# We want to avoid adding duplicate routes to the DB		
						if rt["id"] in idTracking:
							routeExists = True

						if routeExists is False:
							routes["routes"].append(rt)	
							area = ','.join(rt["location"])
							
							# Locations from MP are arrays of location names
							thisLocArr = rt["location"]
							thisAreaId = self.getAreaMatchId(reversed(thisLocArr))
							if thisAreaId == 999:
								print thisLocArr
							thisCragId = self.getCragMatchId(reversed(thisLocArr))
							rating = self.getCleanRating(str(rt["rating"]))
							routeType = self.getRouteType(rt["type"])
							
							# Get the grade
							if "boulder" in rt["type"].lower():
								grade = self.getBoulderGrade(rating)
							else:
								grade = self.getYDSGrade(rating)							
							
							if len(str(rt["pitches"])) > 0:
								pitches = rt["pitches"]
							else:
								pitches = 0 # a better default than n/a

							query = cur.mogrify("INSERT INTO route(id,routeid,name,area,type,grade,mpurl,mpimgmedurl,mpimgsmallurl,mpstars,mpstarvotes,pitches,crag) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (str(rt["id"]), str(rt["id"]), rt["name"], str(thisAreaId), str(routeType), str(grade), str(rt["url"]), str(rt["imgMed"]), str(rt["imgSmall"]), str(rt["stars"]), str(rt["starVotes"]), str(pitches), str(thisCragId)))

							cur.execute(query)
							conn.commit()
							
							# tracking to prevent duplicates which can occur with Ticks
							idTracking.append(rt["id"])
							
							# TODO: add additional info to db table		
							#{u'rating': u'V2', u'name': u'Super Slab', u'url': u'http://www.mountainproject.com/v/super-slab/106042278', 
							#u'imgMed': u'http://www.mountainproject.com/images/24/49/106042449_medium_7fd478.jpg',
							#u'pitches': u'', u'starVotes': u'6', u'imgSmall': u'http://www.mountainproject.com/images/24/49/106042449_small_7fd478.jpg', 
							#u'location': [u'Colorado', u'Morrison/Evergreen', u'Morrison Boulders', u'The Dark Side'], u'stars': u'3.8', 
							#u'type': u'Boulder', u'id': u'106042278'}
				ids = ''
			idCt += 1	
		conn.close()		
		
		#self.printRoutesInfo(routes)
	
	
	def getAreaMatchId(self, locationArr):
		for loc in locationArr:		
			for a in areaLookup:
				aId = a[0]
				aName = a[1]
				
				if aName.lower().lstrip("*").replace(" ", "") == loc.lower().lstrip("*").replace(" ", ""):
					return aId
		
		# no match found
		return -1
	
	
	# currently only matching crags with known areas (check sql query for cragLookup)
	def getCragMatchId(self, locationArr):
		for loc in locationArr:	
			for a in cragLookup:
				cId = a[2]
				cName = a[3]
				
				if cName.lower().lstrip("*").replace(" ", "") == loc.lower().lstrip("*").replace(" ", ""):
					return cId
		
		#no match found
		return -1
	
	def routeExists(self, inRouteId):
		for routeId in routeLookup:
			if str(routeId[0]) == str(inRouteId):
				return True
				
		return False
	
	
	def getCleanRating(self, rating):
		rating = rating.lower().replace("r", "")
		rating = rating.replace("pg13", "")
		rating = rating.replace("/b", "")
		rating = rating.replace("/c", "")
		rating = rating.replace("/d", "")
		rating = rating.replace("-2", "")
		rating = rating.replace("-3", "")
		rating = rating.replace("-4", "")
		rating = rating.replace("-5", "")
		rating = rating.replace("-6", "")
		rating = rating.replace("-7", "")
		rating = rating.replace("-8", "")
		rating = rating.replace("-9", "")
		rating = rating.replace("-10", "")
		rating = rating.replace("-11", "")
		rating = rating.replace("-12", "")
		rating = rating.replace("-13", "")
		rating = rating.replace("-14", "")
		rating = rating.replace("-15", "")
		rating = rating.replace("-easy", "")
		rating = rating.replace("easy snow", "")
		rating = rating.replace("?", "")
		rating = rating.replace("x", "")
		rating = rating.replace("+", "")
		rating = rating.replace("-", "")
		rating = rating.strip()
		
		return rating				
					
							
	def getCleanTypeName(self, type):
		# We are doing this if/else check because types can come in all kinds of combinations
		# I.E. "trad, bouder"
		if "boulder" in type.lower():
			# sometimes types are boulder, trad. this is non-sense. its boulder
			type = "Boulder"	
		elif "trad" in type.lower():
			# i don't care if it's "sport, trad". lets consider it trad if you use passive gear
			type = "Trad"
		elif "alpine" in type.lower():
			type = "Alpine"
		elif "sport" in type.lower():
			type = "Sport"
		elif "tr" in type.lower():
			type = "Top-Rope"
		
		return type


	def getRouteType(self, type):
		type = self.getCleanTypeName(type)		
		for tRow in typeLookup:
			typeId = tRow[0]
			typeName = tRow[1]
				
			if typeName.lower() in type.lower():
				return typeId
		
		print "Can't find type = ", typeName
		return 999


	def getYDSGrade(self, inGrade):
		found = False
		for row in gradesLookup:
			gradeId = row[0]
			ydsGrade = row[1]
			boulderGrade = row[2]

			if inGrade in ydsGrade:
				return gradeId
		
		# If we got this far there was no match for rope YDS grades. 
		# Lets check if its a boulder grade
		grade = self.getBoulderGrade(inGrade, gradesLookup)
		
		if grade == 999:
			print "Missing YDS and boulder grade -> ", inGrade
		return grade
	
	
	def getBoulderGrade(self, inGrade):
		for row in gradesLookup:
			gradeId = row[0]
			
			if row[2] is None:
				boulderGrade = ""
			else:
				boulderGrade = row[2].lower()
				boulderGrade = boulderGrade.replace("+", "")
				boulderGrade = boulderGrade.replace("-", "")
				boulderGrade = boulderGrade.strip()

			if inGrade in boulderGrade:
				return gradeId		
		
		return 999


	def printRoutesInfo(self, routesJSON):
		routeCt = 1
		print routesJSON["routes"]
		for route in routesJSON["routes"]:
			print "Route # " , routeCt
			print 
			print route["id"]
			print route["name"]
			print route["type"]
			print route["rating"]
			print route["stars"]
			print route["starVotes"]
			print route["pitches"]
			print route["location"]
			locationList = route["location"]
			print locationList[0]  # Root - State
			
			locationCt = 1
			locationListLen = len(locationList)
			for locationStep in locationList:	
				if locationCt == 1:
					print "Root = " + locationStep
				elif locationCt > 1 and locationCt < locationListLen:
					print "Area / Sub Area " + str(locationCt) + " = " + locationStep
				elif locationCt == locationListLen:
					print "Crag = " + locationStep	
					
				locationCt += 1
			print route["url"]
			
			routeCt += 1
		print "Route Count = " + str(routeCt)


if __name__ == '__main__':
	
	MPData = MPData()
	MPData.init()
	toDoIdList = MPData.getToDos()
	MPData.getRoutes(toDoIdList, 'todo')
	
	tickIdList = MPData.getTicks()
	MPData.getRoutes(tickIdList, 'tick')