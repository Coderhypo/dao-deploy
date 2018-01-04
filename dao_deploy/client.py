import requests
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter

from .errors import ClientError
from .config import VERSION

DEFAULT_HEADERS = {"User-Agent": "Dao-Deploy Client v{}".format(VERSION)}


class BaseClient(requests.Session):
    def __init__(self, base_url, headers: dict = None):
        super(BaseClient, self).__init__()
        self.base_url = base_url
        if not headers:
            headers = {}
        self.headers.update(DEFAULT_HEADERS)
        self.headers.update(headers)
        self.mount("http://", HTTPAdapter(max_retries=3))
        self.mount("https://", HTTPAdapter(max_retries=3))

    def url(self, path):
        return urljoin(self.base_url, path)

    @classmethod
    def result_or_raise(cls, response, json=True):
        status_code = response.status_code

        if status_code // 100 != 2:
            raise ClientError("<Status Code {}>: {}".format(status_code, response.text))
        if json:
            return response.json()
        return response.text


class SaltClient(BaseClient):
    def __init__(self, cluster, eauth="pam"):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.username = cluster.username
        self.password = cluster.password
        self.eauth = eauth
        super().__init__(cluster.cluster_url, headers)

    def _post(self, data):
        try:
            rsp = self.post(self.base_url, json=data, timeout=3)
        except requests.exceptions.RequestException:
            raise ClientError("Can't get a connection to {}"
                              .format(self.base_url))
        rsp = self.result_or_raise(rsp)
        return rsp

    def login(self):
        data = {
            "username": self.username,
            "password": self.password,
            "eauth": self.eauth,
        }
        try:
            rsp = self.post(self.url('/login'), json=data, timeout=3)
        except requests.exceptions.RequestException:
            raise ClientError("SaltStack Client Error: Can't get a connection to {}"
                              .format(self.base_url))
        if rsp.status_code // 100 != 2:
            if rsp.status_code == 401:
                raise ClientError("Username or password error")
            raise ClientError("Can't get a connection to {}"
                              .format(self.base_url))

        try:
            result = rsp.json()['return']
            if len(result) < 1:
                raise ClientError("SaltStack Client Error: Can't get salt token, check your master config.")
            token_info = result[0]
            token = token_info['token']
        except KeyError:
            raise ClientError("SaltStack Client Error: Can't get salt token, check your salt version.")
        self.headers['X-Auth-Token'] = token
        return True

    def command(self, command):
        return self._post(command)


class DCEClient(BaseClient):
    def __init__(self, rest_url, username, password, dce_version):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.username = username
        self.password = password
        self.dce_version = dce_version
        super().__init__(rest_url, headers)

    def login(self):
        pass


CLIENT_MAP = {
    "salt_stack": SaltClient,
    "dce": DCEClient,
}
