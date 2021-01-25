import socket
import logging
import datetime
import threading
import random
import string
import pickle
import time
import os

testing = False
ID_LEN = 10
ID_CHARS = string.ascii_letters + string.digits
KEEP_ALIVE_CHAR = " "
'''class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'''''

if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(filename='logs\{:%Y_%m_%d_%H.%S}.log'.format(datetime.datetime.now()),
                            format='%(asctime)s | %(levelname)-8s | %(message)s', filemode='w')
logger = logging.getLogger("server_logger")
logger.setLevel(logging.DEBUG)

def log(message, display=True, level="info"):
    if level == "info":
        logger.info(message)
    elif level =="warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)
    elif level == "critical":
        logger.critical(message)
    else:
        return f"invalid level, level={level}"
    if display:
        print(message)

class user():
    def __init__(self, connection):
        self.connection = connection
        self.ip = str(self.connection[1][0])
        self.id = ''.join(random.sample(ID_CHARS, ID_LEN))
        self.name = None

    def dc(self):
        log(f'User {self.ip} (id = "{self.id}") (nickname = "{self.name}") has disconnected.')
        del self.id, self.ip

class server():
    def __init__(self):
        self.settings = ['Change server welcome message', 'qwe']
        self.welcome_msg = 'Welcome to this server'
        self.server_name = 'test server' #todo let user set this
        self.users = []
        self.recipients = []
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.connect((socket.gethostbyname('www.google.com'), 80))
        self.ip = self.main_socket.getsockname()[0]
        if testing:
            self.ip = "127.0.0.1"
        self.port = 6969  # random port
        self.main_socket.close()
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.main_socket.bind((self.ip, self.port))
        self.main_socket.listen()
        log(f"Server started successfully @ {self.ip}:{self.port}")

    def keep_alive(self):
        while True:
            self.broardcast_message(KEEP_ALIVE_CHAR)
            time.sleep(2)

    def handle_dc(self, user):
        self.tmp_name = user.name
        user.dc()
        self.users.remove(user)
        self.broardcast_message(f"{self.tmp_name} has disconnected.")

    def setup(self):
        # todo add server options and have admin set options using this function on server start
        print('-Server Setup-')
        while True:
            print('What would you like to change?')
            menu = [f'{self.settings.index(i) + 1}: {i}' for i in self.settings]
            menu.append('0: Exit setup and start server')
            menu = '\n'.join(menu)
            print(menu)
            option = None
            while option == None:
                option = input('> ')
                try:
                    option = int(option) - 1
                    if  not 0 <= option < len(self.settings):
                        raise Exception
                except:
                    print('Please enter a valid option')
                    option = None
                #todo actually implement selecting option and changing it

    def handle_user(self, connection):
        myself = threading.local()
        myself.this_user = user(connection)
        self.users.append(myself.this_user)
        try:
            self.send_message(myself.this_user, self.server_name)
            self.send_message(myself.this_user, f'Connecting to the server @ {self.ip}:{self.port}...')
        except:
            self.handle_dc(myself.this_user)
            return
        while True:
            try:
                self.data = pickle.loads(myself.this_user.connection[0].recv(1024))
                if self.data == '':
                    self.handle_dc(myself.this_user)
                    return
                if not myself.this_user.name:
                    myself.this_user.name = self.data # first thing client sends server is user's nickname set before client's attempt to connect
                    log(
                        f'User {myself.this_user.connection[1][0]} (id = "{myself.this_user.id}") (nickname = "{myself.this_user.name}") has connected.')
                    self.send_message(myself.this_user,
                                      f'You are connected to the server @ {self.ip}:{self.port} as {myself.this_user.name}')
                    self.send_message(myself.this_user, self.welcome_msg)
                    self.broardcast_message(f'{myself.this_user.name} has connected')
                else:
                    self.broardcast_message(f'<{myself.this_user.name}>: {self.data}')
                    log(f'<{myself.this_user.name}>: {self.data}')
            except:
                self.handle_dc(myself.this_user)
                break

    def handle_incoming(self):
        threading.Thread(target=self.keep_alive, args=()).start()
        while True:
            self.connection = self.main_socket.accept()
            threading.Thread(target=self.handle_user, args=(self.connection, )).start()

    def send_message(self, user, msg):
        if user in self.users:
            user.connection[0].send(pickle.dumps(str(msg)))

    def broardcast_message(self, msg):
        for u in self.users:
            threading.Thread(target=self.send_message, args=(u, msg)).start()


if __name__ == '__main__':
    main_server = server()
    main_server.setup()
    main_server.handle_incoming()
