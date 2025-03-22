# Include the libraries for socket and system calls
import socket
import sys
import os
import argparse
import re

# 1MB buffer size
BUFFER_SIZE = 1000000

# Get the IP address and Port number to use for this web proxy server
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = int(args.port)

# Create a server socket, bind it to a port and start listening
try:
  # Create a server socket
  # ~~~~ INSERT CODE ~~~~
  serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # Correctly create socket object
  # ~~~~ END CODE INSERT ~~~~
  print ('Created socket')
except:
  print ('Failed to create socket')
  sys.exit()

try:
  # Bind the server socket to a host and port
  # ~~~~ INSERT CODE ~~~~
  # Update 1: the input of bing should be a tuple
  serverSocket.bind((proxyHost, proxyPort))
  # Bind requires a tuple (host, port)
  # ~~~~ END CODE INSERT ~~~~
  print ('Port is bound')
except:
  print('Port is already in use')
  sys.exit()

try:
  # Listen on the server socket
  # ~~~~ INSERT CODE ~~~~
  # Update 2:allow 5 connections queing
  serverSocket.listen(5)
  # Listen with a queue of up to 5 connections
  # ~~~~ END CODE INSERT ~~~~
  print ('Listening to socket')
except:
  print ('Failed to listen')
  sys.exit()

# Continuously accept connections
while True:
  print ('Waiting for connection...')
  clientSocket = None

  # Accept connection from client and store in the clientSocket
  try:
    # ~~~~ INSERT CODE ~~~~
    clientSocket, addr = serverSocket.accept()
    # Accept incoming client connection
    # ~~~~ END CODE INSERT ~~~~
    print ('Received a connection')
  except:
    print ('Failed to accept connection')
    sys.exit()

  # Get HTTP request from client and store it in the variable: message_bytes
  # ~~~~ INSERT CODE ~~~~
  message_bytes = clientSocket.recv(BUFFER_SIZE)
  # Receive request from client
  # ~~~~ END CODE INSERT ~~~~
  message = message_bytes.decode('utf-8')
  print ('Received request:')
  print ('< ' + message)

  # Extract the method, URI and version of the HTTP client request 
  requestParts = message.split()
  method = requestParts[0]
  URI = requestParts[1]
  version = requestParts[2]

  print ('Method:\t\t' + method)
  print ('URI:\t\t' + URI)
  print ('Version:\t' + version)
  print ('')

  # Get the requested resource from URI
  URI = re.sub('^(/?)http(s?)://', '', URI, count=1)
  URI = URI.replace('/..', '')

  resourceParts = URI.split('/', 1)
  hostname = resourceParts[0]
  resource = '/'

  if len(resourceParts) == 2:
    resource = resource + resourceParts[1]

  print ('Requested Resource:\t' + resource)

  # Check if resource is in cache
  try:
    cacheLocation = './' + hostname + resource
    if cacheLocation.endswith('/'):
        cacheLocation = cacheLocation + 'default'

    print ('Cache location:\t\t' + cacheLocation)

    fileExists = os.path.isfile(cacheLocation)
    cacheFile = open(cacheLocation, "rb")  # open in binary mode
    cacheData = cacheFile.read()

    print ('Cache hit! Loading from cache file: ' + cacheLocation)
    # ProxyServer finds a cache hit, send back response to client
    # ~~~~ INSERT CODE ~~~~
     # Update 3:use sendall() to send binary data
    clientSocket.sendall(cacheData)  # Use sendall to send binary data
    # ~~~~ END CODE INSERT ~~~~
    cacheFile.close()
    print ('Sent to the client:')
    print ('> ' + cacheData.decode('utf-8'))
  except:
    originServerSocket = None
    # Create a socket to connect to origin server
    # ~~~~ INSERT CODE ~~~~
    originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Create socket object correctly
    # ~~~~ END CODE INSERT ~~~~

    print ('Connecting to:\t\t' + hostname + '\n')
    try:
      address = socket.gethostbyname(hostname)
      # Connect to the origin server
      # ~~~~ INSERT CODE ~~~~
      originServerSocket.connect((address, 80))
      # Connect to origin server on port 80
      # ~~~~ END CODE INSERT ~~~~
      print ('Connected to origin Server')

      originServerRequest = ''
      originServerRequestHeader = ''
      # Create origin server request line and headers
      # ~~~~ INSERT CODE ~~~~
      originServerRequest = f'{method} {resource} {version}'
      originServerRequestHeader = f'Host: {hostname}\r\nConnection: close\r\n'
      # Build HTTP request for origin server
      # ~~~~ END CODE INSERT ~~~~

      request = originServerRequest + '\r\n' + originServerRequestHeader + '\r\n\r\n'
      originServerSocket.sendall(request.encode())

      print ('Forwarding request to origin server:')
      for line in request.split('\r\n'):
        print ('> ' + line)

      try:
        originServerSocket.sendall(request.encode())
      except socket.error:
        print ('Forward request to origin failed')
        sys.exit()

      print('Request sent to origin server\n')

      # Get the response from the origin server
      # ~~~~ INSERT CODE ~~~~
      response = b''
      while True:
        data = originServerSocket.recv(BUFFER_SIZE)
        if not data:
          break
        response += data
      # Properly receive all data from origin server
      # ~~~~ END CODE INSERT ~~~~

      # Send the response to the client
      # ~~~~ INSERT CODE ~~~~
      #Update 4: use sendall() to send respond
      clientSocket.sendall(response)
      # Use sendall to ensure complete data transfer
      # ~~~~ END CODE INSERT ~~~~

      cacheDir, file = os.path.split(cacheLocation)
      if not os.path.exists(cacheDir):
        os.makedirs(cacheDir)
      cacheFile = open(cacheLocation, 'wb')
      # Save origin server response in the cache file
      # ~~~~ INSERT CODE ~~~~
      cacheFile.write(response)
      # Save response data to cache
      # ~~~~ END CODE INSERT ~~~~
      cacheFile.close()

      originServerSocket.close()
      clientSocket.shutdown(socket.SHUT_WR)
    except OSError as err:
      print ('origin server request failed. ' + err.strerror)

  try:
    clientSocket.close()
  except:
    print ('Failed to close client socket')
