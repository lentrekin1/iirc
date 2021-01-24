import PySimpleGUI as sg
import socket
import IPy
import pickle
import threading
import traceback
import time

testing = False
WINDOW_TITLE = 'bruh irc'
WINDOW_SIZE = (500, 500)
MAX_NICKNAME_LEN = 10
BUFFER_SIZE = 1024
KEEP_ALIVE_CHAR = " "
THEME = 'DarkBlue1'
sg.theme(THEME)
all_layouts = {'setup': [[sg.Text(WINDOW_TITLE, text_color='red', key='setup_title')],
                         [sg.Text('Enter the IP Address of the Server Below:', key='ip_banner')],
                         [sg.InputText(key='ip')],
                         [sg.Text('Enter the Port to Connect on Below:', key='port_banner')],
                         [sg.InputText(key='port')],
                         [sg.Text('Enter Your Nickname Below:', key='name_banner')],
                         [sg.InputText(key='name')],
                         [sg.Button('Connect', key='connect')],
                         [sg.Text('', size=(WINDOW_SIZE[0], 10), key='setup_error')]],

               'main': [[sg.Text(WINDOW_TITLE, text_color='red', key='main_title')],
                        [sg.Multiline(size=(WINDOW_SIZE[0], 20), autoscroll=True, disabled=True, key='chatbox')],
                        [sg.Text("Enter your message below:", key='input_banner'), sg.Button('Send message', key='send'), sg.Button('Disconnect', key='dc')],
                        [sg.InputText(key='input')],
                        [sg.Text("", size=(WINDOW_SIZE[0], 10), key='main_error')]]}

class client():
    def __init__(self):
        self.messages = []
        self.response_req = False
        self.response = None
        self.dc = False
        self.win1_active = True
        self.win2_active = False

        self.make_guis()
        self.handle_gui()

    def connect_to_server(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = (self.server_ip, self.server_port)
        try:
            self.client.connect(self.addr)
            self.client.settimeout(5)
        except:
            return -1
        try:
            self.client.send(pickle.dumps(self.name))
        except:
            return -2
        while True:
            try:
                self.response = pickle.loads(self.client.recv(BUFFER_SIZE))
            except EOFError:
                return -3
            if self.response:
                self.messages.append(self.response)
                break
            else:
                return -4

    def handle_dc(self):
        self.messages.append('You have been disconnected from the server.')
        self.window2['chatbox'].update('\n'.join(self.messages))
        self.window2.refresh()
        self.client.close()
        del self.messages[:]

    def make_guis(self):
        self.window1 = sg.Window(WINDOW_TITLE, layout=all_layouts['setup'], size=WINDOW_SIZE).finalize()
        self.window2 = sg.Window(WINDOW_TITLE, layout=all_layouts['main'], size=WINDOW_SIZE).finalize()

        if testing:
            self.window1['ip'].update('127.0.0.1')
            self.window1['port'].update('6969')

        self.window2.hide()

    def check_server_info(self):
        try:
            IPy.IP(self.values['ip'])
            self.server_ip = self.values['ip']
        except ValueError:
            return 'The given IP address is invalid'
        try:
            if 0 < int(self.values['port']) < 65525:
                self.server_port = int(self.values['port'])
        except ValueError:
            return 'The given port is invalid'
        if self.values['name'] != '' and len(self.values['name']) < MAX_NICKNAME_LEN:
            self.name = self.values['name']
        else:
            return 'The name is invalid'
        return 0

    def start_connection(self):
        try:
            conn_thread = threading.Thread(target=self.connect_to_server, args=())
            conn_thread.start()
            # TODO make loading gif stay with window if moved
            while conn_thread.is_alive():
                sg.PopupAnimated(sg.DEFAULT_BASE64_LOADING_GIF,
                                 time_between_frames=100, message='Connecting...')
            sg.PopupAnimated(None)
            if len(self.messages) > 0:
                self.server_conn = threading.Thread(target=self.maintain_connection, args=())
                self.server_conn.start()
                return 0
            else:
                return 'The server could not be reached'
        except:
            return traceback.format_exc()

    def dc_server(self):
        try:
            self.dc = True
            self.server_conn.join()
            self.handle_dc()
            return 0
        except:
            return traceback.format_exc()

    def send_msg(self):
        try:
            if self.values['input'] != '':
                self.response = self.values['input']
                self.send_message()
                return 0
            else:
                return 'Please enter a message to send.'
        except:
            return traceback.format_exc()

    def send_message(self):
        self.client.send(pickle.dumps(self.response))

    def watch_for_dc(self):
        while True:
            if self.dc:
                self.dc = False
                break
            time.sleep(1)

    def maintain_connection(self):
        watcher = threading.Thread(target=self.watch_for_dc, args=())
        watcher.start()
        while watcher.is_alive():
            try:
                try:
                    curr_msg = pickle.loads(self.client.recv(BUFFER_SIZE))
                except:
                    self.handle_dc()
                    break
                if curr_msg and curr_msg != KEEP_ALIVE_CHAR:
                    self.messages.append(curr_msg)
            except:
                traceback.print_exc()
                break

    def handle_gui(self):
        while True:
            if self.win1_active:
                self.event, self.values = self.window1.read(timeout=100)
            if self.win2_active:
                self.event, self.values = self.window2.read(timeout=100)
            if self.event == sg.WIN_CLOSED or self.event == 'Exit':
                break
            if self.win1_active:
                if self.event == 'connect' and not self.win2_active:
                    self.info_valid = self.check_server_info()
                    if self.info_valid == 0:
                        self.conn_valid = self.start_connection()
                        if self.conn_valid == 0:
                            self.win2_active = True
                            self.win1_active = False
                            self.window1.hide()
                            self.window2.UnHide()
                        else:
                            self.window1['setup_error'].update(self.conn_valid)
                    else:
                        self.window1['setup_error'].update(self.info_valid)

            if self.win2_active:
                if self.event == 'dc' or not self.server_conn.is_alive():
                    self.dc_status = self.dc_server()
                    if self.dc_status == 0:
                        self.win1_active = True
                        self.win2_active = False
                        self.window2.hide()
                        self.window1.UnHide()
                        if self.event == 'dc':
                            self.window1['setup_error'].update('You disconnected from the server')
                        elif not self.server_conn.is_alive():
                            self.window1['setup_error'].update('The server most likely crashed and you were disconnected')
                        else:
                            pass
                    else:
                        self.window2['main_error'].update(self.dc_status)
                if self.event == 'send':
                    self.send_status = self.send_msg()
                    if self.send_status == 0:
                        pass
                    else:
                        self.window2['main_error'].update(self.send_status)
                self.window2['chatbox'].update('\n'.join(self.messages))

        self.window1.close()
        self.window2.close()


if __name__ == '__main__':
    c = client()