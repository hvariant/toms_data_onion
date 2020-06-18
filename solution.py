import base64
import sys
import string
import random

def slurp(fn):
    s = b''
    with open(fn, 'rb') as f:
        for line in f:
            s += line.strip()
    return s

def decode_a86(fn):
    return base64.a85decode(slurp(fn), adobe=True)

def layer0(fn):
    print(decode_a86(fn).decode('utf-8'))

def layer1_op(b):
    flipped = (b ^ 0b01010101)
    return flipped >> 1 | ((flipped & 1) << 7)

def layer1(fn):
    puzzle_input = decode_a86(fn)
    puzzle = bytearray(puzzle_input)
    for i in range(len(puzzle)):
        puzzle[i] = layer1_op(puzzle[i])

    print(puzzle.decode('utf-8'))

def is_parity_valid(b):
    parity = b & 1
    for i in range(7):
        if b & (1 << (i+1)):
            parity = parity ^ 1
    return parity == 0

def group_by_8(bs):
    b0 = ((bs[0] << 1) & 0xff) | ((bs[1] & (0b1000000)) >> 6)
    b1 = ((bs[1] << 2) & 0xff) | ((bs[2] & (0b1100000)) >> 5)
    b2 = ((bs[2] << 3) & 0xff) | ((bs[3] & (0b1110000)) >> 4)
    b3 = ((bs[3] << 4) & 0xff) | ((bs[4] & (0b1111000)) >> 3)
    b4 = ((bs[4] << 5) & 0xff) | ((bs[5] & (0b1111100)) >> 2)
    b5 = ((bs[5] << 6) & 0xff) | ((bs[6] & (0b1111110)) >> 1)
    b6 = ((bs[6] << 7) & 0xff) | bs[7]
    return bytearray([b0,b1,b2,b3,b4,b5,b6])

def layer2(fn):
    puzzle_input = decode_a86(fn)

    # remove corrupted bytes
    filtered = bytearray(
        map(
            lambda b: b >> 1,
            filter(is_parity_valid, puzzle_input)
        )
    )

    fudged = bytearray()
    for i in range(len(filtered)//8):
        fudged.extend(group_by_8(filtered[i*8:i*8+8]))

    print(fudged.decode('utf-8'))

def acceptable_title(b):
    return (b == ord('=')
        or b == ord('[')
        or b == ord(']')
        or b == ord('/')
        or b == ord(':')
        or ord('0') <= b <= ord('9')
        or ord('A') <= b <= ord('Z')
        or ord('a') <= b <= ord('z')
        or b == ord(' '))

def guess_candidate_keys(puzzle_input):
    #
    # Assume that the first block of bytes include the title up to ],
    # so the second block of bytes must begin with ============================\n
    # then try the following:
    #
    #   >>> initial_bytes_second = b"============================\n"
    #   >>> key = [c ^ t for (c, t) in zip(initial_bytes, puzzle_input[32:])]
    #   >>> initial_bytes = bytearray([k ^ c for (k, c) in zip(key, s)])
    #   >>> initial_bytes
    #   bytearray(b'==[ Layer 4/5: Network Traffi')
    #   >>> len(initial_bytes)
    #   29
    #

    initial_bytes = b'==[ Layer 4/5: Network Traffic'
    key = bytearray()
    for i in range(len(initial_bytes)):
        key.append(puzzle_input[i] ^ initial_bytes[i])
    acceptable_bytes = set(bytes(string.printable, 'ascii'))

    candidates = []
    def search(i):
        if len(key) == 32:
            candidates.append(key.copy())
            return

        for k in range(0x100):
            good = True
            if not acceptable_title(puzzle_input[i] ^ k):
                good = False
            if good:
                j = 0
                while i + j * 32 < len(puzzle_input):
                    if puzzle_input[i + j * 32] ^ k not in acceptable_bytes:
                        good = False
                        break
                    j = j + 1

            if good:
                key.append(k)
                search(i+1)
                key.pop()

    search(len(initial_bytes))
    print(len(candidates)) # 6 candidates left

    for candidate in candidates:
        first_block = bytearray([k ^ c for (k, c) in zip(candidate, puzzle_input)])
        print(first_block)

    # bytearray(b'==[ Layer 4/5: Network Traffic Z')
    # bytearray(b'==[ Layer 4/5: Network Traffic ]')

    # the second candidate makes more sense
    return candidates[1]

def layer3(fn):
    puzzle_input = decode_a86(fn)
    key = guess_candidate_keys(puzzle_input)

    solution = bytearray()
    for i in range(len(puzzle_input) // 32 + 1):
        solution.extend([k ^ c for (k, c) in zip(key, puzzle_input[i*32:i*32 + 32])])
    print(solution.decode('utf-8'))

if __name__ == "__main__":
    layer = int(sys.argv[1])
    fn = sys.argv[2]

    if layer == 0:
        layer0(fn)
    if layer == 1:
        layer1(fn)
    if layer == 2:
        layer2(fn)
    if layer == 3:
        layer3(fn)
    else:
        print("not implemented yet")
