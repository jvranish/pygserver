import pyhnet.hnet as hnet

class MyClientHandler(hnet.HNetHandler):
    def runConnection(self):
        reply = self.sendAndWait('Hello')
        obj = reply.proxy()
        playerId = obj.joinGame("MyGame", "Job")
        obj.sendGamePacket("MyGame", "asdf")
        obj.sendGamePacket("MyGame", "asdfasdgf")
        #time.sleep(0.3)
        # NOTE! we disconnect when this function returns
        #  if you want to for the remote side to disconnect, you can do:
        self.done.wait(0.3)
        
    def onRecv(self, packet):
        print packet.msg()
        
if __name__ == "__main__":
    MyClientHandler(hnet.connectTCP('localhost', 30131)).run().wait(1.0)
