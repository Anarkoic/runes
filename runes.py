import argparse
import json
"""import bitcoin.rpc
from bitcoin.core import lx, COIN
from bitcoin.core import CTransaction, CTxIn, CTxOut, COutPoint
from bitcoin.core.script import OP_RETURN, CScript
from bitcoin.wallet import CBitcoinAddress
from bitcoin import bech32
"""
import bitcointx.rpc
from bitcointx.core import b2lx, COutPoint, CTransaction, CTxIn, CTxOut
from bitcointx.core.script import CScript, OP_RETURN
from bitcointx.wallet import CCoinAddress  # Note the change here

COIN = 100_000_000  # Number of Satoshis in one Bitcoin

class RuneProtocol:
    BASE_OFFSET = 1  # set to 1 for 1-26 numbering, and 0 for 0-25 numbering

    def __init__(self, conf_file=None):
        # Here you can create a Proxy object with the given configuration file.
        # The exact parameter or method to use will depend on how the Proxy class is implemented.
        #self.proxy = bitcointx.rpc.Proxy(btc_conf_file=conf_file)
        bitcointx.select_chain_params('bitcoin')  # for mainnet


    def symbol_to_int(self, symbol: str) -> int:
        if not all(c.isalpha() and c.isupper() for c in symbol):
            raise ValueError(f"Invalid symbol: {symbol}. Only uppercase letters A-Z are allowed")

        value = 0
        for i, c in enumerate(reversed(symbol)):
            value += (ord(c) - ord('A') + self.BASE_OFFSET) * (26 ** i)
        return value

    def int_to_symbol(self, num: int) -> str:
        if num < 0:
            raise ValueError("Input must be a non-negative integer")

        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        symbol = ''

        if self.BASE_OFFSET == 1 and num == 0:  # In 1-26 numbering, 0 is invalid
            raise ValueError("Input must be a positive integer when using 1-26 numbering")

        if self.BASE_OFFSET == 0 and num == 0:
            return alphabet[0]  # return 'A' if num is 0

        while num > 0:
            num, remainder = divmod(num - self.BASE_OFFSET, 26)
            symbol = alphabet[remainder] + symbol  # prepend the character corresponding to the remainder

        return symbol



    def encode_varint(self, i: int) -> bytes:
        if i < 0:
            raise ValueError("Varints cannot be negative")

        # Initialize an empty bytes object to hold the varint
        encoded = bytes()

        while i > 127:  # 127 is the maximum value that can be encoded in 7 bits
            # Encode the lowest 7 bits of i, and set the continuation bit to 1
            encoded += bytes([(i & 0x7F) | 0x80])

            # Right shift i by 7 bits to remove the bits we've just encoded
            i >>= 7

        # Encode the last 7 bits of i without the continuation bit
        encoded += bytes([i])

        return encoded


    def decode_varint(self, encoded: bytes) -> int:
        decoded = 0  # Initialize the decoded integer
        shift = 0   # Initialize the bit shift counter

        for byte in encoded:
            # Extract the 7 least significant bits and accumulate in decoded
            decoded |= (byte & 0x7F) << shift

            # If the most significant bit is 0, this is the last byte
            if not (byte & 0x80):
                break

            # Prepare for the next byte
            shift += 7

        return decoded


    def select_utxo(self):
        # TODO not working yet
        # listunspent will return a list of UTXOs available in the wallet.
        # You might want to filter this list to suit your needs, e.g., by confirmation status or by amount.
        available_utxos = self.proxy.listunspent()

        """try:
            unspent_list = self.proxy.listunspent()
            for unspent in unspent_list:
                try:
                    unspent['address'] = CBitcoinAddress(unspent['address'])
                except CBitcoinAddressError:
                    unspent['address'] = 'Unrecognized Address Format'
        except Exception as e:
            print(f"An error occurred: {e}")
        if not available_utxos:
            raise ValueError("No available UTXOs")"""

        # A simple selection strategy, selecting the first available UTXO
        # Replace with more sophisticated logic as per your requirements.
        selected_utxo = available_utxos[0]

        return selected_utxo


    def create_op_return_output(self, data: bytes) -> CScript:
        return CScript([OP_RETURN, data])


    def issue_rune(self, symbol: str, decimals: int, amount: int, destination_address: str, change_address: str, fee_per_byte: int, live: bool):
        symbol_int = self.symbol_to_int(symbol)
        print(symbol_int)

        issuance_data = b'R' + self.encode_varint(symbol_int) + self.encode_varint(decimals)
        op_return_output = self.create_op_return_output(issuance_data)

        utxo_tx_id = "25c796a6c8aed0ba4d3de8f434168d62e7fb1c988e141a9bca914ed7571e2c32"
        vout = 0
        #txins = [CTxIn(COutPoint(b2lx(utxo_tx_id), vout))]
        #txins = [CTxIn(COutPoint(b2lx(bytes.fromhex(utxo_tx_id)), vout))]
        txins = [CTxIn(COutPoint(bytes.fromhex(utxo_tx_id)[::-1], vout))]


        destination_address_obj = CCoinAddress(destination_address)
        output_value = int(amount * COIN)
        destination_output = CTxOut(output_value, destination_address_obj.to_scriptPubKey())

        op_return_output = CTxOut(0, CScript([OP_RETURN, issuance_data]))
        tx = CTransaction(txins, [destination_output, op_return_output])

        raw_tx_hex = tx.serialize().hex()
        if live:
            txid = self.proxy.sendrawtransaction(raw_tx_hex)
            return txid
        else:
            print(tx)
            return None

    """def issue_rune(self, symbol: str, decimals: int, amount: int, destination_address: str, change_address: str, fee_per_byte: int, live: bool):
        symbol_int = self.symbol_to_int(symbol)
        print(symbol_int)

        # TODO transfer output stuff
        issuance_data = b'R' + self.encode_varint(symbol_int) + self.encode_varint(decimals)
        op_return_output = self.create_op_return_output(issuance_data)


        # Constructing inputs
        # Replace with actual logic to select appropriate UTXOs
        # Selecting UTXO
        #utxo = self.select_utxo()

        # TODO remove the hard-coding, e.g. if not getting unspent list, at least pass txid on commandline and look up txn details via RPC
        utxo_tx_id = "25c796a6c8aed0ba4d3de8f434168d62e7fb1c988e141a9bca914ed7571e2c32" #lx(utxo['txid'])  # Transaction id of the UTXO to spend
        vout = 0 #utxo['vout']
        input_value = 0.00100000 #utxo['amount']  # value of the selected UTXO in BTC
        inputs = [{'txid': utxo_tx_id, 'vout': vout}]


        # Create a CTxIn object for each input
        txins = [CTxIn(COutPoint(lx(utxo_tx_id), vout))]

        # Create normal CTxOut objects for regular outputs
        destination_address_obj = CBitcoinAddress(destination_address)
        output_value = int(amount * COIN)
        destination_output = CTxOut(output_value, destination_address_obj.to_scriptPubKey())

        # Create a CTxOut object for the OP_RETURN output
        op_return_output = CTxOut(0, CScript([OP_RETURN, issuance_data]))

        # Construct the transaction
        tx = CTransaction(txins, [destination_output, op_return_output])

        # Serialize and send the transaction
        raw_tx_hex = tx.serialize().hex()

        if live:
            # Broadcasting the transaction if live
            #txid = self.proxy.sendrawtransaction(signed_tx['hex'])
            txid = proxy.sendrawtransaction(raw_tx_hex)

            return txid
        else:
            # Output transaction info as JSON if not live
            print(tx)
            #print(json.dumps(signed_tx._asdict(), indent=4))
            return None
        """

    """
        # Constructing outputs
        # Replace with actual logic to calculate output amounts and destinations
        destination_address = str(destination_address) #CBitcoinAddress(destination_address)
        print(amount*COIN)
        print(COIN)
        outputs = {destination_address: amount, str(op_return_output): 0}

        # Creating raw transaction
        print("inputs:")
        print(inputs)
        print("outputs")
        print(outputs)
        raw_tx = self.proxy._call('createrawtransaction', inputs, outputs)
        """

    """
        # Signing the transaction
        signed_tx = self.proxy.signrawtransactionwithwallet(raw_tx)

        # Getting the size of the signed transaction
        signed_tx_size = len(signed_tx['hex']) // 2  # serialized tx is in hex, so divided by 2 to get bytes

        fee = int(signed_tx_size * fee_per_byte) # TODO probably convert sats fee to Bitcoin?

        # Calculating the change
        change = (input_value * COIN) - (amount * COIN + fee) # TODO probably remove COIN
        print("change")
        print(change)

        # if change is negative, inputs are not sufficient to cover outputs and fees
        if change < 0:
            raise ValueError('Insufficient funds to cover the transaction and fees')

        # If there is any change, you need to recreate, resign the transaction with the change output and adjusted fee.
        if change > 0:
            outputs[change_address] = change  # Assigning leftover to change address
            raw_tx = self.proxy.createrawtransaction(inputs, outputs)  # Creating the transaction again
            signed_tx = self.proxy.signrawtransactionwithwallet(raw_tx)  # Signing the transaction again

        if live:
            # Broadcasting the transaction if live
            txid = self.proxy.sendrawtransaction(signed_tx['hex'])
            return txid
        else:
            # Output transaction info as JSON if not live
            print(json.dumps(signed_tx._asdict(), indent=4))
            return None
        """

    def transfer_rune(self, rune_id: int, output_index: int, amount: int):
        # TODO: Implement Rune Transfer logic here
        1


