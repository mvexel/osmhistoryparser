osmhistoryparser
================

The goal of this script is to parse full osm history files as published on http://planet.openstreetmap.org/full-experimental/ and drop them into a database, recreating all the features and their previous versions correctly.

Currently there is an experimental osmosis plugin that does this but I'm not very good at writing java so I started this.

status
------
currently it does not do this. what it does do:
* read compressed or uncompressed osm xml files (also plain planet / api ones)
* store nodes, ways, relations, tags and relation members in separate tables preserving the relation between tags / members and the osm primitives they belong to.

It uses sqlite3 to store the data which is inefficient for large datasets.

installation
------------

Tested on a homebrew python install on Mac OSX. 
You need the following python modules:
* iso8601
* hurry.filesize

roadmap
-------
next version will:
* use postgresql for storage
* take postres database credentials and server params as arguments.

and further along the road:
* resolve historic ways and relations correctly
* do the database things in a separate thread for performance.

wanna help make this happen? Please do! Fork this and contribute. 

Best,
Martijn
