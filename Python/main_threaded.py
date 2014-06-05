import XBee_Threaded
from time import sleep

if __name__ == "__main__":
    xbee = XBee_Threaded.XBee("COM3")  # Your serial port name here

    # A simple string message
    sent = xbee.SendStr("Hello World")
    Msg = xbee.Receive()
    if Msg:
        content = Msg[7:-1].decode('ascii')
        print("Msg: " + content)

    # A message that requires escaping
    xbee.Send(bytearray.fromhex("7e 7d 11 13 5b 01 01 01 01 01 01 01"))
    Msg = xbee.Receive()
    if Msg:
        content = Msg[7:-1]
        print("Msg: " + xbee.format(content))

    xbee.shutdown()
