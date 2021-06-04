import tornado.ioloop
import tornado.web
import logging
import psycopg2
import sys
PORT = 8888

logger=logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        logger.info("entered MainHandler.get function")
        self.write('Hello World! Exercise solved.')
        '''
        conn = psycopg2.connect(dbname="postgres", user="postgres", host="localhost", password="123456")
        logger.info('******conn = ', conn)
        cur = conn.cursor()
        cur.execute("SELECT * from test_table")
        rows = cur.fetchall()
        for row in rows:
            self.write( str(row[1]))
        cur.close()
        conn.close()
        '''
        logger.info("leaving Mainhandler.get function")

def make_app():
    logger.info("entered make_app function")
    return tornado.web.Application([
        (r"/dbcontents", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    logger.info(f"Listening on port {PORT}")
    app.listen(PORT)
    tornado.ioloop.IOLoop.current().start()

