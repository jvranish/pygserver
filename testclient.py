import pyhnet.hnet as hnet

class MyClientHandler(hnet.HNetHandler):
    def runConnection(self):
        reply = self.socket.sendAndWait('Hello')
        print reply.msg()
        # NOTE! we disconnect when this function returns
        #  if you want to for the remote side to disconnect, you can do:
        #  self.done.wait()
        
    def onRecv(self, packet):
        pass
        
if __name__ == "__main__":
    MyClientHandler(hnet.connectTCP('localhost', 30131)).run().wait(1.0)
