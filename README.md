# Mander

**Mander** is a little ditty that I've been doing to see how I can group parts of a road network into neighborhoods or districts. This is achieved by considering all intersections of a road network as subgraphs successively unioning these subgraphs based on a strategy that prioritizes the unioning of low-weight subgraphs (i.e. subnetworks which have a small total distance) and of subgraphs which are separated by short edges.


Creating and using districts like this can have a lot of different uses, such as helping to decide on delivery service areas, or informing solutions to the contentious issue of gerrymandering. 

This project is not set up as a python module; just a standalone script with dependencies specified in requirements.txt. Postgres database connection in `db.py`. 

Use `run geo.py` to execute the algorithm. You will be prompted for a name of an area, such as "Manhattan" or "Prince Edward Island" that is geocodable by OpenStreetMap. The output will be a CSV that can be imported into a GIS as delimited text. From there you can generate maps of the areas based on phases that the algorithm went through from `0` upwards. There will be approximately 4 times as many subgraphs displayed in phase 0 than in phase 2.