#!/usr/bin/python

## @package Reliable-UDP.Common.constants
## @file constants.py Implementation of @ref Reliable-UDP.Common.constants

import logging

##Map of logging level names to numerical values
_LOGGING_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}
##Keep alive interval, after this time of idle connection
# a keep-alive will be sent
_KEEP_ALIVE_INTERVAL = 20000 #milliseconds
##Retry interval or RTO, after this time packets that have not been
#acked will be retransmitted
_RETRY_INTERVAL = 1000
##Connection approval interval, time that initiator of connection
#will wait for connection approval before giving up and closing connection.
_CONNECTION_APPROVAL_INTERVAL = 10000
##Maximum amount of retries before giving up and closing connection.
_RETRY_COUNT = 15
##Length in bytes of length component of RUDP packet.
_LENGTH_LENGTH = 4
##Length in bytes of CID component of RUDP packet.
_CID_LENGTH = 4
##Length in bytes of flag component of RUDP packet.
_FLAG_LENGTH = 1
##Length in bytes of sequence number component of RUDP packet.
_SQN_LENGTH = 4
##Max length in bytes of data component of RUDP packet.
_DATA_LENGTH = 1024
##Max length of RUDP packet, calculated by other values.
_MAX_RUDP_SIZE = _DATA_LENGTH + _SQN_LENGTH + _FLAG_LENGTH + _CID_LENGTH + _LENGTH_LENGTH
##Default HTTP port for listening to HTTP Connections
_HTTP_PORT = 80
##Default RUDP Port for the UDP socket
_RUDP_PORT = 1026
##Default Control Port for the listening to control connections
_CONTROL_PORT = 1025
##Default timeout of poller
_TIMEOUT = 2000
##Receive buff limit of HTTP socket objects
_HTTP_BUFF_LIMIT = 4096
##Reading block size of HTTP socket objects
_HTTP_BLOCK_SIZE = 1024
##Receive buff limit of Control socket objects
_CONTROL_BUFF_LIMIT = 4096
##Reading block size of Control socket objects
_CONTROL_BLOCK_SIZE = 1024
##Reading block size of files
_FILE_BLOCK_SIZE = 1024
##Receive buff limit of Data socket objects
_DATA_BUFF_LIMIT = 4096
##Reading block size of Data socket objects
_DATA_BLOCK_SIZE = 1024
##Max number of connections per two servers, calculated by CID length
_MAX_CONNECTIONS = 16 ** (_CID_LENGTH)
##Control code in reponse for success
_CONTROL_OK = 0
##Control code in reponse for invalid request
_CONTROL_INVALID_REQUEST = 1
##Control code in response for connection does not exist
#when statistics are requested for a nonexistent connection
_CONTROL_CONNECTION_NOT_EXIST = 2
##Line feed
_LF = '\n'
##Line feed encoded in 'utf-8'
_LF_BIN = _LF.encode('utf-8')
##Carriage return and line feed
_CRLF = '\r\n'
##Carriage return and line feed, encoded in 'utf-8'
_CRLF_BIN = _CRLF.encode('utf-8')
##HTTP Protocol signature
_HTTP_SIGNATURE = 'HTTP/1.1'
##Max header length in HTTP
_MAX_HEADER_LENGTH = 4096
##Max number of headers in HTTP
_MAX_NUMBER_OF_HEADERS = 100
##HTTP Internal Error code
_HTTP_INTERNAL_ERROR = 500
##HTTP File not found code
_HTTP_FILE_NOT_FOUND = 404
##HTTP "Request is OK" code
_HTTP_OK_CODE = 200
##HTTP "Request is OK" Message
_HTTP_OK_MESSAGE = "OK"
##Base directory for files
_BASE_DIRECTORY = "."
##Minimum Port possible in TCP
_MIN_PORT = 0
##Maximum Port possible in TCP
_MAX_PORT = 65536
##Supported content types of the HTTP server
#Maps file extensionts to Content-Types
_CONTENT_TYPES = {
    '.css': 'text/css',
    '.html': 'text/html',
    '.txt': 'text/plain',
    '.ico': 'image/x-icon',
}
##POSIX standard input
_STD_IN = 0
##POSIX standard output
_STD_OUT = 1
##POSIX standard error
_STD_ERR = 2
##HTML code of form page with placeholder for port number
_FORM_HTML = """
<html>
    <head>
        <link rel="stylesheet" type="text/css" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
        <link rel="stylesheet" type="text/css" href="style.css">
    </head>
    <body>
        <div class="container">
            <nav class="navbar navbar-default">
                <div class="container-fluid">
                    <div class="navbar-header">
                      <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1" aria-expanded="false">
                        <span class="sr-only">Toggle navigation</span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                        <span class="icon-bar"></span>
                      </button>
                  </div>

                <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
                  <ul class="nav navbar-nav">
                    <li><a href="/home.html">Home</a></li>
                    <li><a href="/connections">Connection Data</a></li>
                    <li class="active"><a href="/open_port.html">Open A Port</a></li>
                  </ul>
                </div>
              </div>
            </nav>
            <h1>Open A Listening Port</h1>
            <p class="open-port-paragraph">Request the RUDP Server to open a listening port. Connecting to the given port will result in the server connecting to the desired destination through the desired RUDP Server.</p>
              $port$
              <form action="return_port">
                <div class="form-group">
                  <label for="InputExitAddress">IP Address of Exit Server</label>
                  <p class="form-description">This is the IP address of the other RUDP server you want your connection to pass through.</p>
                  <input type="text" class="form-control" id="InputExitAddress" placeholder= "Exit address" name="exit_address">
                </div>
                <div class="form-group">
                  <label for="InputExitPort">RUDP Port of Exit Server</label>
                  <p class="form-description">This is the RUDP port of that RUDP server.</p>
                  <input type="text" class="form-control" id="InputExitPort" placeholder= "Exit port" name="exit_port">
                </div>
                <div class="form-group">
                  <label for="InputDestAddress">IP Address of Destination</label>
                  <p class="form-description">This is the IP address of your final destination.</p>
                  <input type="text" class="form-control" id="InputDestAddress" placeholder= "Destination address" name="dest_address">
                </div>
                <div class="form-group">
                  <label for="InputDestPort">TCP Port of Destination</label>
                  <p class="form-description">This is the TCP port of your destination.</p>
                  <input type="text" class="form-control" id="InputDestAPort" placeholder= "Destination port" name="dest_port">
                </div>
                <div class="form-group">
                  <label for="InputTTL">Time to Live of Port</label>
                  <p class="form-description">This is how long the listening port you get will stay open. If you don't care, just type 0 - it will stay open indefinitely.</p>
                  <input type="text" class="form-control" id="InputTTL" placeholder="Time to live" name="ttl">
                </div>
                <button type = "submit" class="btn btn-info" value="submit">Submit</button>
              </form>
        </div>
    </body>
</html>
"""
##HTML code of connections page with placeholder for table data
_CONNECTIONS_HTML = """
<html>
      <head>
          <link rel="stylesheet" type="text/css" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css">
          <link rel="stylesheet" type="text/css" href="style.css">
      </head>
      <body>
          <div class="container">
              <nav class="navbar navbar-default">
                  <div class="container-fluid">
                      <div class="navbar-header">
                        <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1" aria-expanded="false">
                          <span class="sr-only">Toggle navigation</span>
                          <span class="icon-bar"></span>
                          <span class="icon-bar"></span>
                          <span class="icon-bar"></span>
                        </button>
                    </div>

                  <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
                    <ul class="nav navbar-nav">
                      <li><a href="/home.html">Home</a></li>
                      <li class="active"><a href="/connections">Connection Data</a></li>
                      <li><a href="/open_port.html">Open A Port</a></li>
                    </ul>
                  </div>
                </div>
              </nav>
              <h1>Connection Data</h1>
              <a href="/connections" class="glyphicon glyphicon-refresh refresh-button"></a>
              <table class="table table-striped table-bordered table-hover table-connections">
                  <thead>
                      <tr>
                          <th class="connection-table-heading">
                            Exit Address, CID<br>
                            <span class='table-field-description'>IP address and RUDP Port of peer server, and connection ID between the two servers</span>
                          </th>
                          <th class="connection-table-heading">
                            Connected User<br>
                            <span class='table-field-description'>IP address and TCP Port of the user connected directly to this server</span>
                          </th>
                          <th class="connection-table-heading">
                            Remote User<br>
                            <span class='table-field-description'>IP address and TCP Port of the user connected to the peer server</span>
                          </th>
                          <th class="connection-table-heading">
                            Bytes Sent<br>
                            <span class='table-field-description'>Raw data sent in connection in RUDP protocol</span>
                          </th>
                          <th class="connection-table-heading">
                            Bytes Received<br>
                            <span class='table-field-description'>Raw data received in connection in RUDP protocol</span>
                          </th>
                          <th class="connection-table-heading">
                            Sequence Number<br>
                            <span class='table-field-description'>Current sequence number of packets sent in this connection by this server</span>
                          </th>
                          <th class="connection-table-heading">
                            Peer Sequence Number<br>
                            <span class='table-field-description'>Current sequence number of packets received in this connection from peer server</span>
                          </th>
                      </tr>
                  </thead>
                  <tbody>
                      $data$
                  </tbody>
              </table>
          </div>
      </body>
  </html>
"""
