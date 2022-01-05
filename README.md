# ACI Subscriber

## Sections
- [Description](#description)
- [How it Works?](#cisco-aci)
- [Websocket and ACI](#websocket-and-aci)
- [Parsing and Storing Data](#parsing-and-storing-data)
- [PostgreSQL](#postgresql)
- [Overall Flow Diagram](#overall-flow-diagram)
- [How To Install](#how-to-install)
- [Author Info](#author-info)

---

## Description
ACI Subscriber is a python based tool that can listen and subscribe desired MOs on APIC. It was created for one of my customer in order to automate Day-2 Operation of ACI within some other scripts (Unfortunately I am not able to share them at least now.)

---

## How it Works?

### Cisco ACI 
ACI fabric is SDN Soluiton from Cisco which can build and manage entire fabric from single managment controller called APIC. One of the major benefit of this controller is utilization of REST APIs. Any object can be configured or monitored via REST. That is how we retrieve raw data and later on parse it. 



> **Note:** Please refer official solution link [Cisco ACI for Data Center](https://www.cisco.com/c/en/us/solutions/data-center-virtualization/application-centric-infrastructure/index.html) for more information about ACI

> **Note:** Please refer [ACI Programmability](https://developer.cisco.com/docs/aci/#!introduction#aci-programmability) for more information about Programmability on ACI

---

### Websocket and ACI

According to [Wikipedia](https://en.wikipedia.org/wiki/WebSocket), WebSocket is a computer communications protocol, providing full-duplex communication channels over a single TCP connection.

Basically websocket is providing subscription to requested url or dn so that client can retrieve or to be informed if any change occurs on monitored item. 


APIC provides utilization of websocket for ACI Managed Objects(MO) so that any client can be updated about config or state change of tracked object.

Almost every object can be monitored/tracked. However in our case we choose to subscribe interface and epg config change events. But this script can be customized for user's own requirements.

If faults needs to be monitored and reflected to a web app or excel or even to a txt file, it can be done as well.


> **Examples for interface and epg MOs:**


> __"https://z.z.z.z/api/node/class/infraHPortS.json?rsp-subtree=full&subscription=yes&refresh-timeout=500?query-target=subtree"__

> __"https://z.z.z.z/api/node/class/fvAEPg.json?subscription=yes&refresh-timeout=500?query-target=subtree"__


### Parsing and Storing Data

After retriving raw data from APIC, in case of state change, we need to parse and store for future use.


In our case, script(aci_subscriber) has built in parser functions that can obtain required data. 


> **Note:** For each object that needs to be tracked, will require its own custom parser.


Storing data another important aspect of this project. In our case we need to keep meaningful data in an organized way so that those can reached anytime from multiple resources. As an example each user can have seperate excel workbooks those are connected to SQL db to load data. 

> **Note:** For more information about [Connecting to PostgreSQL from Excel](https://www.devart.com/odbc/postgresql/docs/excel.htm)

### PostgreSQL 

Since data needs to be stored in a SQL Db, postgreSQL is choosed.

Postgre can be installed or configured as docker container since it is easy to install and operate however if user has their pre-installed DB it can be used as well.

> **Note**: For more information about PostgreSQL docker image please visit [Postgres](https://hub.docker.com/_/postgres).

> **Note**: Please note that script has preconfigured for postgres, however you can tune it for dbs as well if required.

---

## Overall Flow Diagram 

![Flow Diagram](https://github.com/kilinchar/aci_subscribe/blob/master/Capture_jpeg.JPG)

---

## How To Install

Subscriber can be used alone with running aci_subscriber script alone or it can be used in containerized way. 



    Running Standalone Script:

    1. Copy content of folder named src.
    2. Edit config.py with your own variables.
    3. Install dependent libraries (pip install -r requirements.txt)
    4. Run aci_subscriber script (python aci_subscriber.py)


On the other hand  second way is advised one since you can install all dependencies in a seperate container without being affected from other services or packages.
    
    Running as a docker container:

    1. Download all contents to folder.
    2. Edit config.py under src folder with your own variables.
    3. Built docker image with below command line:
    > docker build -t aci_subscriber .
    4. Create and run docker container using previously created image:
    > docker run -d --restart unless-stopped aci_subscriber

If you have any questions or advice, feel free to reach me out. That is all. Enjoy with it.

---

## Author Info
- Linkedin - [Harun KILINC](https://www.linkedin.com/in/harunkilinc/)
