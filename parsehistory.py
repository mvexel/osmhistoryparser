import xml.parsers.expat
import datetime
import iso8601
from osm import node,way,relation,member
import sqlite3
import sys
from os import path
from hurry.filesize import size
import bz2
import gzip
import string
import psycopg2
import psycopg2.extras
import argparse

VERSION="0.2"
PGSQL= False

starttime = datetime.datetime.now() 

parsing_node=False
parsing_way=False
parsing_relation=False
nnc = 0
wwc = 0
rrc = 0
nn = []
ww = []
rr = []
n = None
w = None
r = None

def usage():
	print '''
Usage: python %s inputfile [outputfile]

The inputfile is an OSM XML file (.osm or .xml) and may 
be compressed (bz2 or gzip).

The outputfile is the sqlite3 file where the resulting 
data is stored. Defaults to osmhistory.db in the current 
working directory.
	''' % (sys.argv[0])

def dump(obj):
	for attr in dir(obj):
		print "obj.%s = %s" % (attr, getattr(obj, attr))

def create_tables_sqlite():
	c = conn.cursor()
	c.execute('drop table if exists nodes')
	c.execute('drop table if exists tags')
	c.execute('drop table if exists ways')
	c.execute('drop table if exists relations')
	c.execute('drop table if exists members')
	c.execute('create table nodes(lat real, lon real, version int, user_id int, user text, id int, timestamp integer, changeset_id integer)')
	c.execute('create table ways(version int, user_id int, user text, id int, timestamp integer, changeset_id integer)')
	c.execute('create table tags(feature_id int, k text, v text)')
	c.execute('create table relations(version int, user_id int, user text, id int, timestamp integer, changeset_id integer)')
	c.execute('create table members(relation_id int, type text, ref int, role text)')
	conn.commit()
	print "all tables created"
	c.close()

def create_tables_pgsql():
	with open('pgsql_simple_schema_0.6.sql', 'r') as f: #this is the same schema that osmosis uses. 
		sql = f.read()
	c = conn.cursor()
	c.execute(sql)
	conn.commit()
	print "all tables created"
	c.close()
	
def insert_node(n): #deprecated
	c = conn.cursor()
	c.execute('insert into nodes values(?,?,?,?,?,?,?,?)',(n.lat,n.lon,n.version,n.user_id,n.user,n.id,n.timestamp,n.changeset_id))
	for k,v in n.tags.iteritems():
		c.execute('insert into tags values(?,?,?)',(n.id,k,v))
	conn.commit()
	c.close()
	
def postgis_point(lon,lat):
	return "ST_SetSRID(ST_MakePoint(%s, %s), 4326)" % (lon,lat)

def insert_nodes(nn):
	global nnc
	c = conn.cursor()
	tagcount=0
	for n in nn:
		if PGSQL:
			SQL = "INSERT INTO nodes VALUES(%s,%s,%s,%s,%s,%s," + postgis_point(n.lon,n.lat) + ");"
			c.execute(SQL,(n.id,n.version,n.user_id,n.timestamp,n.changeset_id,n.tags))
		else:
			c.execute('insert into nodes values(?,?,?,?,?,?,?,?)',(n.lat,n.lon,n.version,n.user_id,n.user,n.id,n.timestamp,n.changeset_id))
			for k,v in n.tags.iteritems():
				c.execute('insert into tags values(?,?,?)',(n.id,k,v))
				tagcount+=1
	conn.commit()
	c.close()
	#print "%i nodes and %i tags inserted..." % (len(nn),tagcount)
	nnc += len(nn)
	del nn[:]
	
def insert_ways(ww):
	global wwc
	tagcount = 0
	c = conn.cursor()
	for w in ww:
		c.execute('insert into ways values(?,?,?,?,?,?)',(w.version,w.user_id,w.user,w.id,w.timestamp,w.changeset_id))
		for k,v in w.tags.iteritems():
			c.execute('insert into tags values(?,?,?)',(w.id,k,v))
			tagcount+=1
	conn.commit()
	c.close()
	#print "%i ways and %i tags inserted..." % (len(ww),tagcount)
	wwc += len(ww)
	del ww[:]
	
