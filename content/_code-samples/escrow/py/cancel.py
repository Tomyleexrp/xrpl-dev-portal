from xrpl.models import EscrowCancel
from xrpl.clients import JsonRpcClient
from xrpl.transaction import (safe_sign_and_autofill_transaction,
                              send_reliable_submission)
from xrpl.wallet import Wallet

client = JsonRpcClient("https://s.altnet.rippletest.net:51234") # connect to the testnetwork

# Cancel an escrow
# If the escrow wasnt created with a CancelAfter time, it never expires and this transaction fails

sender_seed = "sxxxxxxxxxxxxxxxxxxxxxx" # sender seeed
escrow_creator = "rxxxxxxxxxxxxxxxxxxxxxxxxxxx" # ecsrow creator/ sender address
escrow_seq = int # escrow sequence

# generate wallet object
sender_wallet = Wallet(seed=sender_seed, sequence=0)

# build escrow cancel transaction
cancel_txn = EscrowCancel(account=sender_wallet.classic_address, owner=escrow_creator, offer_sequence=escrow_seq)

# sign transaction with wallet
stxn = safe_sign_and_autofill_transaction(cancel_txn, sender_wallet, client)

# send transaction and wait for response
stxn_response = send_reliable_submission(stxn, client)

# parse response and return result
stxn_result = stxn_response.result

# parse result and print out the transaction result and transaction hash 
print(stxn_result["meta"]["TransactionResult"]) 
print(stxn_result["hash"])
