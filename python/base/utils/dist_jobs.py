
import os
import tempfile
import paramiko

ESC = chr(27)
RBB = ESC + '[41;1m'
GBB = ESC + '[42;1m'
RBT = ESC + '[31;1m'
GBT = ESC + '[32;1m'
RESET = ESC + "[0m"

class Connection(object):
    """Friendly Python SSH2 interface.
    Connects and logs into the specified hostname. 
    Arguments that are not given are guessed from the environment.""" 

    def __init__(self,
                 host,
                 username = None,
                 private_key = None,
                 password = None,
                 port = 22,
                 log = True,
                 ):        
        self._sftp_live = False
        self._sftp = None
        if not username:
            username = os.environ['LOGNAME']
  
        ERROR = 40
        logger = paramiko.util.get_logger('paramiko')
        logger.setLevel(ERROR)
        if log:    
            # Log to a temporary file.
            templog = tempfile.mkstemp('.txt', 'ssh-')[1]
            paramiko.util.log_to_file(templog, ERROR)

        # Begin the SSH transport.
        self._transport = paramiko.Transport((host, port))
        self._transport_live = True
        
        # Authenticate the transport.
        if password:
            # Using Password.
            self._transport.connect(username = username, password = password)
        else:
            # Use Private Key.
            if not private_key:
                # Try to use default key.
                if os.path.exists(os.path.expanduser('~/.ssh/id_rsa')):
                    private_key = '~/.ssh/id_rsa'
                elif os.path.exists(os.path.expanduser('~/.ssh/id_dsa')):
                    private_key = '~/.ssh/id_dsa'
                else:
                    raise TypeError, "You have not specified a password or key."

            private_key_file = os.path.expanduser(private_key)
            rsa_key = paramiko.RSAKey.from_private_key_file(private_key_file)
            self._transport.connect(username = username, pkey = rsa_key)
    
    def _sftp_connect(self):
        """Establish the SFTP connection."""
        if not self._sftp_live:
            self._sftp = paramiko.SFTPClient.from_transport(self._transport)
            self._sftp_live = True

    def get(self, remotepath, localpath = None):
        """Copies a file between the remote host and the local host."""
        if not localpath:
            localpath = os.path.split(remotepath)[1]
        self._sftp_connect()
        self._sftp.get(remotepath, localpath)

    def put(self, localpath, remotepath = None):
        """Copies a file between the local host and the remote host."""
        if not remotepath:
            remotepath = os.path.split(localpath)[1]
        self._sftp_connect()
        self._sftp.put(localpath, remotepath)

    def execute(self, command):
        """Execute the given commands on a remote machine."""
        channel = self._transport.open_session()
        channel.exec_command(command)
        output = channel.makefile('rb', -1).readlines()
        if output:
            return output
        else:
            return channel.makefile_stderr('rb', -1).readlines()

    def close(self):
        """Closes the connection and cleans up."""
        # Close SFTP Connection.
        if self._sftp_live:
            self._sftp.close()
            self._sftp_live = False
        # Close the SSH Transport.
        try:
            if self._transport_live:
                self._transport.close()
                self._transport_live = False
        except AttributeError:
            pass

    def __del__(self):
        """Attempt to clean up if not explicitly closed."""
        self.close()

def main():
    """Little test when called directly."""
    # Set these to your own details.
    myssh = Connection('example.com')
    myssh.put('ssh.py')
    myssh.close()

# start the ball rolling.
if __name__ == "__main__":
    get_cpu_load_cmd = "python /home/csunix/scksrd/cpu_load.py"
    ppservers = ["cslin065.leeds.ac.uk:8080","cslin066.leeds.ac.uk:8080","cslin067.leeds.ac.uk:8080",\
                "cslin068.leeds.ac.uk:8080","cslin069.leeds.ac.uk:8080","cslin070.leeds.ac.uk:8080",\
                "cslin071.leeds.ac.uk:8080","cslin073.leeds.ac.uk:8080","cslin074.leeds.ac.uk:8080",\
                "cslin075.leeds.ac.uk:8080","cslin076.leeds.ac.uk:8080","cslin077.leeds.ac.uk:8080",\
                "cslin011.leeds.ac.uk:8080","cslin012.leeds.ac.uk:8080",                            \
                "cslin020.leeds.ac.uk:8080","cslin021.leeds.ac.uk:8080","cslin022.leeds.ac.uk:8080",\
                "cslin023.leeds.ac.uk:8080","cslin024.leeds.ac.uk:8080","cslin025.leeds.ac.uk:8080",\
                "cslin026.leeds.ac.uk:8080","cslin027.leeds.ac.uk:8080","cslin028.leeds.ac.uk:8080",\
                "cslin029.leeds.ac.uk:8080","cslin030.leeds.ac.uk:8080","cslin031.leeds.ac.uk:8080",\
                "cslin032.leeds.ac.uk:8080","cslin033.leeds.ac.uk:8080","cslin036.leeds.ac.uk:8080",\
                "cslin037.leeds.ac.uk:8080","cslin038.leeds.ac.uk:8080","cslin039.leeds.ac.uk:8080",\
                "cslin040.leeds.ac.uk:8080","cslin041.leeds.ac.uk:8080","cslin042.leeds.ac.uk:8080",]

    learn_cmd = ' '
    valid_servers = []
    count = 0
    max_cpu_load = 75
    for serv in ppservers:
        [server, port] = serv.split(':')
        try:
            s = Connection(host = server, log = False)
            print GBB + 'connected to: ' + server + RESET
            load = s.execute(get_cpu_load_cmd)
            s.close()
        except Exception:
            print RBB + 'Warning: Could not connect to ' + server + ', skipping it' + RESET
            continue
        cpu_load  = eval(load[0].strip().split()[0])
        mem_avail = eval(load[0].strip().split()[1])
        if cpu_load > max_cpu_load:
            # too much load on system, someone is busy on the system, end this process
            print server + ' is an ' + RBT + 'INVALID' + RESET + ' server with load: ' + repr(cpu_load)
            continue
        ppservers.remove(serv)
        valid_servers.append((cpu_load, serv))
        print server + ' is a ' + GBT + 'VALID' + RESET + ' server with load: ' + repr(cpu_load)
        count += 1

    # Sort in descending order of server load.     
    valid_servers.sort() 
    if len(valid_servers) == 0:
        print RBT + 'Valid servers not enough to submit all jobs.' + RESET
            
    for (cpu_load, serv) in valid_servers:
        [server, port] = serv.split(':')
        pid = os.fork()
        if pid == 0:
            # if child process
            s = Connection(host = server, log = False)
            print 'Executing remotely ' + learn_cmd
            s.execute(learn_cmd)
            s.close()
            os._exit(0)
            time.sleep(25)          
    print 'All tasks submitted to remote workers'
