osmhistoryparser
================

The goal of this script is to parse full osm history files as published on http://planet.openstreetmap.org/full-experimental/ (experimental extracts suitable for testing are available at ftp://ftp5.gwdg.de/pub/misc/openstreetmap/osm-full-history-extracts/110418/hardcut-bbox-xml/) and drop them into a database, recreating all the features and their previous versions correctly.

Included is a modified version of the osmosis PostgreSQL schema suitable for storing history.

Currently there is an experimental osmosis plugin that does this but I'm not very good at writing java so I started this.

status
------
implementation of full history parsing is on its way. Node versions for historic ways are stored through the waynodes table which includes version numbers for nodes as well as ways. There is no reverse lookup yet for intermediate changes to nodes that do not affect the way version, and no solution for the resulting intermediate way versions.

installation
------------

Tested on a homebrew python 2.7.1 install on Mac OSX. 
You need the following python modules:

* iso8601
* psycopg2
* ppygis

These are all available in the PyPi.

roadmap
-------
next version will:

* do reverse version lookup on nodes for ways.
* resolve historic versions of relations.

and further along the road:

* test performance for several in-memory storage techniques for nodes table. currently using sqlite3. look at stockpyle? memcached?

wanna help make this happen? Please do! Fork this and contribute. 

Best,
Martijn
