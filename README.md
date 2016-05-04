###tx_tcp_line_client

This is a line_only_client that writes to a TCP socket with the following specs (unchecked means TODO):

- [x] writes messages delimited by '\r\n' and waits for response
- [x] uses a connection pool
- [x] connection retry
- [x] times out waiting for response and closes connection
- [ ] logs timeout and message request failure exceptions
- [ ] handles OK/fail response
- [ ] retries after timeout with exponential backoff
