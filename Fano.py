import os

from bitarray import bitarray
from bitstring import BitArray, ConstBitStream, ReadError


class Node:
    def __init__(self, symbol=None, left=None, right=None):
        self.symbol = symbol  # None if it's not a leaf
        self.left = left  # Left child (Node)
        self.right = right  # Right child (Node)


def fano_tree(symbols, probabilities):
    # Sort symbols by probability in descending order for a stable partition
    sorted_pairs = sorted(zip(probabilities, symbols), reverse=True)
    sorted_probs, sorted_symbols = zip(*sorted_pairs)

    def divide_and_code(symbols, probabilities):
        # If only one symbol remains, create a leaf node
        if len(symbols) == 1:
            return Node(symbol=symbols[0])

        # Find a partition that balances the probabilities
        total = sum(probabilities)
        partial_sum = 0
        split_index = 0

        for i, p in enumerate(probabilities):
            if partial_sum + p > total / 2:
                break
            partial_sum += p
            split_index = i

        # Partition symbols and probabilities into left and right sets
        left_symbols = symbols[:split_index + 1]
        right_symbols = symbols[split_index + 1:]
        left_probs = probabilities[:split_index + 1]
        right_probs = probabilities[split_index + 1:]

        # Recursively build the left and right subtrees
        left_node = divide_and_code(left_symbols, left_probs)
        right_node = divide_and_code(right_symbols, right_probs)

        # Return an internal node
        return Node(symbol=None, left=left_node, right=right_node)

    # Build and return the root of the Fano tree
    return divide_and_code(sorted_symbols, sorted_probs)


def encode_tree_bits(node: Node) -> bytes:
    bits = BitArray()

    def encode_node(n):
        if n.symbol is not None:
            # Leaf node: write '1', then the symbol as 8 bits
            bits.append('0b1')
            # Convert symbol to its ASCII byte
            symbol_code = ord(n.symbol)
            bits.append(f'uint:8={symbol_code}')
        else:
            # Internal node: write '0', then left and right recursively
            bits.append('0b0')
            encode_node(n.left)
            encode_node(n.right)

    encode_node(node)
    return bits.tobytes()


def decode_tree_bits(data: bytes) -> Node:
    # Wrap data in a BitArray for easy reading
    bits = BitArray(data)
    pos = 0  # bit position

    def read_bits(count):
        nonlocal pos
        val = bits[pos:pos + count]
        pos += count
        return val

    def read_bit():
        return read_bits(1).uint

    def read_uint8():
        return read_bits(8).uint

    def decode_node():
        bit = read_bit()  # read node type bit
        if bit == 1:
            # Leaf node
            symbol_code = read_uint8()
            return Node(symbol=bytes([symbol_code]))
        else:
            # Internal node
            left = decode_node()
            right = decode_node()
            return Node(symbol=None, left=left, right=right)

    return decode_node()


def get_code_for_symbol(root: Node, target_symbol: bytes) -> str:
    """
    Traverse the tree to find the leaf node with the target_symbol.
    Return the code as a string of '0' and '1'.
    If the symbol is not found, return None or raise an exception.
    """

    def dfs(node, path):
        # If this is a leaf node:
        if node.symbol is not None:
            if node.symbol == target_symbol:
                return path
            else:
                return None
        # If it's an internal node, search in left and right subtrees
        if node.left is not None:
            left_result = dfs(node.left, path + '0')
            if left_result is not None:
                return left_result
        if node.right is not None:
            right_result = dfs(node.right, path + '1')
            if right_result is not None:
                return right_result
        return None

    return dfs(root, "")


# To verify the codes, you can traverse the tree:
def code_exists(root: Node, code: str) -> (bool, str):
    """
    Check if a binary code exists in the Fano tree.

    Args:
        root (Node): The root of the Fano tree.
        code (str): The binary code to check (e.g., '010').

    Returns:
        tuple: (exists (bool), symbol (str or None))
    """
    current = root
    for bit in code:
        if bit == '0':
            if current.left is None:
                return False, None
            current = current.left
        elif bit == '1':
            if current.right is None:
                return False, None
            current = current.right
        else:
            raise ValueError(f"Invalid bit in code: '{bit}'. Only '0' and '1' are allowed.")

    if current.symbol is not None:
        return True, current.symbol
    else:
        return False, None


def skaiciuojam_daznius(filename):
    probs = {}
    with open(filename, "rb") as f:
        byte = f.read(1)
        while byte:
            probs[byte] = probs.get(byte, 0) + 1
            byte = f.read(1)
    return dict(sorted(probs.items(), key=lambda item: item[1]))


def uzkoduoti(infile, outfile, saknis):
    count = 0
    with open(infile, "rb") as f:
        with open(outfile, "wb") as f2:
            f2.write(b'\x00')
            tree = encode_tree_bits(saknis)
            f2.write(len(tree).to_bytes(2, byteorder='big'))
            f2.write(tree)
            inbyte = f.read(1)
            outbyte = ''
            while inbyte:
                outbyte += get_code_for_symbol(saknis, inbyte)
                if len(outbyte) >= 8:
                    conv = outbyte[:8]
                    outbyte = outbyte[8:]
                    f2.write(int(conv, 2).to_bytes(1, byteorder='big'))
                inbyte = f.read(1)
            while len(outbyte) > 0:
                if len(outbyte) < 8 and len(inbyte) > 0:
                    count = 8 - len(outbyte)
                    outbyte += '1' * count
                conv = outbyte[:8]
                outbyte = outbyte[8:]
                f2.write(int(conv, 2).to_bytes(1, byteorder='big'))
            f2.seek(0)
            f2.write(count.to_bytes(1, byteorder='big'))


def atkoduoti(infile, outfile):
    with open(infile, "rb") as f, open(outfile, "wb") as f2:
        bitstream = ConstBitStream(f)
        count = bitstream.read("uint:8")
        lentree = bitstream.read("uint:16")
        tree = bitstream.read(f"bytes:{lentree}")
        decoded = decode_tree_bits(tree)
        print(get_codes(decoded))

        read = ""
        size = os.path.getsize(infile) * 8 - count
        try:
            while bitstream.pos < size:
                read += bitstream.read('bin:1')
                exists, symbol = code_exists(decoded, read)
                if exists:
                    f2.write(symbol)
                    read = ""
        except ReadError:
            pass


def get_codes(node, prefix=""):
    if node.symbol is not None:
        # Leaf node
        return {node.symbol: prefix}
    codes = {}
    if node.left:
        codes.update(get_codes(node.left, prefix + "0"))
    if node.right:
        codes.update(get_codes(node.right, prefix + "1"))
    return codes

dazniai = skaiciuojam_daznius("example.bmp")
symbols, probabilities = zip(*dazniai.items())
root = fano_tree(symbols, probabilities)
bytesofroot = bitarray()
bytesofroot.frombytes((encode_tree_bits(root)))
print(bytesofroot)
print(get_codes(root))

uzkoduoti("example.bmp", "out", root)
atkoduoti("out", "res.bmp")
