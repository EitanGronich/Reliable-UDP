Packet Structure:

  + - - - - - - - - + - - - - - - - + - - - - - - - - - - - - - +
  | Component       | Length        | Details                   |
  + - - - - - - - - + - - - - - - - + - - - - - - - - - - - - - +
  | Length          | 4 octets      | Length of datagram        |
  + - - - - - - - - + - - - - - - - + - - - - - - - - - - - - - +
  | Connection ID   | 4 octets      | ID shared between sides   |
  + - - - - - - - - + - - - - - - - + - - - - - - - - - - - - - +
  | Flag            | 1 octets      | 0 - data                  |
  |                 |               | 1 - acknowledge packet
  |                 |               | 2 - close connection
  |                 |               | 4 - init connection       |
  |                 |               | 8 - keep alive packet     |
  + - - - - - - - - + - - - - - - - + - - - - - - - - - - - - - +
  | Sequence No.    | 2 octets      | Sequence number of packet |
  + - - - - - - - - + - - - - - - - + - - - - - - - - - - - - - +
  | Data            | 1024 octets   | Data                      |
  |                 | (max)         |                           |
  + - - - - - - - - + - - - - - - - + - - - - - - - - - - - - - +

Protocol:
    RUDP protocol is a reliable stream protocol over UDP.
    Initialization of connection is as follows:
        1.  Initializer of connection sends a connection packet to target endpoint.
            This connection packet includes: Flag=4, Data=address of initializer and address of desired endpoint in the following format:
            Source Address: #address\n
            Source Port: #port\n
            Destination Address: #address\n
            Destination Port: #port\n
        2.  If connection is successful: endpoint returns an ack.
            If not, returns close packet.
        Transmission of stream is as follows:
        1.  After each packet sent, the sender will wait N milliseconds for an acknowledgement.
        2.  After each packet received, the receiver will send an acknowledgement, with the same sequence number of the data acknowledged.
        3.  If no acknowledgement was received after N milliseconds, the sender of the packet
            will retry the send-wait sequence M times.
        4.  If K milliseconds of inactivity have passed (no data or acknowledgement sent),
            the inactive side will send a keep alive packet (Flag=8, no data).
        5.  If no keep alive packet was received after K milliseconds of inactivity, the connection is terminated.
