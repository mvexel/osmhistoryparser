#!/usr/local/bin/python
# -*- coding: UTF-8 -*-

import xml.parsers.expat
import datetime
import iso8601
from osm import node,way,relation,member
import sys
from os import path
import psycopg2
from psycopg2 import extras
import ppygis
import argparse
import logging
import sqlite3

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
wnc = 0
nn = []
ww = []
wn = []
rr = []
noderefs = []
n = None
w = None
r = None
cut_nodes = 0

conn_nodememstore = sqlite3.connect(":memory:")
cursor_nodememstore = conn_nodememstore.cursor()
cursor_nodememstore.execute("create table nodes (id INT, timestamp TEXT, version INT);")



FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT,filename='%s.log' % NAME,level=logging.DEBUG)


def usage():
    print '''
Usage: python %s inputfile [outputfile]

The inputfile is an OSM XML file (.osm or .xml) and may 
be compressed (bz2 or gzip).
    ''' % (sys.argv[0])

def dump(obj):
    d = ""
    for attr in dir(obj):
        d += "obj.%s = %s\n" % (attr, getattr(obj, attr))
    return d

def postgis_point(lon,lat):
    return "ST_SetSRID(ST_MakePoint(%s, %s), 4326)" % (lon,lat)

def database_size():
	if c is None:
		return
	c.execute("select pg_size_pretty(pg_database_size('osm'))")
	return c.fetchone()[0]

def insert_nodes(nn):
    global nnc
    for n in nn:
        c.execute('insert into nodes values(%s,%s,%s,%s,%s,%s,%s,%s)',(n.id,n.version,n.user_id,n.timestamp,n.changeset_id,n.visible,n.tags,ppygis.Point(n.lon,n.lat,None,None,4326)))
        cursor_nodememstore.execute("insert into nodes values (?,?,?)",(n.id,n.timestamp.strftime("%Y%m%d%H%M%S"),n.version))
    conn.commit()
    conn_nodememstore.commit()
    nnc += len(nn)
    del nn[:]
    
def insert_ways(ww):
    global wwc
    for w in ww:
        c.execute('insert into ways values(%s,%s,%s,%s,%s,%s,%s,%s)',(w.id,w.version,w.user_id,w.timestamp,w.changeset_id,w.visible,w.tags,w.noderefs))
    conn.commit()
    wwc += len(ww)
    del ww[:]

def insert_waynodes(wn):
    global wnc
    for waynode in wn:
        c.execute("insert into way_nodes values (%s,%s,%s,%s,%s)",waynode)
    conn.commit()
    wnc += len(wn)
    del wn[:]

def insert_relations(rr):
    global rrc
    for r in rr:
        c.execute('insert into relations values(%s,%s,%s,%s,%s,%s,%s)',(r.id,r.version,r.user_id,r.timestamp,r.changeset_id,
        r.visible,r.tags))
        for m in r.members:
            c.execute('insert into relation_members values(%s,%s,%s,%s,%s)',(r.id,m.ref,m.type,m.role,m.sequence_id))
    conn.commit()
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
    global n,parsing_node,w,parsing_way,r,parsing_relation,noderefs,sequence_id,cut_nodes,sequence_id,wnc
    if name == 'node':
        parsing_node=True
        n = node()
        n.lat = 'lat' in attrs and float(attrs['lat'])
        n.lon = 'lon' in attrs and float(attrs['lon'])
        n.version = 'version' in attrs and int(attrs['version'])
        n.user_id = 'uid' in attrs and int(attrs['uid']) or 0
        n.user = 'user' in attrs and unicode(attrs['user']) or "__anonymous__"
        n.id = 'id' in attrs and int(attrs['id'])
        n.visible = 'visible' in attrs and attrs['visible'] == "true"
        n.timestamp = 'timestamp' in attrs and iso8601.parse_date(attrs['timestamp'])
        n.changeset_id = 'changeset' in attrs and int(attrs['changeset'])
    elif name == 'way':
        sequence_id = 0
        parsing_way=True
        w = way()
        w.version = 'version' in attrs and int(attrs['version'])
        w.user_id = 'uid' in attrs and int(attrs['uid']) or 0
        w.user = 'user' in attrs and unicode(attrs['user']) or "__anonymous__"
        w.id = 'id' in attrs and int(attrs['id'])
        w.visible = 'visible' in attrs and attrs['visible'] == "true"
        w.timestamp = 'timestamp' in attrs and iso8601.parse_date(attrs['timestamp'])
        w.changeset_id = 'changeset' in attrs and int(attrs['changeset'])
    elif name == 'relation':
        parsing_relation=True
        r = relation()
        r.version = 'version' in attrs and int(attrs['version'])
        r.user_id = 'uid' in attrs and int(attrs['uid']) or 0
        r.user = 'user' in attrs and unicode(attrs['user']) or "__anonymous__"
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
            noderef = 'ref' in attrs and int(attrs['ref'])
            timestamp_way = w.timestamp.strftime("%Y%m%d%H%M%S")
            # find node version that corresponds to way version
            # that is the last node version that has creation date before this way version creation date.
            cursor_nodememstore.execute("select max(timestamp),version from nodes where id = ? and timestamp <= ?",(noderef,timestamp_way))
            row = cursor_nodememstore.fetchone()
            if row[0] == None:
            	# Node does not exist in file, possibly because this version was not in the extract's bbox
            	# Solution for now is to cut this node out for this way-version.
            	cut_nodes += 1
            	logging.warn("node ref %i was cut from way %i version %i because the node was not in the file" % (noderef,w.id,w.version))
            else:
                noderefs.append(noderef)
                wn.append((w.id,w.version,noderef,row[1],sequence_id))
                sequence_id += 1
                wnc += 1
    elif name == 'member' and parsing_relation:
        #print '\tmember start:', attrs['ref']
        if not r:
            print "\tnmember outside of relation"
        else:
            m = member()
            m.type = 'type' in attrs and attrs['type']
            m.ref = 'ref' in attrs and attrs['ref']
            m.role = 'role' in attrs and attrs['role']
            m.sequence_id = sequence_id
            sequence_id += 1
            r.members.append(m)
            
