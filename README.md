## About
Tool for Eve Online to find the nearest station belonging to an NPC corporation. A server hosting this tool is at http://nearest.ouroborus.org.

This project consists of two parts: Data conversion software to convert the EVE data into a structure more convenient for the web server; and a web application designed to run on the Google App Engine platform.

## Build environment

* The Eve Online static data export
    * Download page: https://developers.eveonline.com/resource/resources
* Downloads: https://www.python.org/downloads/
    * 3.8.0 as of this writing (GAE is still 2.7)
    * Install jinja2: `pip install jinja2`
* Google App Engine SDK for Python:
    * Download page: https://cloud.google.com/appengine/downloads

## Building

* Download the dataset fro EVE Online's site
* `cd` into the directory
* Mangler configuration is in `config.yaml`
* `python map.py`
  * This can take a while
* `python reduce.py`
* Move the generated file (`testdata.py`) to the `gae` folder and rename it to `data.py`
* `cd gae`
* `dev_appserver.py app.yaml`
