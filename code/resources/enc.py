from cryptography.fernet import Fernet

def write(text,key):
    f = Fernet(key)
    out = f.encrypt(bytes(text))
    return out

def read(text,key):
    f = Fernet(key)
    out = f.decrypt(text)
    return out

class Crypter:
    def __init__(self,root_key=None):
        if not root_key:
            root_key = Fernet.generate_key()
        self.root_key = root_key
    def write(self,text):
        key = Fernet.generate_key()
        first_pass = write(bytes(text),key)
        second_pass = write(first_pass+";"+key,bytes(self.root_key))
        return second_pass
    def read(self,text,default):
        if not text:
            return default
        try:
            first_pass = read(bytes(text),bytes(self.root_key))
            second_pass,key2 = first_pass.rsplit(";",1)
            password2 = read(bytes(second_pass),bytes(key2))
        except:
            return default
        return password2


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
