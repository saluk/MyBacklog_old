"""
>>> import os
>>> from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
>>> from cryptography.hazmat.backends import default_backend
>>> backend = default_backend()
>>> key = os.urandom(32)
>>> iv = os.urandom(16)
>>> cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
>>> encryptor = cipher.encryptor()
>>> ct = encryptor.update(b"a secret message") + encryptor.finalize()
>>> decryptor = cipher.decryptor()
>>> decryptor.update(ct) + decryptor.finalize()"""

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend

backend = default_backend()

import base64
import os

iv = os.urandom(16)

def generate_key():
    return base64.urlsafe_b64encode(os.urandom(32))

def write(text,key):
    cipher = Cipher(algorithms.AES(base64.urlsafe_b64decode(key)), modes.CFB(iv),backend=backend)
    encryptor = cipher.encryptor()
    while len(text)//16 != len(text)/16:
        text += b' '
    ct = encryptor.update(bytes(text))+encryptor.finalize()
    out = base64.urlsafe_b64encode(iv+ct)
    return out

def read(text,key):
    print(key)
    print(base64.urlsafe_b64decode(key))
    text = base64.urlsafe_b64decode(text)
    iv2,text = text[:16],text[16:]
    cipher = Cipher(algorithms.AES(base64.urlsafe_b64decode(key)), modes.CFB(iv2),backend=backend)
    decryptor = cipher.decryptor()
    #f = AES.new(base64.urlsafe_b64decode(key), AES.MODE_CFB,iv2)
    out = decryptor.update(text) + decryptor.finalize()
    return out

class Crypter:
    def __init__(self,root_key=None):
        if not root_key:
            root_key = generate_key()
        self.root_key = root_key
    def write(self,text):
        key = generate_key()
        first_pass = write(bytes(text,"utf8"),key)
        print("root_key",self.root_key)
        second_pass = write(first_pass+b";"+key,self.root_key)
        return second_pass
    def read(self,text,default=""):
        if not text:
            return default
        try:
            b = bytes(text,"utf8")
            first_pass = read(b,self.root_key)
            print("f:",first_pass)
            second_pass,key2 = first_pass.rsplit(b";",1)
            print("s:",second_pass)
            print("k:",key2)
            password2 = read(second_pass,key2)
        except:
            raise
            return default
        return str(password2,"utf8")


def test(password="MyPassword"):
    root_pass = Fernet.generate_key()
    c = Crypter(root_pass)
    
    print("input password:",password)
    exp = c.write(password)
    print("exported password:",exp)

    password2 = c.read(exp)
    print("re_imported password:",password2)

if __name__=="__main__":
    import sys
    test("This is some secret text")
    test(sys.argv[1])
