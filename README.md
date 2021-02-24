## About
Tool for Eve Online to find the nearest station belonging to an NPC corporation. A server hosting this tool is at http://nearest.ouroborus.org.

This project consists of two parts: Data conversion software to convert the EVE data into a structure more convenient for the web server; and a web application designed to run on the Google App Engine platform.

This repository includes a pre-compiled data set, `gae/data.py`. Building it isn't necessary.

## Build environment

* The Eve Online static data export
    * Download page: https://developers.eveonline.com/resource/resources
* Downloads: https://www.python.org/downloads/
    * 3.8.0 as of this writing (GAE is still 2.7)
    * Install jinja2: `pip install jinja2`
* Google App Engine SDK for Python:
    * Download page: https://cloud.google.com/appengine/downloads

## Building

`cd` into the directory, then run `./map.py` followed by `./reduce.py`. `map.py` can take quite a while depending on CPU speed as the YAML format isn't efficient for reading.
