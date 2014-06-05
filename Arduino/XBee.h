#ifndef XBEE_H
#define XBEE_H

class XBee{
public:
    XBee(){;}
    ~XBee(){;}
   
    int Receive(unsigned char *inbuf, int len, unsigned char *outbuf);
    int Send(unsigned char *buf, int len, unsigned char *outbuf, int addr = 0xFFFF);
private:
    int escape(unsigned char *input, int inlen, unsigned char *output);
    int unescape(unsigned char *input, int inlen, unsigned char *output);
};
#endif
