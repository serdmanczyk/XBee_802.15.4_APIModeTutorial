#include "XBee.h"
#include <SoftwareSerial.h>
XBee xbee;
SoftwareSerial mySerial(10,11); // RX, TX

void setup(void)
{
  mySerial.begin(9600);
  Serial.begin(9600);
}

void loop(void)
{
   unsigned char inbuf[100];
   unsigned char msgbuf[100];
   int len = 0;
   int msglen = 0;
   
   delay(25);
   
   if (mySerial.available()>10){
     len = mySerial.available();
     for (int i=0; i<len; i++)
     { 
       inbuf[i] = (unsigned char)mySerial.read(); 
     }
    
   msglen = xbee.Receive(inbuf, len, msgbuf);
   if (msglen > 0)
   {
      unsigned char outmsg[100];
      unsigned char outframe[100];
      int framelen = 0;
      int addr = ((int)msgbuf[4] << 8) + (int)msgbuf[5];

      memcpy(outmsg, "you sent: ", 10);      // 10 is length of "you sent: "
      memcpy(&outmsg[10], &msgbuf[8], msglen-9);   // len - (9 bytes of frame not in message content)

      framelen = xbee.Send(outmsg, msglen+1, outframe, addr);        // 10 + (-9) = 1 more byte in new content than in previous message
      Serial.print(framelen);
      Serial.write(outframe, framelen);
      mySerial.write(outframe, framelen);
   }
   }
}
