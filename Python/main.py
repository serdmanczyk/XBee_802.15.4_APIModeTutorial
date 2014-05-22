import XBee

if __name__ == "__main__":
   from time import sleep
   
   xbee = XBee.XBee("COM3")

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
