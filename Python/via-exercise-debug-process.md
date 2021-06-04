# Via Home Exercise

Having no experience with Docker or Tornado, and having limited experience with SQL, when asked for a reasonable submission date, I estimated about two days for studying up. While I did manage to get about 50% through an online Docker course, I also had more interviews than I expected, which negatively impacted my assimilation of all the new information. <br>

1. The first thing I did once inside `hiring-debug-test`, was to `ls -a1` the contents of the directory and the subdirectory, `db`. I used `cat` to inspect every file. The first thing I noticed was that `/dbcontents/` wasn't anywhere in `server.py`. Instead, `/get_db_contents` was in the `make_app()` function. I double checked that the database name and other credentials were accurate. I checked that the Dockfiles were referencing the correct filenames.<br>
2. Before moving forward with debugging, I needed to see the current output when running the curl commands. I ran `docker image build -t server.py .` followed by `docker-compose up -d` before realizing the `-d` flag causes the container to run in the background as opposed to the foreground, where I would be able to montior logging. So I ran `docker-compose up` and used another terminal tab for my curl commands. I tried the following:
**Input:** `curl 0.0.0.0:8888/dbcontents`
**Output:** `<html><title>404: Not Found</title><body>404: Not Found</body></html>`
**Output in logs:** `WARNING:tornado.access:404 GET /dbcontents (172.18.0.1) 0.50ms`
**Input:** `curl 0.0.0.0:8888/get_db_contents`
**Output:** `<html><title>500: Internal Server Error</title><body>500: Internal Server Error</body></html>`
**Output in logs:** 
```
api_1  | ERROR:tornado.application:Uncaught exception GET /get_db_contents (172.18.0.1)
api_1  | HTTPServerRequest(protocol='http', host='0.0.0.0:8888', method='GET', uri='/get_db_contents', version='HTTP/1.1', remote_ip='172.18.0.1')
api_1  | Traceback (most recent call last):
api_1  |   File "/opt/conda/lib/python3.7/site-packages/tornado/web.py", line 1702, in _execute
api_1  |     result = method(*self.path_args, **self.path_kwargs)
api_1  |   File "server.py", line 21, in get
api_1  |     conn = psycopg2.connect("dbname='postgres' user='postgres' host='localhost' password='123456'")
api_1  |   File "/opt/conda/lib/python3.7/site-packages/psycopg2/__init__.py", line 127, in connect
api_1  |     conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
api_1  | psycopg2.OperationalError: could not connect to server: Connection refused
api_1  |        Is the server running on host "localhost" (127.0.0.1) and accepting
api_1  |        TCP/IP connections on port 5432?
api_1  | could not connect to server: Cannot assign requested address
api_1  |        Is the server running on host "localhost" (::1) and accepting
api_1  |        TCP/IP connections on port 5432?
api_1  | 
api_1  | ERROR:tornado.access:500 GET /get_db_contents (172.18.0.1) 2.26ms
```

Immediately I noticed the difference in error outputs, noting that using the `get_db_contents` elicited a more verbose error and cited the `server.py` code. I googled both errors separatly, but the needs of the OPs were too variable and distinct to be able to glean anything useful.

3. I tried modifying the `server.py`:
* `^C`ed the running container
* Saved the original `server.py` as `backup.server.py`
* Modified the `make_app()` function from:
```
def make_app():
    return tornado.web.Application([
        (r"/get_db_contents", MainHandler),
    ])
```
```
def make_app():
    logger.info("entered make_app function")
    return tornado.web.Application([
        (r"/dbcontents", MainHandler),
    ])
```
* `cat`ed the `server.py` to make sure it was new version
* Re-built `server.py`
* Ran `docker-compose up`
* Repeated step 2. 

I was getting the same errors, something wasn't right. <br>

4. I stopped the running containers, etc. I added debug statements in the code:
```
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        logger.info("entered MainHandler.get function")
        conn = psycopg2.connect(dbname="postgres", user="postgres", host="localhost", password="123456")
        cur = conn.cursor()
        cur.execute("SELECT * from test_table")
        rows = cur.fetchall()
        for row in rows:
            self.write( str(row[1]))
        cur.close()
        conn.close()
        logger.info("leaving Mainhandler.get function")

def make_app():
    logger.info("entered make_app function")
    return tornado.web.Application([
        (r"/dbcontents", MainHandler),
    ])
```
* Repeated the processes described in step #3. Again I was getting the same errors corresponding to `/dbcontents` and `/get_db_contents` except this time I could see that `get_db_contents` was making it into the `MainHandler` because I could see my print statement. However, it didn't explain why the system was responding to `/get_db_contents` when it was nowhere to be found in the `server.py` code. 

