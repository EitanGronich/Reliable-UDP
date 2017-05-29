#!/usr/bin/python
import logging

_LOGGING_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}
_KEEP_ALIVE_INTERVAL = 20000 #milliseconds
_RETRY_INTERVAL = 1000
_CONNECTION_APPROVAL_INTERVAL = 10000
_RETRY_COUNT = 15
_LENGTH_LENGTH = 4
_CID_LENGTH = 4
_FLAG_LENGTH = 1
_SQN_LENGTH = 4
_DATA_LENGTH = 1024
_MAX_INIT_LENGTH = 43
_HTTP_PORT = 80
_RUDP_PORT = 1026
_CONTROL_PORT = 1025
_TIMEOUT = 2000
_HTTP_BUFF_LIMIT = 4096
_HTTP_BLOCK_SIZE = 1024
_CONTROL_BUFF_LIMIT = 4096
_CONTROL_BLOCK_SIZE = 1024
_FILE_BLOCK_SIZE = 1024
_DATA_BUFF_LIMIT = 4096
_DATA_BLOCK_SIZE = 1024
_MAX_RUDP_SIZE = _DATA_LENGTH + _SQN_LENGTH + _FLAG_LENGTH + _CID_LENGTH + _LENGTH_LENGTH
_MAX_CONNECTIONS = 65536
_CONTROL_OK = 0
_CONTROL_INVALID_REQUEST = 1
_CONTROL_TOO_MANY_CONNECTIONS = 2
_CONTROL_CONNECTION_NOT_EXIST = 3
_LF = '\n'
_LF_BIN = _LF.encode('utf-8')
_CRLF = '\r\n'
_CRLF_BIN = _CRLF.encode('utf-8')
_HTTP_SIGNATURE = 'HTTP/1.1'
_MAX_HEADER_LENGTH = 4096
_MAX_NUMBER_OF_HEADERS = 100
_HTTP_INTERNAL_ERROR = 500
_HTTP_FILE_NOT_FOUND = 404
_HTTP_OK_CODE = 200
_HTTP_OK_MESSAGE = "OK"
_BASE_DIRECTORY = "."
_MIN_PORT = 0
_MAX_PORT = 65536
_CONTENT_TYPES = {
    '.css': 'text/css',
    '.html': 'text/html',
    '.txt': 'text/plain',
    '.ico': 'image/x-icon',
}
_STD_IN = 0
_STD_OUT = 1
_STD_ERR = 2
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
