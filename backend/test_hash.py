import bcrypt
from passlib.hash import bcrypt as passlib_bcrypt

hash_str = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36zLa27LnNLTNBi2JpFGUSe"
print("bcrypt direct:", bcrypt.checkpw(b"1234", hash_str.encode()))

try:
    print("passlib:", passlib_bcrypt.verify("1234", hash_str))
except Exception as e:
    print("passlib exception:", e)
