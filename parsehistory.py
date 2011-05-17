#!/usr/local/bin/python
# -*- coding: UTF-8 -*-

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
import ppygis
import argparse
import logging

VERSION="0.2"
starttime = datetime.datetime.now() 
NAME="parsehistory"
DEBUG=True

parsing_node=False
parsing_way=False
parsing_relation=False
nnc = 0
wwc = 0
rrc = 0
nn = []
ww = []
rr = []
noderefs = []
n = None
w = None
r = None

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT,filename='%s.log' % NAME,level=logging.DEBUG)


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
	d = ""
	for attr in dir(obj):
		d += "obj.%s = %s\n" % (attr, getattr(obj, attr))
	return d

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
	global nnc,options
	c = conn.cursor()
	for n in nn:
#		logging.debug(dump(n))
		if options.output == 'pgsql':
			c.execute('insert into nodes values(%s,%s,%s,%s,%s,%s,%s,%s)',(n.id,n.version,n.user_id,n.timestamp,n.changeset_id,n.visible,n.tags,ppygis.Point(n.lon,n.lat,None,None,4326)))
		elif options.output == 'sqlite3':
			c.execute('insert into nodes values(?,?,?,?,?,?,?,?)',(n.lat,n.lon,n.version,n.user_id,n.user,n.id,n.timestamp,n.changeset_id))
			for k,v in n.tags.iteritems():
				c.execute('insert into tags values(?,?,?)',(n.id,k,v))
	conn.commit()
	c.close()
	nnc += len(nn)
	del nn[:]
	
def insert_ways(ww):
	global wwc
	c = conn.cursor()
	for w in ww:
		logging.debug("noderefs for %i is %s" % (w.id, noderefs))
		c.execute('insert into ways values(%s,%s,%s,%s,%s,%s,%s,%s)',(w.id,w.version,w.user_id,w.timestamp,w.changeset_id,w.visible,w.tags,w.noderefs))
		for k,v in w.tags.iteritems():
			logging.debug("this tag needs to be meaningfully inserted: (%s,%s)" % (k,v))
	conn.commit()
	c.close()
	wwc += len(ww)
	del ww[:]
	
def insert_relations(rr):
	global rrc
	c = conn.cursor()
	for r in rr:
		c.execute('insert into relations values(%s,%s,%s,%s,%s,%s,%s)',(r.id,r.version,r.user_id,r.timestamp,r.changeset_id,r.visible,r.tags))
		for m in r.members:
			c.execute('insert into members values(%s,%s,%s,%s)',(r.id,m.id,m.type,m.ref,m.role))
	conn.commit()
	c.close()
	rrc += len(rr)
	del rr[:]

# http://stackoverflow.com/questions/1036409/recursively-convert-python-object-graph-to-dictionary/1118038#1118038
def todict(obj, classkey=None):
    if isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = todict(obj[k], classkey)
        return obj
    elif hasattr(obj, "__iter__"):
        return [todict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, todict(value, classkey)) 
            for key, value in obj.__dict__.iteritems() 
            if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj

