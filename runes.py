import argparse
import json
import bitcoin.rpc
from bitcoin.core import lx, COIN
from bitcoin.core.script import OP_RETURN, CScript

class RuneProtocol:
    def __init__(self):
        self.proxy = bitcoin.rpc.Proxy()

    def symbol_to_int(self, symbol: str) -> int:
        if not all(c.isalpha() and c.isupper() for c in symbol):
            raise ValueError(f"Invalid symbol: {symbol}. Only uppercase letters A-Z are allowed")

        value = 0
        for i, c in enumerate(reversed(symbol)):
            value += (ord(c) - ord('A') + 1) * (26 ** i)
        return value


    def encode_varint(self, i: int) -> bytes:
        if i < 0:
            raise ValueError("Varints cannot be negative")

        elif i < (1 << 7):  # 7 bits, 1 leading zero bit
            return bytes([i])

        elif i < (1 << 14):  # 14 bits, 2 leading zero bits
            return bytes([0b10000000 | (i & 0x7F), (i >> 7)])

        elif i < (1 << 21):  # 21 bits, 3 leading zero bits
            return bytes([0b11000000 | (i & 0x7F), ((i >> 7) & 0x7F), (i >> 14)])

        # ... and so on for larger numbers

        else:
            raise ValueError("Integer too large to encode as varint")

    def decode_varint(self, data: bytes) -> int:
        if not data:
            raise ValueError("Data cannot be empty")
        first_byte = data[0]
        if first_byte < 0b11000000:
            return first_byte
        elif first_byte < 0b11100000:
            if len(data) < 2:
                raise ValueError("Insufficient data")
            return ((first_byte & 0b00111111) << 8) | data[1]
        elif first_byte < 0b11110000:
            if len(data) < 3:
                raise ValueError("Insufficient data")
            return ((first_byte & 0b00011111) << 16) | (data[1] << 8) | data[2]
        # ... and so on for larger encoded varints


    def select_utxo(self):
        # listunspent will return a list of UTXOs available in the wallet.
        # You might want to filter this list to suit your needs, e.g., by confirmation status or by amount.
        available_utxos = self.proxy.listunspent()

        if not available_utxos:
            raise ValueError("No available UTXOs")

        # A simple selection strategy, selecting the first available UTXO
        # Replace with more sophisticated logic as per your requirements.
        selected_utxo = available_utxos[0]

        return selected_utxo


    def create_op_return_output(self, data: bytes) -> CScript:
        return CScript([OP_RETURN, data])

    def issue_rune(self, symbol: str, decimals: int, amount: int, destination_address: str, fee_per_byte: int, live: bool):
        symbol_int = self.symbol_to_int(symbol)
        print(symbol_int)
        issuance_data = b'R' + self.encode_varint(symbol_int) + self.encode_varint(decimals)
        op_return_output = self.create_op_return_output(issuance_data)


        # Constructing inputs
        # Replace with actual logic to select appropriate UTXOs
        # Selecting UTXO
        utxo = self.select_utxo()

        utxo_tx_id = lx(utxo['txid'])  # Transaction id of the UTXO to spend
        vout = utxo['vout']
        input_value = utxo['amount']  # value of the selected UTXO in BTC
        inputs = [{'txid': utxo_tx_id, 'vout': vout}]

        # Constructing outputs
        # Replace with actual logic to calculate output amounts and destinations
        destination_address = CBitcoinAddress(destination_address)
        outputs = {destination_address: amount*COIN, op_return_output: 0}

        # Creating raw transaction
        raw_tx = self.proxy.createrawtransaction(inputs, outputs)

        # Signing the transaction
        signed_tx = self.proxy.signrawtransactionwithwallet(raw_tx)

        # Getting the size of the signed transaction
        signed_tx_size = len(signed_tx['hex']) // 2  # serialized tx is in hex, so divided by 2 to get bytes

        fee = int(signed_tx_size * fee_per_byte)

        # Calculating the change
        change = (input_value * COIN) - (amount * COIN + fee)

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

    def transfer_rune(self, rune_id: int, output_index: int, amount: int):
        # TODO: Implement Rune Transfer logic here
        1

# Command Line Arguments Handling, e.g. 'ABC', 2, 100
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Issue Rune via Command Line.')
    parser.add_argument('symbol', type=str, help='Symbol of the Rune to be issued.')
    parser.add_argument('decimals', type=int, help='Number of decimals of the Rune.')
    parser.add_argument('amount', type=int, help='Amount of Rune to be issued.')
    parser.add_argument('destination_address', type=str, help='Destination address for the transaction.')
    parser.add_argument('fee', type=int, help='Transaction fee in satoshis per byte.')
    parser.add_argument('--live', action='store_true', help='If provided, will broadcast the transaction to the network.')

    args = parser.parse_args()

    if args.fee <= 0:
        parser.error('fee must be a positive integer.')

    rune_protocol = RuneProtocol()
    rune_protocol.issue_rune(args.symbol, args.decimals, args.amount, args.destination_address, args.fee, args.live)
