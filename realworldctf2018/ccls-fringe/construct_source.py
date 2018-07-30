import json

a = json.load(open("cache.json"))

usr2var = {}

usr2type = a['usr2type']

l = [[" " for i in range(100)] for _ in range (70)]
l[0] = "#include<iostream>"
l[1] = "#include<vector>"
l[2] = "#include<ucontext>"

def f(x, loc):
	x = x.replace("std::","")
	s = loc.split("|")[0].split('-')
	a,b = map(int, s[0].split(":"))
	c,d = map(int, s[1].split(":"))
	
	if a == c and d - b == len(x) or a != c:
		l[a][b:b+len(x)] = [k for k in x]
		print "success", x,loc
	else:
		print "failed", x,loc, a,b,c,d
		

def g(x):
	snoffset = x['short_name_offset']
	snsize = x['short_name_size']
	shortname = x['detailed_name'][snoffset:snoffset+snsize]
	return shortname

for i in a['usr2var']:
	usr2var[i['usr']] = i


for i in a['usr2func']:
	print "FUNC"
	f(i['detailed_name'], i['extent'])
	sn = g(i)
	#f(sn, i['spell'])

	for j in i['vars']:
		print "VAR"
		j = usr2var[j]
		f(j['detailed_name'], j['extent'])
		sn = g(j)
		f(sn, j['spell'])

		for u in j['uses']:
			print "USE"
			f(sn, u)
	

for i in usr2type:
	
	sn = g(j)

	for j in i['vars']:
		j = usr2var[j['L']]
		dn = j['detailed_name']
		dn = dn.replace(sn+"::", "")
		f(dn, j['extent'])
		f(g(j), j['spell'])

	for j in i['instances']:
		j = usr2var[j]
		s = j['spell'].split("|")[0].split('-')
		f(j['detailed_name'], j['extent'])
		sn = g(j)
		f(sn, j['spell'])

		for u in j['uses']:
			print "USE"
			f(sn, u)

	for j in i['instances']:
		j = usr2var[j]
		f(j['detailed_name'], j['extent'])
		f(g(j), j['spell'])
		

	if 'extent' not in i:
		continue 

	f(i['detailed_name'], i['extent'])
	f(g(i), i['spell'])
	for u in i['uses']:
		f(g(i), u)

print len(usr2type)
g = open("partial_source.cc", "w")
g.write("\n".join(["".join(i).rstrip() for i in l]))
g.close()
