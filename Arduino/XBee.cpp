#include "XBee.h"
#include "String.h"

int XBee::Receive(unsigned char *inBuff, int len, unsigned char *outBuff){
    int unescapeLen = 0;
    unsigned char checksum = 0;
    unsigned char LSB = 0;

    if (inBuff[0] != 0x7E)
        return 0;

    if (len < 10)
        return 0;

    unescapeLen = unescape(inBuff, len, outBuff);

    // Check we have at least the amount of bytes indicated by LSB
    LSB = outBuff[2]; 
    if (LSB > (unescapeLen - 4))
        return 0;

    // Calculate our checksum
    // (char will overflow, no need to AND for lower bytes)
    for (int i=3; i<LSB+4; i++){
        checksum += outBuff[i];
    }

    if (checksum != 0xFF)
        return 0;

    return LSB+4;
}


int XBee::Send(unsigned char *msg, int len, unsigned char *outBuff, int addr){
    unsigned char buf[100];
    int escapedLen = 0;
    unsigned char checksum = 0;

    buf[0] = 0x7E;
    buf[1] = 0x00;
    // LSB = content + 5 (content length + API type + frameid + addr(2) + options)
    buf[2] = (unsigned char)(len + 5);
    buf[3] = 0x01;  // transmit request
    buf[4] = 0x00;  // Frame ID
    buf[5] = (unsigned char)((addr & 0xFF00) >> 8);
    buf[6] = (unsigned char)(addr & 0xFF);
    buf[7] = 0x01;  // Disable acknowledge
    memcpy(&buf[8], msg, len);

    for (int i=3;i<len+8;i++){
        checksum += buf[i];
    }

    // Total length = LSB + 9 (LSB value + MSB + LSB + start delimeter + checksum)
    buf[len+8] = 0xFF - checksum;
    escapedLen = escape(buf, len+9, outBuff);

    return escapedLen;
}

int XBee::escape(unsigned char *input, int inLen, unsigned char *output){
    int pos = 1;

    output[0] = input[0];
    for (int i=1; i<inLen; i++){
        switch(input[i]){
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

int XBee::unescape(unsigned char *input, int inLen, unsigned char *output){
    int pos = 1;
    bool skip = false;
    unsigned char curr = 0;

    output[0] = input[0];
    for (int i=1; i<inLen; i++) {
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