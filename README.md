# otp-proxy

Currently works. Uses a hardcoded seed phrase to generate an OTP process that dynamically changes the proxy's port number. Any existing connection 
remains open when the code rolls, but all following connections must use a new port. 

TO DO
~~- Add qr code generator to dump OTP qr code to current dir~~
- Log to file in a standardized format rather than stdout
