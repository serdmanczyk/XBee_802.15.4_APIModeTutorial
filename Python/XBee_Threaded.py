import serial
import threading 
import queue
from time import sleep

class XBee(threading.Thread):
   rxbuff = bytearray()
   RxQ = queue.Queue()
   stop = threading.Event()
   rx = True

   def __init__(self, serialport):
      threading.Thread.__init__(self)
      # self.serial = serial.Serial(port=serialport, baudrate=9600, timeout=0)
      self.start()

   def shutdown(self):
      self.stop.set()
      self.join()

   def run(self):
      print("run")
      while not self.stop.is_set():
         self.Rx()
         sleep(0.125)

   def Receive(self, wait=5):
      """
      Checks receive queue for messages

      Inputs:
         wait(optional): Desired number of seconds to wait for a message
      Output:
         Message, if received.  None if timed out.
      """
      try:
         return self.RxQ.get(timeout=wait)
      except queue.Empty:
         return None
         
   def Rx(self):
      """
      Checks serial for an incoming message.  If a message is received, 
         calles Parse() to verify it is a properly formatted XBee API message.
      """

      # if self.serial.inWaiting():
      #    remaining = self.serial.inWaiting()
      #    while remaining > 0:
      #       chunk = self.serial.read(remaining)
      #       remaining -= len(chunk)
      #       self.rxbuff.extend(chunk)

      if self.rx:
         self.rxbuff = bytearray.fromhex(\
            "7e 00 10 81 ff ff 4c 00 48 65 6c 6c 6f 20 57 6f 72 6c 64 18 \
            7e 00 16 81 ff ff 98 00 4d 79 20 4e 61 6d 65 20 69 73 20 4a 6f 68 6e 6e 79 ef \
            00 00 7e 00 10 81 ff ff 4d 00 48 6f 77 20 41 72 65 20 59 6f 75 70 7E 00 00")
         self.rx = False
      
         msgs = self.rxbuff.split(bytes(b'\x7E'))
         for msg in msgs[:-1]:
            self.Validate(msg)

         if self.Validate(msgs[-1]):
            self.rxbuff = bytearray()
         else:
            self.rxbuff = msgs[-1]

   def SendStr(self, msg, addr=0xFFFF, options=0x01, frameid=0x00):
      """
      Inputs:
         msg: A message, in string format, to be sent to an XBee
         addr: The 16 bit address of the destination XBee (default: 0xFFFF broadcast)
         options: Optional byte to specify transmission options (default 0x01: disable acknowledge)
         frameod: Optional frameid, only used if Tx status is desired
      Returns:
         Message sent to XBee; stripped of start delimeter, MSB, LSB, and checksum;
          formatted into a readable string
      """
      return self.Send(msg.encode('utf-8'), addr, options, frameid)

   def Send(self, msg, addr=0xFFFF, options=0x01, frameid=0x00):
      """
      Inputs:
         msg: A message, in bytes or bytearray format, to be sent to an XBee
         addr: The 16 bit address of the destination XBee (default broadcast)
         options: Optional byte to specify transmission options (default 0x01: disable ACK)
         frameod: Optional frameid, only used if transmit status is desired
      Returns:
         Number of bytes sent
      """
      out = bytearray()

      out.append(0x7E)                 # Start delimeter
      out.append(0x00)                 # MSB (always zero)
      out.append(len(msg) + 5)         # LSB (number of bytes minus checksum)
      out.append(0x01)                 # Tx Request
      out.append(frameid)              # Frame ID
      out.append((addr & 0xFF00) >> 8) # Address MSB
      out.append(addr & 0xFF)          # Address LSB
      out.append(options)              # Options byte
      
      #  Append message content
      for c in msg:
         out.append(c) 

      # Calculate checksum byte
      out.append(self.CheckSum(out))

      # Escape any bytes containing reserved characters
      out = self.Escape(out)

      # return self.serial.write(out)

   def Validate(self, msg):
      """
      Parses a byte or bytearray object to verify the contents are a 
         properly formatted XBee message.  If validated, returns
         received message
      """

      # 10 bytes is Minimum length to be Rx message
      #  Src LSB, RSSI, Options, 1 byte data, checksum
      if len(msg) < 9: 
         return False

      # All bytes in message must be unescaped.
      #  Only exception is the start delimiter at the beginning
      frame = self.Unescape(msg)

      LSB = frame[1]
      # Frame (minus checksum) must contain at least length of LSB
      if LSB > (len(frame[2:]) - 1):
         return False

      # Validate checksum
      if (sum(frame[2:3+LSB]) & 0xFF) != 0xFF:
         return False

      self.RxQ.put(frame)
      print("Rx: " + self.format(msg))
      return True

   def Unescape(self, msg):
      """
      Helper function to unescaped an XBee API message.

      Inputs:
         msg: An byte or bytearray object containing a raw XBee message
               minus the start delimeter

      Outputs:
         XBee message with original characters.
      """
      out = bytearray()

      skip = False
      for i in range(len(msg)):
         if skip:
            skip = False
            continue

         if msg[i] == 0x7D:
            out.append(msg[i+1] ^ 0x20)
            skip = True
         else:
            out.append(msg[i])

      return out

   def Escape(self, msg):
      """
      Escapes reserved characters before an XBee message is sent.

      Inputs:
         msg: A bytes or bytearray object containing an original message to
               be sent to an XBee

      Outputs:
         A bytearray object prepared to be sent to an XBee in API mode
      """

      escaped = bytearray()
      reserved = bytearray("\x7E\x7D\x11\x13")

      escaped.append(msg[0])
      for m in msg[1:]:
         if m in reserved:
            escaped.append(0x7D)
            escaped.append(m ^ 0x20)
         else:
            escaped.append(m)

      return escaped

   def CheckSum(self, msg):
      """
      Calculate the checksum byte for an XBee message.

      Input:
         msg: An unescaped byte or bytearray object containing a full XBee message

      Output:
         A single byte containing the message checksum
      """
      return 0xFF - (sum(msg[3:]) & 0xFF)

   def format(self, msg):
      """
      Formats a byte or bytearray object into a more human readable string
         where each hexadecimal bytes are ascii charactesr separated by spaces

      Input:
         msg: A bytes or bytearray object

      Output:
         A string representation
      """
      return " ".join("{:02x}".format(b) for b in msg)