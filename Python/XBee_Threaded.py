import serial
import threading
try:
    import Queue  # Python 2.7
except:
    import queue as Queue  # Python 3.3
from time import sleep


class XBee(threading.Thread):
    rxbuff = bytearray()
    RxQ = Queue.Queue()
    stop = threading.Event()
    rx = True

    def __init__(self, serialport):
        threading.Thread.__init__(self)
        self.serial = serial.Serial(port=serialport, baudrate=9600, timeout=0)
        self.start()

    def shutdown(self):
        self.stop.set()
        self.join()

    def run(self):
        while not self.stop.is_set():
            self.Rx()
            sleep(0.01)

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
        except Queue.Empty:
            return None

    def Rx(self):
        """
        Checks serial for an incoming message.  If a message
         is received, calles Parse() to verify it is a properly
         formatted XBee API message.
        """
        if self.serial.inWaiting():
            remaining = self.serial.inWaiting()
            while remaining > 0:
                chunk = self.serial.read(remaining)
                remaining -= len(chunk)
                self.rxbuff.extend(chunk)

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
            addr: The 16 bit address of the destination XBee
              (default: 0xFFFF broadcast)
            options: Optional byte to specify transmission options
              (default 0x01: disable acknowledge)
            frameod: Optional frameid, only used if Tx status is desired
        Returns:
            Message sent to XBee; stripped of start delimeter,
            MSB, LSB, and checksum; formatted into a readable string
        """
        return self.Send(msg.encode('utf-8'), addr, options, frameid)

    def Send(self, msg, addr=0xFFFF, options=0x01, frameid=0x00):
        """
        Inputs:
            msg: A message, in bytes or bytearray format, to be sent to an XBee
            addr: The 16 bit address of the destination XBee
              (default broadcast)
            options: Optional byte to specify transmission options
              (default 0x01: disable ACK)
            frameod: Optional frameid, only used if transmit status is desired
        Returns:
            Number of bytes sent
        """
        if not msg:
            return 0

        hexs = '7E 00 {:02X} 01 {:02X} {:02X} {:02X} {:02X}'.format(
            len(msg) + 5,           # LSB (length)
            frameid,
            (addr & 0xFF00) >> 8,   # Destination address high byte
            addr & 0xFF,            # Destination address low byte
            options
        )

        frame = bytearray.fromhex(hexs)
        #  Append message content
        for c in msg:
            frame.append(c)

        # Calculate checksum byte
        frame.append(self.CheckSum(frame))

        # Escape any bytes containing reserved characters
        frame = self.Escape(frame)

        print("Tx: " + self.format(frame))
        return self.serial.write(frame)

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
        if not frame:
            return False

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
        if msg[-1] == 0x7D:
            # Last byte indicates an escape, can't unescape that
            return None

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
            msg: An unescaped byte or bytearray object containing a
              full XBee message

        Output:
            A single byte containing the message checksum
        """
        return 0xFF - (sum(msg[3:]) & 0xFF)

    def format(self, msg):
        """
        Formats a byte or bytearray object into a more human
          readable string where each hexadecimal bytes are ascii
          characters separated by spaces

        Input:
            msg: A bytes or bytearray object

        Output:
            A string representation
        """
        return " ".join("{:02x}".format(b) for b in msg)
