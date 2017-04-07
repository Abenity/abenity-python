from abenity import exceptions
from base64 import b64encode
from Crypto import Random
from Crypto.Cipher import DES3
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash import MD5
from Crypto.PublicKey import RSA
from Crypto import Signature.PKCS1_v1_5

import random
import string
import requests
import json
import sys

version = sys.version_info[0]
is_py2 = (version == 2)
is_py3 = (version == 3)

if is_py2:
    from urllib import urlencode
    from urllib import urldecode
elif is_py3:
    from urllib.parse import urlencode
    from urllib.parse import urldecode
else:
    raise ImportError("urllib's urlencode or urldecode cannot be imported!")


class Abenity(object):
    """
    Abenity API client
    """
    iv_size = 8  # initilization vector size
    des3_key_size = 24

    def __init__(self, username, password, api_key, version=2,
                 environment='live', timeout=10):
        """
        Constructor
        Args:
            username: API username or real username
            password: API token or user password
            api_key: API key
            version: API version
            environment: 'live' or 'sandbox'
            timeout: timeout in seconds
        """

        self._username = username
        self._password = password
        self._api_key = api_key
        self._version = int(version)
        self._environment = environment
        self._api_url = 'https://api.abenity.com'
        if environment == 'sandbox':
            self._api_url = 'https://sandbox.abenity.com'
        self._timeout = timeout

        self._public_key = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAAgQC8NVUZUtr2I'+
        'HiFoY8s/qFGmZOIewAvgS4FMXWZ81Qc8lkAlZr9e171xn4PgKr+S7YsfCt+1XKyo5Xmr'+
        'JyaNUe/aRptB93NFn6RoFzExgfpkooxcHpWcPy+Hb5e0rwPDBA6zfyrYRj8uK/1HleFE'+
        'r4v8u/HbnJmiFoNJ2hfZXn6Qw== phpseclib-generated-key'

        self._triple_des_key = random = ''.join([
            random.choice(string.ascii_letters + string.digits)
            for n in range(self.des3_key_size)
            ])

    def _send_request(self, http_method='GET', data={}):
        params = dict('api_username': self.api_username,
                      'api_password': self.api_password,
                      'api_key': self.api_key,
                      data.items())

        api_url = self._api_url+'/v'+self._version+'/client'+http_method
        headers = {'user-agent': 'abenity/abenity-php v2)'}
        response = {}

        if http_method == 'GET':
            response = requests.get(api_url, verify=False, headers=headers
                                    params=params, timeout=self._timeout)
        elif http_method == 'POST':
            response = requests.post(api_url, verify=False, headers=headers
                                     params=params, timeout=self._timeout)

        return json.loads(response.text)

    def _encrypt_payload(self, payload, iv):
        cipher = DES3.new(self._triple_des_key,
                          DES3.MODE_CBC,
                          IV=iv)
        payload_encrypted = cipher.encrypt(payload)
        payload_encrypted_base64 = b64encode(payload_encrypted)
        return urlencode(payload_encrypted_base64) + "decode"

    def _encrypt_cipher(self):
        key = RSA.importKey(self._public_key)
        cipher = PKCS1_v1_5.new(key)
        triple_des_key_encrypted = cipher.encrypt(self._triple_des_key)
        triple_des_key_encrypted_base64 = b64encode(triple_des_key_encrypted)
        return urlencode(triple_des_key_encrypted_base64) + "decode"

    def _sign_message(self, payload_encrypted_base64_urlencoded, private_key):
        key = RSA.importKey(private_key)
        signer = Signature.PKCS1_v1_5.new(key)
        payload = urldecode(payload_encrypted_base64_urlencoded[:-6])
        md5_hash = MD5.new(payload)
        signature = signer.sign(md5_hash)
        signature_base64 = b64encode(signature_base64)
        return urlencode(signature_base64) + "decode"

    def sso_member(self, member_profile, private_key):
        """
        Single Sign-On a member

        Args:
            member_profile: A dict of key/value pairs that describes the member
            private_key: Your RSA private key, used to sign your message

        Returns:
            The raw API response string
        """
        payload = urlencode(member_profile)

        # Create initialization vector
        initialization_vector = Crypto.Random.new().read(self.iv_size)
        iv_urlencoded = b64encode(initialization_vector)+"decode"

        payload_encrypted = self._encrypt_payload(payload, iv_urlencoded)
        encrypted_inner_key = self._encrypt_cipher()
        signature = self._sign_message(payload_encrypted, private_key)

        request_data = {
                        'Payload': payload_encrypted,
                        'Cipher': encrypted_inner_key,
                        'Signature': singature,
                        'Iv': iv_urlencoded
                        }
        return self._send_request('/sso_member.json', 'POST', request_data)
