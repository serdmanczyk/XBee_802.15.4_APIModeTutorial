#include "XBee.h"
#include "String.h"

int XBee::Receive(unsigned char *inbuf, int len, unsigned char *outbuf)
{
   int unescapelen = 0;
   unsigned char checksum = 0;
   
   if (inbuf[0] != 0x7E)
      return 0;

   if (len < 10)
      return 0;

   unescapelen = unescape(inbuf, len, outbuf);

   if (outbuf[2] != (unescapelen - 4))
      return 0;

   for (int i=3; i<unescapelen; i++) {
      checksum += outbuf[i];
   }

   if (checksum != 0xFF)
      return 0;

   return unescapelen;
}


int XBee::Send(unsigned char *msg, int len, unsigned char *outbuf, int addr)
{
   unsigned char buf[100];
   int escapedlen = 0;
   unsigned char checksum = 0;

   buf[0] = 0x7E;
   buf[1] = 0x00;
   buf[2] = (unsigned char)(len + 5);
   buf[3] = 0x01;
   buf[4] = 0x00;  // Frame ID
   buf[5] = (unsigned char)((addr & 0xFF00) >> 8);
   buf[6] = (unsigned char)(addr & 0xFF);
   buf[7] = 0x01;  // Disable acknowledge
   memcpy(&buf[8], msg, len);

   for (int i=3;i<len+8;i++)
   {
      checksum += buf[i];
   }

   buf[len+8] = 0xFF - checksum;
   
   escapedlen = escape(buf, len+9, outbuf);

   return escapedlen;
}
//
//void XBee::outhex(unsigned char *buf, int len)
//{
//   char pbuf[200];
//
//   for (int i=0;i<len;i++)
//   {
//      sprintf(&pbuf[i*3], "%02X ", buf[i]);
//   }
//
//   printf(pbuf);
//}

int XBee::escape(unsigned char *input, int inlen, unsigned char *output)
{
   int pos = 1;

   output[0] = input[0];
   for (int i=1; i<inlen; i++)
   {
      switch(input[i])
      {
      case 0x7D:
      case 0x7E:
      case 0x11:
      case 0x13:
         output[pos++] = 0x7D;
         output[pos++] = input[i] ^ 0x20;
         break;
      default:
         output[pos++] = input[i];
         break;
      }
   }

   return pos;
}

int XBee::unescape(unsigned char *input, int inlen, unsigned char *output)
{
   int pos = 1;
   bool skip = false;
   unsigned char curr = 0;

   output[0] = input[0];
   for (int i=1; i<inlen; i++) {
      if (skip){
         skip = false;
         continue;
      }

      if (input[i] == 0x7D){
         curr = input[i+1] ^ 0x20;
         skip = true;
      }else{
         curr = input[i];
      }

      output[pos] = curr;
      pos++;
   }

   return pos;
}
