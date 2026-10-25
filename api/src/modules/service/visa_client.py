from modules.repository.queries.common import CommonQueries
from hashlib import sha256
import calendar
import json
from modules.utils.misc import date_time_now_utc, _get_x_correlation_id
import sys
import hmac
import requests

"""
@author: visa
"""


class VisaAPIClient(CommonQueries):
    def _get_x_pay_session(
        self,
        shared_secret,
        resource_path,
        query_string,
        body,
    ):
        return XSession(shared_secret, resource_path, query_string, body)

    def _get_mutual_auth_session(
        self, user_name: str, password: str, cert: str, key: str
    ):
        return MSession(user_name, password, cert, key)

    """
       Correlation Id ( x-correlation-id ) is an optional header.
       You can skip passing the header while calling the API's.
    """

    def _logging_helper(self, url, response, test_info, body):
        self.logger.info(test_info)
        self.logger.info(url)
        if body != "":
            self.logger.info(json.dumps(body, indent=4, sort_keys=True))
        self.logger.info("Response Code : " + str(response.status_code))
        self.logger.info("Response Headers : ")
        for header in response.headers:
            self.logger.info(header + ":" + response.headers[header])
        self.logger.info("Response Body : ")
        if response.text != "":
            self.logger.info(
                json.dumps(json.loads(response.text), indent=4, sort_keys=True)
            )

    def do_mutual_auth_request(
        self, path, body, test_info, method_type, input_headers={}
    ):
        user_name = self.cf.visa_params["userId"]
        password = self.cf.visa_params["password"]
        cert = self.cf.visa_params["cert"]
        key = self.cf.visa_params["key"]
        end_point = self.cf.visa_params["visaUrl"]
        url = end_point + path
        response = {}
        self.session = self._get_mutual_auth_session(
            user_name,
            password,
            cert,
            key,
        )
        if input_headers:
            for key in input_headers.keys():
                self.session.headers[key] = input_headers[key]
        if method_type == "post" or method_type == "put":
            self.session.headers.update(
                {
                    "content-type": "application/json",
                    "accept": "application/json",
                    "x-correlation-id": _get_x_correlation_id(),
                }
            )
            if method_type == "post":
                response = self.session.post(url, json=body, timeout=10)
            if method_type == "put":
                response = self.session.put(url, json=body, timeout=10)
            self._logging_helper(url, response, test_info, body)
        elif method_type == "get":
            self.session.headers.update(
                {
                    "accept": "application/json",
                    "x-correlation-id": _get_x_correlation_id(),
                }
            )
            response = self.session.get(url, timeout=10)
            self._logging_helper(url, response, test_info, "")
        return response

    def do_x_pay_request(
        self,
        base_uri,
        resource_path,
        query_string,
        body,
        test_info,
        method_type,
        input_headers={},
    ):
        shared_secret = self.cf.visa_params["sharedSecret"]
        end_point = self.cf.visa_params["visaUrl"]
        url = end_point + base_uri + resource_path + "?" + query_string
        self.logger.info(url)
        response = {}
        if method_type == "get":
            self.session = self._get_x_pay_session(
                shared_secret, resource_path, query_string, ""
            )
        else:
            self.session = self._get_x_pay_session(
                shared_secret, resource_path, query_string, json.dumps(body)
            )
        if input_headers:
            self.logger.info(input_headers)
            for key in input_headers.keys():
                self.session.headers[key] = input_headers[key]
        if method_type == "post" or method_type == "put":
            self.session.headers.update(
                {
                    "content-type": "application/json",
                    "accept": "application/json",
                    "x-pay-token": self.session.x_pay_token,
                    "x-correlation-id": _get_x_correlation_id(),
                }
            )
            if method_type == "post":
                response = self.session.post(url, json=body, timeout=10)
            if method_type == "put":
                response = self.session.put(url, json=body, timeout=10)
            self._logging_helper(url, response, test_info, body)
        elif method_type == "get":
            self.session.headers.update(
                {
                    "x-pay-token": self.session.x_pay_token,
                    "x-correlation-id": _get_x_correlation_id(),
                }
            )
            response = self.session.get(url, timeout=10)
            self._logging_helper(url, response, test_info, "")
        return response


class XSession(requests.Session):
    """Requests Session for xpaytoken apis
    Construct as XSession(apikey, shared_secret), usage same as
    requests.Session
    """

    def _get_timestamp(self) -> str:
        d = date_time_now_utc()
        timestamp = calendar.timegm(d.timetuple())
        return str(timestamp)

    def _get_x_pay_token(self, shared_secret, resource_path, query_string, body):
        timestamp = self._get_timestamp()
        pre_hash_string = timestamp + resource_path + query_string + body
        if sys.version_info < (3, 0):
            hash_string = hmac.new(
                shared_secret, msg=pre_hash_string.rstrip(), digestmod=sha256
            ).hexdigest()
        else:
            hash_string = hmac.new(
                str.encode(shared_secret),
                msg=pre_hash_string.rstrip().encode("utf-8"),
                digestmod=sha256,
            ).hexdigest()
        return "xv2:" + timestamp + ":" + hash_string

    def __init__(self, shared_secret, resource_path, query_string, body):
        super(XSession, self).__init__()
        self.x_pay_token = self._get_x_pay_token(
            shared_secret, resource_path, query_string, body
        )


class MSession(requests.Session):
    """Requests Session for mutualauth(2-way SSL) apis
    username, password: App credentials
    cert: path to app's client certificate
    key: path to app's private key
    """

    def __init__(self, username, password, cert, key):
        super(MSession, self).__init__()
        self.cert = (cert, key)
        self.auth = (username, password)