def insert_relations(rr):
	global rrc
	tagcount=0
	membercount=0
	c = conn.cursor()
	for r in rr:
		c.execute('insert into relations values(?,?,?,?,?,?)',(r.version,r.user_id,r.user,r.id,r.timestamp,r.changeset_id))
		for k,v in r.tags.iteritems():
			c.execute('insert into tags values(?,?,?)',(r.id,k,v))
			tagcount+=1
		for m in r.members:
			c.execute('insert into members values(?,?,?,?)',(r.id,m.type,m.ref,m.role))
			membercount+=1
	conn.commit()
	c.close()
	#print "%i relations, %i tags and %i members inserted..." % (len(rr),tagcount,membercount)
	rrc += len(rr)
	del rr[:]

def start_element(name, attrs):
	global n,parsing_node,w,parsing_way,r,parsing_relation
	if name == 'node':
		#print 'node start:', attrs['id']
		#print 'node:', attrs
		parsing_node=True
		n = node();
		n.lat = 'lat' in attrs and attrs['lat']
		n.lon = 'lon' in attrs and attrs['lon']
		n.version = 'version' in attrs and attrs['version']
		n.user_id = 'user_id' in attrs and attrs['user_id']
		n.user = 'user' in attrs and attrs['user']
		n.id = 'id' in attrs and attrs['id']
		n.timestamp = 'timestamp' in attrs and iso8601.parse_date(attrs['timestamp'])
		n.changeset_id = 'changeset_id' in attrs and attrs['changeset_id']
	if name == 'way':
		#print 'way start:', attrs['id']
		#print 'node:', attrs
		parsing_way=True
		w = way();
		w.version = 'version' in attrs and attrs['version']
		w.user_id = 'uit' in attrs and attrs['user_id']
		w.user = 'user' in attrs and attrs['user']
		w.id = 'id' in attrs and attrs['id']
		w.timestamp = 'timestamp' in attrs and iso8601.parse_date(attrs['timestamp'])
		w.changeset_id = 'changeset_id' in attrs and attrs['changeset_id']
	if name == 'relation':
		#print 'relation start:', attrs['id']
		#print 'node:', attrs
		parsing_relation=True
		r = relation();
		r.version = 'version' in attrs and attrs['version']
		r.user_id = 'uit' in attrs and attrs['user_id']
		r.user = 'user' in attrs and attrs['user']
		r.id = 'id' in attrs and attrs['id']
		r.timestamp = 'timestamp' in attrs and iso8601.parse_date(attrs['timestamp'])
		r.changeset_id = 'changeset_id' in attrs and attrs['changeset_id']
	if name == 'tag':
		#print '\ttag start:', attrs['k']
		if parsing_node and not n:
			print "\ttag outside of node"
		elif parsing_way and not w:
			print "\ttag outside of way"
		elif parsing_relation and not r:
			print "\ttag outside of relation"
		else:
			if parsing_node:
				p = n
			elif parsing_way:
				p = w
			elif parsing_relation:
				p = r
			if 'k' in attrs and 'v' in attrs and p:
				p.tags[attrs['k']] = attrs['v']
	if name == 'nd' and parsing_way:
		#print '\tnoderef start:', attrs['ref']
		if not w:
			print "\tnoderef outside of way"
		else:
			w.noderefs = 'ref' in attrs and attrs['ref']
	if name == 'member' and parsing_relation:
		#print '\tmember start:', attrs['ref']
		if not r:
			print "\tnmember outside of relation"
		else:
			m = member()
			m.type = 'type' in attrs and attrs['type']
			m.ref = 'ref' in attrs and attrs['ref']
			m.role = 'role' in attrs and attrs['role']
			r.members.append(m)
			
