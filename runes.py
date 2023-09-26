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


    def create_op_return_output(self, data: bytes) -> CScript:
        return CScript([OP_RETURN, data])

    def issue_rune(self, symbol: str, decimals: int, amount: int):
        symbol_int = self.symbol_to_int(symbol)
        issuance_data = b'R' + self.encode_varint(symbol_int) + self.encode_varint(decimals)
        op_return_output = self.create_op_return_output(issuance_data)


        tx = self.proxy.create_transaction({lx('utxo_tx_id'): (0, amount*COIN)}, {op_return_output: 0})

        # sign and send the transaction
        signed_tx = self.proxy.sign_transaction(tx)
        self.proxy.sendrawtransaction(signed_tx)

    def transfer_rune(self, rune_id: int, output_index: int, amount: int):
        # TODO: Implement Rune Transfer logic here
        1

# Example of issuing a rune
if __name__ == '__main__':
    rune_protocol = RuneProtocol()
    rune_protocol.issue_rune('ABC', 2, 100)
