import time

class Timer:  
    def __init__(self):        
        self._start = 0.0        
        self._elapsedtime = 0.0
        self._running = 0
        self.timestr = ""               
        self._setTime(self._elapsedtime)

        
    def _setTime(self, elap):
        """ Set the time string to Minutes:Seconds:Millisecs """
        minutes = int(elap/60)
        seconds = int(elap - minutes*60.0)
        hseconds = int((elap - minutes*60.0 - seconds)*100)                
        self.timestr = '%02d:%02d:%02d' % (minutes, seconds, hseconds)
        self.timeInSecs =int(elap)


    def getTimeStr(self):
        return self.timestr

    def getTimeSecs(self):
        return self.timeInSecs
        
    def start(self):                                                     
        """ Start the stopwatch, ignore if running. """
        if not self._running:            
            self._start = time.time() - self._elapsedtime
            self._running = 1        
    
    def stop(self):                                    
        """ Stop the stopwatch, ignore if stopped. """
        if self._running:
            self._elapsedtime = time.time() - self._start    
            self._setTime(self._elapsedtime)
            self._running = 0
    
    def reset(self):                                  
        """ Reset the stopwatch. """
        self._start = time.time()         
        self._elapsedtime = 0.0    
        self._setTime(self._elapsedtime)
        
        
def main():
    import time
    ti = Timer()
    ti.start()
    t0 = time.clock()
    for i  in range(20000):
        print i * i *2    
    ti.stop()
    duration1S =  ti.getTimeStr()
    duration1 = ti.getTimeSecs()
    ti.reset()
    ti.start()
    for i  in range(20000):
        print i * i *2
    t1 = time.clock()
    print t1
    ti.stop()
    duration2S =  ti.getTimeStr()
    duration2 = ti.getTimeSecs()
    print duration1S
    print duration2S

if __name__ == '__main__':
    main()