def end_element(name):
	global n,parsing_node,w,parsing_way,r,parsing_relation,nn,nnc,ww,wwc,rr,rrc,options
	if name == 'node':
		#print 'node end:', n.id
		#dump(n)
		#insert_node(n)
		nn.append(n)		
		parsing_node=False
		n = None
	if name == 'way':
		#print 'way end:', w.id
		#dump(n)
		#insert_way(w)
		ww.append(w)
		parsing_way=False
		w = None
	if name == 'relation':
		#print 'relation end:', r.id
		#dump(r)
		#insert_way(r)
		rr.append(r)
		parsing_relation=False
		r = None

	#elif name == 'tag':
		#print '\ttag end'
#	print "nodes in memory: %i - ways in memory: %i" %	(len(nn),len(ww))
	if not (len(nn) + len(ww)) % 1000:
		#print "HIT nodes in memory: %i - ways in memory: %i" % (len(nn),len(ww))
		fsize = float(path.getsize(path.abspath(options.outfile)))
		difference = datetime.datetime.now() - starttime
		weeks, days = divmod(difference.days, 7)
		minutes, seconds = divmod(difference.seconds, 60)
		hours, minutes = divmod(minutes, 60)
		if days > 0:
			sys.stdout.write("\rnodes: %ik - ways: %ik - rels: %ik - elapsed: %d days %02d:%02d:%02d - file size %s     " % (
				(nnc+len(nn))/1000,
				(wwc+len(ww))/1000,
				(rrc+len(rr))/1000,
				days,
				hours,
				minutes,
				seconds,
				size(fsize)
			))
		else:
			sys.stdout.write("\rnodes: %ik - ways: %ik - rels: %ik - elapsed: %02d:%02d:%02d - file size %s      " % (
				(nnc+len(nn))/1000,
				(wwc+len(ww))/1000,
				(rrc+len(rr))/1000,
				hours,
				minutes,
				seconds,
				size(fsize)
			))
		insert_nodes(nn)
		insert_ways(ww)
		insert_relations(rr)
		
def char_data(data):
	#print 'Character data:', repr(data)
	del data

parser = argparse.ArgumentParser(description='OpenStreetMap full history planet parser.')
parser.add_argument('infile')
parser.add_argument('outfile',nargs='?', default='osm.db',help='path to SQLite data file (SQLite only)')
parser.add_argument('-d','--database',default='osm')
parser.add_argument('-U','--username',metavar='username',default='osm',help='PostgreSQL database user')
parser.add_argument('-W','--password',metavar='password',default='osm',help='PostgreSQL database password')
parser.add_argument('-H','--host',metavar='host',default='localhost',help='PostgreSQL database host')
parser.add_argument('-P','--port',metavar='port',help='PostgreSQL database port')
parser.add_argument('-O','--output',metavar='outputformat',default='sqlite',choices=('sqlite','pgsql'),help='Output format (SQLite or PostGIS)')
parser.add_argument('-k','--hstore',action='store_true',help='Add hstore column for tags, only for PostGIS')

options=parser.parse_args()

if(options.output=='pgsql'):
	print "Going to use PostGIS database '%s' on %s" % (options.database, options.host)
	print "Using database user %s with password %s" % (options.username, options.password)
else:
	print "Going yo use SQLite database at %s" % path.abspath(options.outfile)
	if path.exists(path.abspath(options.outfile)):
		print "This file exists, tables will be overwritten if they exist"

f=open(path.abspath(options.infile))
conn = sqlite3.connect(path.abspath(options.outfile))

p = xml.parsers.expat.ParserCreate()

p.StartElementHandler = start_element
p.EndElementHandler = end_element
p.CharacterDataHandler = char_data

create_tables_sqlite()

p.ParseFile(f)

insert_nodes(nn)
insert_ways(ww)
insert_relations(rr)

print "operation took %s" % (datetime.datetime.now() - starttime)
print "total %i nodes, %i ways, %i relations." % (nnc, wwc, rrc)
print "sqlite file at %s is size %s" % (path.abspath(options.outfile), size(float(path.getsize(path.abspath(options.outfile)))))
