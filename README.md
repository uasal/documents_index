## Purpose
(see [issue](https://github.com/uasal/spacecoron_design_docs/issues/420))
A simple system single source of truth for project document metadata (title, document number, author name, possibly abstract) and location (link to where it is stored).

## Users
Project members across multiple institutions.

## Requirements
- for each document, the system stores and displays:
    - title
    - document identifier
    - doc_code (to allow for more descriptive identifier that can also be used to search by)
    - author name
    - compiled url
    - source url
    - abstract (optional)
- the author linked to a set of documents can edit the associated metadata (particularly important for keeping links up-to-date)
- has search functionality based on stored fields
- authentication - since no sensitive data will be stored, authentication is needed only to link authors to their documents and allow editing; Google auth ideal for minimum friction across collaboration

## Software stack
For a quick test system:
- Flask back-end
- Vue.js front-end
- sqlite database - not expecting more than 100k visits / day, more than 281 Tb or the need for high concurrency ([sqlite limitations]{https://www.sqlite.org/whentouse.html})
- Google auth
- ~~hosted on lavinia (https://lavinia.as.arizona.edu/)~~
- hosted on separate, encrypted server (caaodoc.as.arizona.edu)

## Long-term
Long term, the system might need to be able to store some / all documents. To allow for this, some possible future directions are:
- scale existing system to strengthen security to allow for storing ITAR docs (would storage capacity on lavinia also be an issue?)
- port to a fork of the LIGO DCC (https://dcc.ligo.org/login/FAQ.html ; https://github.com/ericvaandering/DocDB)
- port to a different system (AWS has a documentation database service; does Google?)

## To test:
1. Run the server-side Flask app in one terminal window (in the appropriate env, which here is called `dis`):
    ```
    $ cd server
    $ conda activate dis
    (env)$ conda install --file requirements.txt
    (env)$ flask run --port=5001 --debug
    ```

2. Run the client-side Vue app in a different terminal window:
    ```
    $ cd client
    $ npm install
    $ npm run dev
    ```
