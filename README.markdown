
#Server setup

run the server with
 python webtorn.py

It'll start on port 8090; put it behind an nginx proxy. It can handle requests either in the root directory or under /panama. [read the code; this isn't the world's most complicated setup

#Requirements:
[these requirements could mostly be eliminated quite easily]

tornado (replacing web.py)
simplejson
mysqldb

