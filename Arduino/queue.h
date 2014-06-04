#ifndef Queue_H
#define Queue_H

#define Q_SIZE (220) //  Max XBee message length is 100.  Give a little space

class Queue{
public:
    Queue();
    ~Queue();
    bool Empty(){return (m_Size == 0);}
    bool Full(){return (m_Size == Q_SIZE);}
    unsigned int Size(){return m_Size;}
    bool Enqueue(unsigned char d);
    unsigned char Dequeue();
    int QueueString(unsigned char *s, int len);
    int Copy(unsigned char *outbuf, int start);

    unsigned char Peek(unsigned int pos);
    int Clear(unsigned int pos);

private:
    unsigned char m_Data[Q_SIZE];
    unsigned int m_Head; // points to oldest data element
    unsigned int m_Tail; // points to next free space 
    unsigned int m_Size; // quantity of elements in queue
};
#endif
