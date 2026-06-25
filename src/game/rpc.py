import time
from pypresence import Presence

client_id = "1513866112906039517"

def run_rpc():
    RPC = Presence(client_id)
    
    try:
        RPC.connect()
        RPC.update(state="v1.0", details="Jumping sessions")
        
        while True:
            time.sleep(15)

    except Exception as e:
        RPC.close()
        return False
    
    finally:
        RPC.close()