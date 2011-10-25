import pyhnet.hnet as hnet
import sys

def threadSafe(f):
    def g(self, *args, **kwargs):
        with self.lock:
            return f(self, *args, **kwargs)
    return g

class GameError(Exception): pass
class PlayerAlreadyAdded(GameError): pass
class PlayerAlreadyInGame(GameError): pass

#TODO need to make Ids classes, with a del function and 
    # make it work with a special with statement somehow
class Game:
    def __init__(self, gameName):
        self.players = {}
        self.clients = {}
        self.gameName = gameName
        self.playerIds = hnet.IdGen()
        self.lock = hnet.RLock()
        self.frame = hnet.Counter(0)
        self.gameFinished = hnet.Event()
        self.gameFinished.set()
    
    @threadSafe
    def startGame(self):
        if self.gameFinished.isSet():
            self.gameFinished.clear()
            hnet.startNewThread(self.run)
            print "Game started:", self.gameName
        
    def run(self):
        while not self.gameFinished.isSet():
          self.frame()
          self.sendGamePacket(("NewFrame", None), srcPlayerId = -1)
          self.gameFinished.wait(0.016667)
            
    def stop(self):
        self.gameFinished.set()
        print "Game ended:", self.gameName
    
    def sendGamePacket(self, packet, srcPlayerId = None, dstPlayerId = None):
        if srcPlayerId == None:
          srcPlayerId = self.clients[hnet.getClientId()]
        with self.frame.lock: # we don't want the server to send out the frame end packet before another packet in that frame
            if dstPlayerId == None:        
              for clientId, handler, _ in self.players.values():
                handler.send((srcPlayerId, self.frame.value, packet))
            else:
              clientId, handler, _ = self.players[dstPlayerId]
              handler.send((srcPlayerId, self.frame.value, packet))

    
    @threadSafe
    def newPlayer(self, playerData):
        for clientId, _, _ in self.players.values():
            if clientId == hnet.getClientId():
                raise PlayerAlreadyAdded("You are already a player in that game") # make custom exception for this 
        playerId = self.playerIds.nextId()
        self.players[playerId] = (hnet.getClientId(), hnet.getHandler(), playerData)
        self.clients[hnet.getClientId()] = playerId
        hnet.getHandler().runOnClose.append(lambda : self.delPlayer(playerId, hnet.getClientId()))
        self.startGame()
        self.sendGamePacket(("PlayerJoined", playerData))
        return playerId
        
    def delPlayer(self, playerId, clientId):
        del self.players[playerId]
        del self.clients[clientId]
        self.playerIds.releaseId(playerId)
        if not self.players:
            self.stop()
  
class GameManager:
  def __init__(self, server):
      self.server = server
      self.games = {}
      self.lock = hnet.Lock()
      self.clients = {}
      #TODO keep track of clients to make sure they only join one game
   
  @threadSafe
  def joinGame(self, gameName, playerData):
      clientId = hnet.getClientId()
      if clientId in self.clients:
        raise PlayerAlreadyInGame(self.clients[clientId][0])
      if gameName not in self.games:
          self.games[gameName] = Game(gameName)
      playerId = self.games[gameName].newPlayer(playerData)
      self.clients[hnet.getClientId()] = (gameName, playerId)
      hnet.getHandler().runOnClose.append(lambda : self.exitGame(playerData))
      print "Player %s joined game: %s:" % (playerData, gameName) 
      return playerId
      
  @threadSafe
  def exitGame(self, playerData):
      clientId = hnet.getClientId()
      gameName, playerId = self.clients[clientId]
      print "Player %s left game: %s:" % (playerData, gameName)
      del self.clients[clientId]
      if not self.games[gameName].players:
        del self.games[gameName]
      
  def sendGamePacket(self, gameName, packet, dstPlayerId = None):
      return self.games[gameName].sendGamePacket(packet, dstPlayerId = dstPlayerId)
      
class Server(hnet.HNetTCPServer):
    def onInit(self):
        self.gameManager = GameManager(self)
        
class ServerHandler(hnet.HNetHandler):
    def onRun(self):
        print "connected"
      
    def onRecv(self, packet):
        if packet.msg() == 'Hello':
            packet.replyWithProxy(self.server.gameManager)
        
    def onInit(self):
        self.runOnClose = []
        
    def onClose(self):
        for f in self.runOnClose:
            f()

def startServer():
    with Server([('', 6112)], ServerHandler) as s:
        try:
            while not s.done.isSet():
                s.done.wait(0.01)
        except KeyboardInterrupt:
            pass
        print "Shutting down server."
        
  
if __name__ == "__main__":
    startServer()
