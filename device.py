import random
import time
import requests
from numpy import random
from requests.exceptions import HTTPError
import sys
import logging

# url server
BASE_SERVER = "http://127.0.0.1:5000/"
# time interval for sending data to the server
INTERVAL_SEND = 1
# max sample
N_MAX_SAMPLE = 40

logging.basicConfig(level=logging.INFO, filename='device' + sys.argv[1] + '_log.log')


class Device:
    def __init__(self, id_device):
        logging.debug("Start new device")
        self.id = id_device
        self.config = 0
        self.distribution = [random.exponential(size=100), random.uniform(size=100), random.chisquare(df=1, size=100),
                             random.normal(size=100)]
        # choose the distribution
        self.id_distribution = random.randint(len(self.distribution))
        # choose the number of sample
        self.n_sample = random.randint(2, N_MAX_SAMPLE)
        self.count = 0
        # extract data
        self.data = random.choice(self.distribution[self.id_distribution], self.n_sample)

    def get_config(self):
        """ get the configuration

        :return:
        """
        return self.config

    def get_data(self):
        """ the data to be sent to the server

        :return:
        """
        # seconds passed since epoch
        seconds = time.time()
        data = {'id_device': self.id, 'timestamp': seconds, 'data': self.data[self.count]}
        return data

    def send(self, send_data):
        """ sends the data to the server

        :param send_data:
        :return:
        """
        try:
            resp = requests.put(BASE_SERVER + 'data_device', json=send_data)
            resp.raise_for_status()
        except HTTPError as http_err:
            logging.warning(f'HTTP error occurred: {http_err}')
            return resp
        except Exception as err:
            logging.warning(f'Other error occurred: {err}')
            return
        else:
            if resp.status_code == 201:
                # update configuration
                self.config = resp.json()

        return resp

    @staticmethod
    def remove_data(data):
        """ asks the server to delete some data from the database

        :param data:
        :return:
        """
        try:
            resp = requests.delete(BASE_SERVER + 'data_device', json=data)

        except HTTPError as http_err:
            logging.warning(f'HTTP error occurred: {http_err}')

        except Exception as err:
            logging.warning(f'Other error occurred: {err}')

        return resp

    def run(self):
        while True:
            if self.count >= self.n_sample:
                logging.debug("change distribution")
                # we have to change the distribution
                # choose the distribution
                self.id_distribution = random.randint(len(self.distribution))
                # choose the number of sample
                self.n_sample = random.randint(2, N_MAX_SAMPLE)
                self.count = 0
                # extract data
                self.data = random.choice(self.distribution[self.id_distribution], self.n_sample)

            self.send(self.get_data())
            self.count = self.count + 1
            time.sleep(INTERVAL_SEND)


if __name__ == '__main__':
    dev = Device(int(sys.argv[1]))
    dev.run()
