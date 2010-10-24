import pyhnet.hnet as hnet

class Server(hnet.HNetTCPServer):
    def onInit(self):
        pass
        
class ServerHandler(hnet.HNetHandler):
    def onRecv(self, packet):
        if packet.msg() == 'Hello':
            packet.reply('Good day sir!')
        
    def onInit(self):
        pass
        
    def onClose(self):
        pass

def startServer():
    with Server([('', 30131)], ServerHandler) as s:
        try:
            while not s.done.isSet():
                s.done.wait(0.01)
        except KeyboardInterrupt:
            pass
        print "Shutting down server."
        
  
if __name__ == "__main__":
    startServer()