def start_element(name, attrs):
	global n,parsing_node,w,parsing_way,r,parsing_relation,noderefs
	if name == 'node':
		parsing_node=True
		n = node();
		n.lat = 'lat' in attrs and float(attrs['lat'])
		n.lon = 'lon' in attrs and float(attrs['lon'])
		n.version = 'version' in attrs and int(attrs['version'])
		n.user_id = 'uid' in attrs and int(attrs['uid'])
		n.user = 'user' in attrs and unicode(attrs['user'])
		n.id = 'id' in attrs and int(attrs['id'])
		n.visible = 'visible' in attrs and attrs['visible'] == "true"
		n.timestamp = 'timestamp' in attrs and iso8601.parse_date(attrs['timestamp'])
		n.changeset_id = 'changeset' in attrs and int(attrs['changeset'])
	elif name == 'way':
		parsing_way=True
		w = way();
		w.version = 'version' in attrs and int(attrs['version'])
		w.user_id = 'uid' in attrs and int(attrs['uid'])
		w.user = 'user' in attrs and unicode(attrs['user'])
		w.id = 'id' in attrs and int(attrs['id'])
		w.visible = 'visible' in attrs and attrs['visible'] == "true"
		w.timestamp = 'timestamp' in attrs and iso8601.parse_date(attrs['timestamp'])
		w.changeset_id = 'changeset' in attrs and int(attrs['changeset'])
	elif name == 'relation':
		parsing_relation=True
		r = relation();
		r.version = 'version' in attrs and int(attrs['version'])
		r.user_id = 'uid' in attrs and int(attrs['uid'])
		r.user = 'user' in attrs and unicode(attrs['user'])
		r.id = 'id' in attrs and int(attrs['id'])
		r.visible = 'visible' in attrs and attrs['visible'] == "true"
		r.timestamp = 'timestamp' in attrs and iso8601.parse_date(attrs['timestamp'])
		r.changeset_id = 'changeset' in attrs and int(attrs['changeset'])
	elif name == 'tag':
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
	elif name == 'nd' and parsing_way:
		#print '\tnoderef start:', attrs['ref']
		if not w:
			print "\tnoderef outside of way"
		else:
			noderefs.append('ref' in attrs and int(attrs['ref']))
	elif name == 'member' and parsing_relation:
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
	global n,parsing_node,w,parsing_way,r,parsing_relation,nn,nnc,ww,wwc,rr,rrc,options,noderefs
	if name == 'node':
		#print 'node end:', n.id
		#dump(n)
		#insert_node(n)
		nn.append(n)		
		parsing_node=False
		n = None
	elif name == 'way':
		#print 'way end:', w.id
		#dump(n)
		#insert_way(w)
		w.noderefs = noderefs
		ww.append(w)
		parsing_way = False
		del noderefs[:]
		w = None
	elif name == 'relation':
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
		sys.stdout.flush()
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
parser.add_argument('-U','--username',default='osm',help='PostgreSQL database user')
parser.add_argument('-W','--password',default='osm',help='PostgreSQL database password')
parser.add_argument('-H','--host',default='localhost',help='PostgreSQL database host')
parser.add_argument('-P','--port',help='PostgreSQL database port')
parser.add_argument('-O','--output',default='sqlite',choices=('sqlite','pgsql'),help='Where to write the OSM data to: SQLite or PostgreSQL/PostGIS')
parser.add_argument('-k','--hstore',action='store_true',help='Add hstore column for tags, only for PostGIS')


options=parser.parse_args()

f=open(path.abspath(options.infile))

if(options.output=='pgsql'):
	print "Going to use PostGIS database '%s' on %s" % (options.database, options.host)
	print "Using database user %s with password %s" % (options.username, options.password)
	conn_string = "host=%s dbname=%s user=%s password=%s" % (options.host,options.database,options.username,options.password)
	conn = psycopg2.connect(conn_string)
	conn.set_client_encoding('UTF8')
	psycopg2.extras.register_hstore(conn)

	with open('pgsql_simple_schema_0.6-hist.sql', 'r') as sqlf: #this is the same schema that osmosis uses. 
		sql = sqlf.read()
	c = conn.cursor()
	c.execute(sql)
	conn.commit()
	print "all PgSQL tables created"
	logging.debug("all pgsql tables created, ready for import")
	c.close()
elif(options.output=='sqlite3'):
	print "Going yo use SQLite database at %s" % path.abspath(options.outfile)
	if path.exists(path.abspath(options.outfile)):
		print "This file exists, tables will be overwritten if they exist"
	conn = sqlite3.connect(path.abspath(options.outfile))
	sql = """DROP TABLE IF EXISTS nodes;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS ways;
DROP TABLE IF EXISTS relations;
DROP TABLE IF EXISTS members;
CREATE TABLE nodes(lat real, lon real, version int, user_id int, user text, id int, timestamp integer, changeset_id integer);
CREATE TABLE ways(version int, user_id int, user text, id int, timestamp integer, changeset_id integer);
CREATE TABLE tags(feature_id int, k text, v text);
CREATE TABLE relations(version int, user_id int, user text, id int, timestamp integer, changeset_id integer);
CREATE TABLE members(relation_id int, type text, ref int, role text);"""
	c = conn.cursor()
	c.executescript(sql)
	print "all sqlite3 tables created"
	c.close()
	
p = xml.parsers.expat.ParserCreate()
logging.debug("expat parser created")

p.StartElementHandler = start_element
p.EndElementHandler = end_element
p.CharacterDataHandler = char_data

logging.debug("about to parse %s" % f.name)
p.ParseFile(f)
logging.debug("parsed %s" % f.name)

insert_nodes(nn)
insert_ways(ww)
insert_relations(rr)

print "operation took %s" % (datetime.datetime.now() - starttime)
print "total %i nodes, %i ways, %i relations." % (nnc, wwc, rrc)
if options.output == 'sqlite3':
	print "sqlite file at %s is size %s" % (path.abspath(options.outfile), size(float(path.getsize(path.abspath(options.outfile)))))