def end_element(name):
    global n,parsing_node,w,parsing_way,r,parsing_relation
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
#    print "nodes in memory: %i - ways in memory: %i" %    (len(nn),len(ww))
    if not (len(nn) + len(ww) + len(wn)) % 1000 and (len(nn) + len(ww)) > 0:
        logging.debug("HIT nodes in memory: %i - ways in memory: %i" % (len(nn),len(ww)))
        difference = datetime.datetime.now() - starttime
        weeks, days = divmod(difference.days, 7)
        minutes, seconds = divmod(difference.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if days > 0:
            sys.stdout.write("\rnodes: %ik - ways: %ik - way-nodes: %ik - rels: %ik - elapsed: %d days %02d:%02d:%02d" % (
                (nnc+len(nn))/1000,
                (wwc+len(ww))/1000,
                (wnc+len(wn))/1000,
                (rrc+len(rr))/1000,
                days,
                hours,
                minutes,
                seconds,
            ))
        else:
            sys.stdout.write("\rnodes: %ik - ways: %ik - way-nodes: %ik - rels: %ik - elapsed: %02d:%02d:%02d" % (
                (nnc+len(nn))/1000,
                (wwc+len(ww))/1000,
                (wnc+len(wn))/1000,
                (rrc+len(rr))/1000,
                hours,
                minutes,
                seconds,
            ))
        sys.stdout.flush()
        insert_nodes(nn)
        insert_ways(ww)
        insert_waynodes(wn)
        insert_relations(rr)
        
def char_data(data):
    #print 'Character data:', repr(data)
    del data

parser = argparse.ArgumentParser(description='OpenStreetMap full history planet parser.')
parser.add_argument('infile')
parser.add_argument('-d','--database',default='osm')
parser.add_argument('-U','--username',default='osm',help='PostgreSQL database user')
parser.add_argument('-W','--password',default='osm',help='PostgreSQL database password')
parser.add_argument('-H','--host',default='localhost',help='PostgreSQL database host')
parser.add_argument('-P','--port',help='PostgreSQL database port')
parser.add_argument('-k','--hstore',action='store_true',help='Add hstore column for tags')


options=parser.parse_args()

f=open(path.abspath(options.infile))

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
insert_waynodes(wn)
insert_relations(rr)

print "\n\noperation took %s" % (datetime.datetime.now() - starttime)
print "total %i nodes, %i ways, %i waynodes, %i relations." % (nnc, wwc, wnc, rrc)
print "%i nodes were left out." % (cut_nodes,)
print "size of database is %s" % (database_size(),)

cursor_nodememstore.close()
conn_nodememstore.close()

c.close()
conn.close()
