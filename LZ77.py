import os
import sys

from bitstring import ConstBitStream, BitArray
from bitarray import bitarray


class LZ77:
    def __init__(self, window_size=12, future_size=4):
        self.window_size = min(255, window_size)
        self.future_size = min(255, future_size)
        self.window = 2 ** self.window_size
        self.future = 2 ** self.future_size
        self.data_len = 0
        print(f"readlength:{self.window + self.future + 1}, sys.maxsize: {sys.maxsize}")
    def ilgiausiasSutapimas(self, data, current_pos):
        future = min(current_pos + self.future, self.data_len + 1)
        start = max(0, current_pos - self.window)
        best_match_length = -1
        best_match_distance = -1
        for i in range(current_pos + 2, future):
            substring = data[current_pos:i]
            match = data.rfind(substring, start, current_pos)
            if match != -1:
                best_match_length = i - current_pos
                best_match_distance = current_pos - match
            else:
                break
        if best_match_distance > 0 and best_match_length > 0:
            return best_match_distance, best_match_length
        return None
    def compress(self, input_file, output_file):
        with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
            if self.future_size + self.window_size > 30:
                data = f_in.read(2 ** 30 - 1)
                readmore = (self.data_len == 2 ** 30 - 1)
            else:
                data = f_in.read(self.window + self.future + 1)
                readmore = (self.data_len == self.window + self.future + 1)
            self.data_len = len(data)
            readmore = (self.data_len == self.window + self.future + 1)

            i = 0

            f_out.write(bytes([self.window_size - 1]))
            f_out.write(bytes([self.future_size - 1]))
            output = bitarray()
            first = True
            while True:
                match = self.ilgiausiasSutapimas(data, i)
                if not match:
                    output.append(False)
                    # print(f"i: {i}, len(data): {self.data_len}, len(data):{len(data)}")
                    output.frombytes(bytes([data[i]]))
                    if first:
                        print(output)
                        first = False
                else:
                    output.append(True)
                    best_match_distance, best_match_length = match
                    output.extend(f"{(best_match_distance - 1):0{self.window_size}b}")
                    output.extend(f"{(best_match_length - 1):0{self.future_size}b}")
                    i += best_match_length - 1
                if readmore:
                    if i > self.data_len - self.future - 1:
                        read = f_in.read(self.future)
                        if len(read) != self.future:
                            readmore = False
                        print(f"len(read): {len(read)}, future: {self.future}")
                        data = data[self.future-1:]
                        data += read
                        i -= self.future - 1
                        self.data_len = len(data)
                if i == self.data_len - 1:
                    break
                if len(output) % 8 == 0:
                    f_out.write(output.tobytes())
                    output.clear()
                i += 1
            output.fill()
            f_out.write(output.tobytes())


    def decompress(self, input_file, output_file):
        self.window_size = 0
        self.window_size = 0
        output_buffer = []
        file_size = os.path.getsize(input_file)
        stream = ConstBitStream(filename=input_file)
        self.window_size = stream.read('uint:8') + 1
        self.future_size = stream.read('uint:8') + 1
        self.window = 2**self.window_size
        self.future = 2**self.future_size
        print(f"window_size: {self.window_size}")
        print(f"future_size: {self.future_size}")
        smallest_token = min((self.window_size + self.future_size + 1), 9)
        first = True
        with open(output_file, 'wb') as f_out:
            while stream.bitpos < file_size * 8:
                match = stream.read('bool:1')
                if match:
                    distance = stream.read(f'uint:{self.window_size}') + 1
                    length = stream.read(f'uint:{self.future_size}') + 1
                    if first:
                        print(f"distance:{distance}, length:{length}")
                        first = False
                    for i in range(length):
                        output_buffer.append(output_buffer[-distance])
                else:
                    app = stream.read('uint:8')
                    output_buffer.append(bytes([app]))
                if len(output_buffer) > self.window:
                    count = len(output_buffer) - self.window - 1
                    if count > 0:
                        f_out.write(b''.join(output_buffer[:count]))
                        output_buffer = output_buffer[count:]
                if stream.bitpos > ((file_size * 8) - smallest_token):
                    print(f"bitpos: {stream.bitpos}, file_size: {file_size}, smallest_token: {smallest_token}")
                    break
            f_out.write(b''.join(output_buffer))


ds = LZ77(16, 8)
ds.compress("example.bmp", "result")
ds.decompress("result", "result.bmp")
