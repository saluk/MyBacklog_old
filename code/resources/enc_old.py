from Crypto.Cipher import AES
import base64
import os
from Crypto import Random
iv = Random.new().read(AES.block_size)

def generate_key():
    return base64.urlsafe_b64encode(os.urandom(32))

def write(text,key):
    f = AES.new(base64.urlsafe_b64decode(key), AES.MODE_CFB,iv)
    while len(text)//16 != len(text)/16:
        text += b' '
    out = f.encrypt(bytes(text))
    out = base64.urlsafe_b64encode(iv+out)
    return out

def read(text,key):
    print(key)
    print(base64.urlsafe_b64decode(key))
    text = base64.urlsafe_b64decode(text)
    iv2,text = text[:16],text[16:]
    f = AES.new(base64.urlsafe_b64decode(key), AES.MODE_CFB,iv2)
    out = f.decrypt(text)
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
    def read(self,text,default):
        if not text:
            return default
        try:
            first_pass = read(bytes(text,"utf8"),self.root_key)
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
    test(sys.argv[1])
