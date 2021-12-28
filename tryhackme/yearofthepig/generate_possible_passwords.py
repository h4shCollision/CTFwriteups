import string
import hashlib

username = ["Marco", "marco", "admin"]
words = ['macchi', 'Macchi', 'savoia','Savoia','curtiss', 'Curtiss']
words += ['Italy', 'italy', 'Italian', 'italian']
words += ['plane', 'Plane', 'flying', 'planes', 'Planes', 'milan', 'Milan']
numbers = '1234567890'
special = string.punctuation

f = open("potential_passwords.txt", 'w')
for i in numbers:
        for j in numbers:
                for k in special:
                        for l in words:
                                for m in username:
                                        password = l + i + j + k
                                        hashed = hashlib.md5(password.encode("ascii")).hexdigest()
                                        content = '{"username":"' + m + '","password":"' + hashed + '"}'
                                        f.write(content+ "\n")
                                #password = l + i + j + k
                                #hashed = hashlib.md5(password.encode("ascii")).hexdigest()
                                #if hashed == '[omitted]':
                                        #print(password)
                                        #print(hashed) 

f.close()