5. I rinsed and repeated, each time making sure with `docker image ls` that I was using the newest builds. This was an issue because for a reason I am unaware of, often I would rebuild server.py and I could see from `docker image ls` that it was still using an older build. 
* It wasn't until I had the idea of rebuilding `hiring-debug-test_api` that the system seemed to recognize `\dbcontents`. At this point the error messages were now successfully reversed, meaning that `curl 0.0.0.0:8888\dbcontents` was making it into the `MainHandler` and `curl 0.0.0.0:8888\get_db_contents` was returning the simple 404 error and would not make it into the `MainHandler` function. 

6. Next I looked at the interaction with the database. I compared it to [this](https://www.psycopg.org/docs/module.html) and [this](https://www.psycopg.org/docs/usage.html). 
* I tried changing the syntax for the `psycopg2.connect` into both example formats (without the inner single quotes and with double quotes only around the arguments) testing the system in between, nothing changed. I reverted the change
* Following the documenation, I added `cur.close()` and `conn.close()` :
```
        cur = conn.cursor()
        cur.execute("SELECT * from test_table")
        rows = cur.fetchall()
        for row in rows:
            self.write( str(row[1]))
        cur.close()
        conn.close()
```
No change in behaviour. <br>

7. I tried logging the output of `psycopg2.connect`, but based on the output logs, it didn't seem to make it out of:
```
        conn = psycopg2.connect(dbname="postgres", user="postgres", host="localhost", password="123456")
```
So, in the next step I tested my theory.<br>

8. I commented out everything other than my print statements in the `MainHandler` function:
```
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        logger.info("entered MainHandler.get function")
        self.write('mim test')
        '''
        conn = psycopg2.connect(dbname="postgres", user="postgres", host="localhost", password="123456")
        cur = conn.cursor()
        cur.execute("SELECT * from test_table")
        rows = cur.fetchall()
        for row in rows:
            self.write( str(row[1]))
        cur.close()
        conn.close()
        '''
        logger.info("leaving Mainhandler.get function")
```
* I added a simple `self.write('mim test')`.
* Everything ran perfectly and all my logging was output. 

9. I moved the `'''` down by one line. The output wasn't able to print `mim test`, which could be the result of having gotten stuck in a buffer while trying to connect to the server. 
10. At this point it had been 2 hours, so I stopped working on the assignment. 
**Theorized unexplored points of failure:** 
* `docker-compose.yml` should the db and the api be in the same working directory? is there a `postgres:5432` missing somewhere?
* Are the environment variables set incorrectly?
* Does server.py need a `try` `catch` block to ID the error more effectively?
<br>
<br>
### Questions:
**Diagnose the problems you see with the setup. In particular :**

**-   Is the API endpoint failing to return the required data ? Can you describe the reason(s) ?**
	- This was in part due to the `/dbcontents` being incorrectly named in `server.py`.  The problem was isolated to be the connection to the database.    
**-   Can you describe the steps you followed to diagnose the problem ?**
	- Please see above. 
    
**-   How would you fix the issues ? Please apply the required bug fixes to the code. \ How would you change the way the code and deployment files are organised (the directory structure)?**  

**How would you improve the API, specifically:**<br>
**-   Is the code releasing database connections as it should ? If not, can you change the code to improve that aspect?**
(For both questions) I'm unsure how this needs to be fixed, but the file organization was definitely something I considered as a point of failure. 
   
**-   How would you improve the error handling ?**  
**- Can you think of health checks you would add to the docker-compose file ? Are all the port mappings in the docker-compose file necessary ?**
(For both questions) I think something along the lines of the error handling and health checks implemented here would help: <br>
```
    healthcheck:
        test: ["CMD", "pg_isready -h localhost -p 5432 -U myuser"]
        interval: 30s
        timeout: 10s
        retries: 5
```
 

