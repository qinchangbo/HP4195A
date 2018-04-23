import sys
import os
import telnetlib
import time
import multiprocessing
import logging
import numpy as np
import numpy.core._methods
import numpy.lib.format


class hp4195a(multiprocessing.Process):
    def __init__(self, command_queue, message_queue, data_queue, logging_queue):
        super(hp4195a, self).__init__()
        self.command_queue = command_queue
        self.message_queue = message_queue
        self.data_queue = data_queue
        self.logging_queue = logging_queue
        self.host = 'bi-gpib-01.dyndns.cern.ch'
        self.port = '1234'
        self.gpib_addr = 11
        self.id = 'Prologix GPIB-ETHERNET Controller version 01.06.06.00'
        #self.root_logger = logging.getLogger()
        #self.qh= logging.handlers.QueueHandler(self.logging_queue)
        #self.root_logger.addHandler(self.qh)
        #self.logger = logging.getLogger(__name__)

    def run(self):
        '''
        This function will run when the class is launched as a separate
        process.
        '''

        while True:
            command = self.command_queue.get()
            #logging.info('Received {}'.format(command), 'from GUI')
            #logging.info('Command queue size = ', self.command_queue.qsize())

            if command == 'connect':
                #logging.info('Connecting...')
                self.telnet_connect()

            elif command == 'disconnect':
                self.telnet_disconnect()

            elif command == 'start_acquisition':
                #logging.info('Starting acquisition')
                if self.acquire_mag_data():
                    if self.acquire_freq_data():
                        self.message_queue.put(True)
                    else:
                        self.message_queue.put(False)
                else:
                    self.message_queue.put(False)
    def telnet_connect(self):
        self.tn = telnetlib.Telnet(self.host, self.port)
        if self.send_query('++ver') == self.id:
            self.init_device()
        else:
            self.tn.close()
            logging.warning('Error connecting to HP4195A.')
            self.message_queue.put(False)

    def telnet_disconnect(self):
        print('disconnecting')
        self.tn.close()
        self.message_queue.put(True)

    def init_device(self):
        self.send_command('++auto 1')
        #logging.info('Initialising HP4195A')
        self.message_queue.put(True)

    # def disconnect(self):

    def acquire_mag_data(self):
        raw_mag_data = self.send_query('A?')
        mag_data = np.fromstring(raw_mag_data, dtype=float, sep=',')
        if len(mag_data) > 0:
            self.data_queue.put(mag_data)
            return True

        #logging.info('Data queue size = ', self.data_queue.qsize())

    def acquire_freq_data(self):
        raw_freq_data = self.send_query('X?')
        freq_data = np.fromstring(raw_freq_data, dtype=float, sep=',')
        if len(freq_data) > 0:
            self.data_queue.put(freq_data)
            return True
        #logging.info('Data queue size = ', self.data_queue.qsize())

    def send_command(self, command):
        cmd = command + '\r\n'
        #logging.info('Sent', cmd.rstrip())
        self.tn.write(cmd.encode('ascii'))

    def send_query(self, command):
        cmd = command + '\r\n'
        #logging.info('Sent', cmd.rstrip())
        self.tn.write(cmd.encode('ascii'))
        raw_data = self.tn.read_until(b'\r\n').decode('ascii')
        #logging.info('Received', len(raw_data), 'of', type(raw_data))
        # remove trailing newline and carriage return
        return raw_data.rstrip()
