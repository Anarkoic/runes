### Install

```sh
pip install -r requirements.txt
```

## Runes by Casey

### [Runes Blog Post by Casey](https://rodarmor.com/blog/runes/)


### Overview
Rune balances are held by UTXOs. A UTXO can contain any amount of any number of runes.

A transaction contains a protocol message if it has an output whose script pubkey contains an OP_RETURN followed by a data push of the ASCII uppercase letter R. The protocol message consists of all data pushes after the first.

Runes input to a transaction with an invalid protocol message are burned. This permits future upgrades that change how runes are assigned or created from creating situations where old clients erroneously assign rune balances.

Integers are encoded as prefix varints, where the number of leading ones in a varint determines its length in bytes.

### Transfer
The first data push in a protocol message is decoded as a sequence of integers.

These integers are interpreted as a sequence of (ID, OUTPUT, AMOUNT) tuples. If the number of decoded integers is not a multiple of three, the protocol message is invalid.

- ID is the numeric ID of the rune to assign.
- OUTPUT is the index of the output to assign it to.
- AMOUNT is the amount of the rune to assign.

ID is encoded as a delta, allowing multiple assignments of the same rune to avoid repeating the full rune ID. For example, the tuples:

```
[(100, 1, 20), (0, 2, 10), (20, 1, 5)]
```

Make the following assignments:
- ID 100, output 1, 20 runes
- ID 100, output 2, 10 runes
- ID 120, output 1, 5 runes

The AMOUNT 0 is shorthand for "all remaining runes."

After processing all tuple assignments, any unassigned runes are assigned to the first non-OP_RETURN output, if any.

Excess assignments are ignored.

Runes may be burned by assigning them to the OP_RETURN output containing the protocol message.

### Issuance
If the protocol message has a second data push, it is an issuance transaction. The second data push is decoded as two integers, SYMBOL, DECIMALS. If additional integers remain, the protocol message is invalid.

An issuance transaction may create any amount, up to 2^128 - 1, of the issued rune, using the ID 0 in assignment tuples.

SYMBOL is a base 26-encoded human-readable symbol, containing only valid characters A through Z.

DECIMALS is the number of digits after the decimal point that should be used when displaying the issued rune.

If SYMBOL has not already been assigned, it is assigned to the issued rune, and the issued rune receives the next available numeric rune ID, starting at one.

If SYMBOL has already been assigned, or is BITCOIN, BTC, or XBT, then no new rune is created. Issuance transaction assignments using the 0 rune ID are ignored, but other assignments are still processed.

### Notes
When displaying UTXO balances, the native bitcoin balance of a UTXO can be displayed with rune ID zero and the symbol BITCOIN, BTC, or XBT.

No attempt is made to avoid symbol squatting to maintain the protocol's simplicity. One possible, yet simple, technique to avoid symbol squatting would be to only allow the assignment of symbols above a certain length, with that length decreasing over time, eventually reaching zero and allowing all symbols. This approach would prevent the assignment of short, desirable symbols in the early days of the protocol and encourage competition for desirable symbols later on, when such competition might be more meaningful.


### Additional Descriptions & Details

#### Data Pushes

In the Bitcoin protocol, a "data push" refers to the method of adding data to a transaction's script. Bitcoin transactions comprise inputs and outputs, each having a script. The script is essentially a list of instructions specifying how to process the transaction, typically involving pushing data onto a stack and then performing operations on that data.

When discussing "second data push" in the context of the Rune protocol:

- `OP_RETURN` is an opcode specifying that this output is provably unspendable and is used to hold data within the transaction.
- The first sequence of data or "first data push" after `OP_RETURN` is used for encoding the transfer of runes according to the Rune protocol.
- A "second data push," if present, signifies it as an issuance transaction and is used for encoding the `SYMBOL` and `DECIMALS` for the rune being issued.

In essence, an `OP_RETURN` output with two data pushes might be represented as:
```plaintext
OP_RETURN [Data Push 1] [Data Push 2]
```
- `Data Push 1` is the first set of data added to the script, encoding rune transfers.
- `Data Push 2` is the second set of data, used in issuance transactions to encode the `SYMBOL` and `DECIMALS` of the newly issued rune.

