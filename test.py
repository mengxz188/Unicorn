# pip3 install redis

from multiprocessing import Pool
import time
import redis


def send_log():
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    sendChan = r.get('ClientSendChan').decode('utf-8')
    while True:
        # Using LPUSH to Send FlightLog
        cmd = "This is a FlightLog"
        r.lpush(sendChan, cmd)
        print('Pushed:', cmd)
        # ct = str(int(1000 * time.time()))
        time.sleep(1)


def receive_command():
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    recvChan = r.get('ClientRecvChan').decode('utf-8')
    while True:
        # Using BRPOP to Receive Command
        str = r.brpop(recvChan, timeout=0)
        print("Received:", str[1].decode('utf-8'))
        # ct = int(1000 * time.time())
        # print "Command Delay: %d ms" % (ct - int(str(job.body)))


def movement(command):
    control = {'w': ['PIT', 1], 's': ['PIT', -1],
               'a': ['AIL', 1], 'd': ['AIL', -1]}
    keys = command.split(',')
    action = {}
    for key in keys:
        col = control[key]
        action[col[0]] = col[1]
    print action

if __name__ == '__main__':
    # p = Pool(2)
    # p.apply_async(send_log)
    # p.apply_async(receive_command)
    # p.close()
    # p.join()

    import keyboard
    keyboard.add_hotkey('w', movement, args=('w'))
    keyboard.wait('esc')
