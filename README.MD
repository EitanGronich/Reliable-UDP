# Reliable UDP

A final project for the Gvahim program. This project implements a reliable stream above UDP,
called RUDP or Reliable UDP. The goal of this protocol is to allow a flexible and easily
adapted replacement in unreliable mediums in which TCP is inefficient.
The program architecture is based on proxying with RUDP, between end users, who communicate in TCP.
Each instance of the program is an asynchronous RUDP server, that includes:
a. A UDP socket for RUDP communication with other RUDP servers
b. TCP sockets for data communication with the end users.
c. TCP sockets for communication with the end users via control channel,
 which allows request of statistics and requests to initialize connections.
d. TCP sockets for HTTP serving of a web page in which the user can
see statistics and request to initialize connections.

The program works in the following way:
1. User A connects to RUDP Server A via control channel/web page, and asks to initialize 
a connection, specifying the destination he wishes to communicate with (User B) and the additional RUDP Server
he wished to pass through (RUDP Server B).
2. Server A sends User A a port number.
3. User A connects to this port and the connection is initialized.
4. Packets User A sends will be sent to Server A in TCP, then to Server B in RUDP, and finally
to User B in TCP.
5. And vice versa.


## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

In order to run the project there are some requirments:
```
1) Download and install Cygwin: https://cygwin.com/install.html
2) In configurations of Cygwin install choose to install git and python 2.7
3) Enter the tmp file of cygwin: cd /tmp
4) Clone repository into tmp file: git clone https://github.com/EitanGronich/Reliable-UDP
```

### Execution

To execute the project open Command Prompt (or Terminal on Linux):
Reach the parent folder of this project:
```
cd [location of Reliable-UDP]
```
Running Server 1:
```
python -m Reliable-UDP.Server (default: --rudp-port 1026 --control-port 1025 --http-port 80)
```

Running Server 2 (on different ports because both are on localhost):
```
python -m Reliable-UDP.Server --rudp-port X --control-port Y --http-port Z
```

Now you can use the servers as drop-in replacement for TCP as described above.


### Arguments

All other arguments are optional. to see all arguments enter -h/--help.

### Graphical Interface

There is no graphical interface as part of the main program.
In order too enter the GUI in your prefered browser
type:
```
[your_ip]/home.html
```
This will open the home page from which other options are available.



## Authors

* **Eitan Gronich** - *Initial work* - [My Profile] (https://github.com/EitanGronich)

See also the list of [contributors](https://github.com/Liron-Berger/Onion-Routing/graphs/contributors) who participated in this project.


## Acknowledgments

* Thanks to Alon and Sarit for all their support and great teaching!