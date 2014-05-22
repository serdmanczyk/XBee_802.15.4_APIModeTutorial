import serial

class XBee:
   def __init__(self, serialport):
      self.serial = serial.Serial(port=serialport, baudrate=9600, timeout=0)

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
      bytes = bytearray()
      [bytes.append(ord(c)) for c in msg]
      return self.Send(bytes, addr, options, frameid)

   def Send(self, msg, addr=0xFFFF, options=0x01, frameid=0x00):
      """
      Inputs:
         msg: A message, in bytes or bytearray format, to be sent to an XBee
         addr: The 16 bit address of the destination XBee (default broadcast)
         options: Optional byte to specify transmission options (default 0x01: disable ACK)
         frameod: Optional frameid, only used if Tx status is desired
      Returns:
         Message sent to XBee, formatted into a readable string.
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
      [out.append(c) for c in msg]

      # Calculate checksum byte
      out.append(self.CheckSum(out))

      # Escape any bytes containing reserved characters
      out = self.Escape(out)

      self.serial.write(out)

      return self.format(out)

   def Receive(self):
      """
      Checks serial for an incoming message.  If a message is received, 
         calles Parse() to verify it is a properly formatted XBee API message.
      """
      buf = bytearray()

      while self.serial.inWaiting():
         buf += self.serial.read()

      if buf:
         return self.Parse(buf)
      else:
         return None

   def Parse(self, msg):
      """
      Parses a byte or bytearray object to verify the contents are a 
         properly formatted XBee message.  If validated, returns
         received message
      """
      if msg[0] != 0x7E:
         return None

      # 10 bytes is Minimum length to be Rx message
      #  Src LSB, RSSI, Options, 1 byte data, checksum
      if len(msg) < 10: 
         return None

      # All bytes in message must be unescaped.
      #  Only exception is the start delimiter at the beginning
      frame = self.Unescape(msg)

      # LSB must match message length (minus checksum)
      if frame[2] != (len(frame[3:]) - 1):
         return None

      # Validate checksum
      if (sum(frame[3:]) & 0xFF) != 0xFF:
         return None

      return self.format(frame)

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
      out.append(msg[0])

      skip = False
      for i in range(1, len(msg)):
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
      reserved = bytearray.fromhex("7E 7D 11 13")

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
         where each hexadecimal byte is separated by a space

      Input:
         msg: A bytes or bytearray object

      Output:
         A string object
      """
      return " ".join("{:02x}".format(b) for b in msg)


if __name__ == "__main__":
   from time import sleep
   
   xbee = XBee("COM3")

   # A simple string message
   sent = xbee.SendStr("Hello World", 0x0001)
   print("Tx: " + sent)
   sleep(1)

   recv = xbee.Receive()
   print("Rx: " + recv)
   rxmsg = (bytearray.fromhex(recv[24:-3])).decode('ascii')
   print("rxmsg: " + rxmsg)

   # A message that requires escaping
   sent = xbee.Send(bytearray.fromhex("7e 7d 11 13 5b 01 01 01 01 01 01 01"))
   print("Tx: " + sent)
   sleep(1)
   
   recv = xbee.Receive()
   print("Rx: " + recv)
   rxmsg = bytearray.fromhex(recv[24:-3])
   print("rxmsg: " + xbee.format(rxmsg))
