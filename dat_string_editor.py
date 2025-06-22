import struct
import sys
import os
import tempfile
import subprocess
import platform

string_count=0
string_header=b''
string_offset=[]
string_length=[]
string_id=[]
string=[]

def read_string_header(f):
    global string_header,string_count
    f.seek(0)
    string_header=f.read(8)
    print(f"Read String Header: ")
    f.seek(4)
    string_count=struct.unpack('<I', f.read(4))[0]
    print(f"String Count: {string_count}")
    pass
def read_string(f):
    global string_id, string_length, string_offset, string
    print(f"Read String: ")
    f.seek(8)
    for i in range(string_count):
        string_offset.append(struct.unpack('<I', f.read(4))[0])
        string_length.append(struct.unpack('<I', f.read(4))[0])
        string_id.append(struct.unpack('<I', f.read(4))[0])
        f.read(4)
        pass
    for i in range(string_count):
        f.seek(string_offset[i])
        string.append(f.read(string_length[i]).decode('utf-8'))
        pass
    for i in range(string_count):
        print(f"{i}, ID: {string_id[i]}, Offset: {string_offset[i]}, Length: {string_length[i]}, {string[i]}")
        pass
    pass
def replace_string(i,value):
    global string, string_length
    string[i]=value
    string_length[i]=len(value)
    print(f"Replace String {string_id[i]}, Length: {string_length[i]}, Value: {string[i]}")
    pass
def remove_string(i):
    global string, string_id, string_offset, string_length, string_count
    del string_id[i]
    del string_offset[i]
    del string_length[i]
    del string[i]
    string_count=string_count-1
def add_new_string(id, value):
    global string_id, string_length, string_offset, string, string_count
    string_id.append(id)
    string.append(value)
    string_offset.append(0)
    string_length.append(len(value))
    string_count=string_count+1
    pass

def sort_string():
    global string_id, string_length, string_offset, string

    # Gabungkan semua elemen dalam satu list sementara dan urutkan berdasarkan string_id
    sorted_data = sorted(zip(string_id, string_length, string_offset, string), key=lambda x: x[0])

    # Pisahkan kembali menjadi list masing-masing
    string_id, string_length, string_offset, string = map(list, zip(*sorted_data))
def rebuild_string(f):
    global string_count, string_header, string_id, string_length, string_offset, string
    # Tentukan nama file baru dengan suffix "-NEW.yaf"
    file_name_without_ext = os.path.splitext(f.name)[0]
    new_file_name = f"{file_name_without_ext}-NEW.dat"
    new_file_path = os.path.join(os.getcwd(), new_file_name)
    # Buat file kosong terlebih dahulu
    with open(new_file_path, "wb") as new_file:
        pass  # File dibuat tapi belum diisi, hanya memastikan file ada

    # Buka file dalam mode "r+b" dan tulis data YAF
    with open(new_file_path, "r+b") as t:
        print(f"Write Header String")
        t.write(string_header)
        t.seek(4)
        t.write(struct.pack('<I',string_count))
        for i in range(string_count):
            t.write(struct.pack('<I',string_offset[i]))
            t.write(struct.pack('<I',string_length[i]))
            t.write(struct.pack('<I',string_id[i]))
            t.write(b'\x00' * 4)
            pass
        string_offset_new=[]
        for i in range(string_count):
            string_offset_new.append(t.tell())
            t.write(string[i].encode('utf-8'))
            t.write(b'\x00')
            pass
        t.seek(8)
        for i in range(string_count):
            t.write(struct.pack('<I',string_offset_new[i]))
            t.read(12)
            pass
        pass

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} infile")
        return 1

    try:
        string_file = open(sys.argv[1], "r+b")
    except IOError:
        print(f"Cannot open {sys.argv[1]}")
        return 1

    #setelah browse file
    read_string_header(string_file)
    read_string(string_file)
    sort_string()
    rebuild_string(string_file)
    string_file.close()
    return 0

if __name__ == "__main__":
    main()