def main():
    parser = argparse.ArgumentParser(description='Runes Command Line Interface.')
    #parser.add_argument('--conf', type=str, default=None, help='Path to the bitcoin configuration file.')

    subparsers = parser.add_subparsers(dest='command', help='Subcommand to run')

    # Subparser for the 'issue' command
    issue_parser = subparsers.add_parser('issue', help='Issue a new Rune.')
    issue_parser.add_argument('symbol', type=str, help='Symbol of the Rune to be issued.')
    issue_parser.add_argument('decimals', type=int, help='Number of decimals of the Rune.')
    issue_parser.add_argument('amount', type=int, help='Amount of Rune to be issued.')
    issue_parser.add_argument('destination_address', type=str, help='Destination address for the Rune.')
    issue_parser.add_argument('change_address', type=str, help='Change address for the transaction.')
    issue_parser.add_argument('fee', type=int, help='Transaction fee in satoshis per byte.')
    #issue_parser.add_argument('--conf', type=str, default='bitcoin.conf', help='Path to the bitcoin configuration file.')
    issue_parser.add_argument('--live', action='store_true', help='If provided, will broadcast the transaction to the network.')

    # Subparser for the 'symbol' command
    symbol_parser = subparsers.add_parser('symbol', help='Encode/Decode a symbol.')
    symbol_parser.add_argument('action', type=str, choices=['encode', 'decode'], help='Whether to encode or decode the symbol.')
    symbol_parser.add_argument('value', type=str, help='The symbol or integer to encode/decode.')

    # Varint Subparser
    varint_parser = subparsers.add_parser('varint', help='Varint operations.')
    varint_parser.add_argument('operation', choices=['encode', 'decode'], help='The varint operation to perform.')
    varint_parser.add_argument('value', type=str, help='The value to operate on.')


    args = parser.parse_args()

    obj = RuneProtocol() #conf_file=args.conf)  # Assume that YourClass accepts conf_file parameter

    if args.command == 'issue':
        if args.fee <= 0:
            parser.error('fee must be a positive integer.')
        obj.issue_rune(args.symbol, args.decimals, args.amount, args.destination_address, args.change_address, args.fee, args.live)
    elif args.command == 'symbol':
        if args.action == 'encode':
            print(obj.symbol_to_int(args.value))
        elif args.action == 'decode':
            print(obj.int_to_symbol(int(args.value)))  # Assume that int_to_symbol is implemented to decode an integer to a symbol

    if args.command == 'varint':
        if args.operation == 'encode':
            number = int(args.value)  # Convert string to int for encoding
            encoded = obj.encode_varint(number)  # Replace with your actual encoding logic
            print(encoded)

        elif args.operation == 'decode':
            decoded = obj.decode_varint(args.value)  # Replace with your actual decoding logic
            print(decoded)

if __name__ == '__main__':
    main()
