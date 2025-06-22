import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import struct
import sys
import os
import tempfile
import subprocess
import platform

root = tk.Tk()
root.title("String Editor PSP")

file_path_var = tk.StringVar()
dat_file_path =""
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

def browse_file():
    global dat_file_path, file_path_var  # tambahkan ini!
    dat_file_path = filedialog.askopenfilename(
        title="Pilih file DAT",
        filetypes=[("DAT Files", "*.dat")]
    )
    if dat_file_path:
        file_path_var.set(dat_file_path)
        print(f"Selected file: {dat_file_path}")
        reset_variables()
        read_file()
        add_button.config(state=tk.NORMAL)
    else:
        print("No file selected.")

def reset_variables():
    global string_count, string_header
    global string_offset, string_length, string_id, string

    string_count = 0
    string_header = b''
    string_offset = []
    string_length = []
    string_id = []
    string = []

def read_file():
    global dat_file_path
    try:
        string_listbox.delete(0, tk.END)  # Kosongkan listbox dulu

        with open(dat_file_path, "r+b") as string_file:
            read_string_header(string_file)
            read_string(string_file)
            print_string()  # Baru tampilkan isi yang baru dibaca

    except Exception as e:
        print(f"Failed to read file: {e}")


def print_string():
    string_listbox.delete(0, tk.END)  # Kosongkan listbox dulu
    for i in range(string_count):
        display_text = f"{i}, ID: {string_id[i]}, Offset: {string_offset[i]}, Length: {string_length[i]}, {string[i]}"
        string_listbox.insert(tk.END, display_text)


def on_listbox_double_click(event):
    selected_index = string_listbox.curselection()
    if not selected_index:
        return

    i = selected_index[0]
    current_id = string_id[i]
    current_value = string[i]

    edit_window = tk.Toplevel(root)
    edit_window.title("Edit String")
    edit_window.geometry("400x150")
    edit_window.grab_set()

    tk.Label(edit_window, text=f"ID: {current_id}").pack(pady=(15, 5))
    new_value_var = tk.StringVar(value=current_value)
    tk.Entry(edit_window, textvariable=new_value_var, width=50).pack(pady=(0, 10), padx=20)

    def apply_change():
        edit_string(i, new_value_var.get())
        edit_window.destroy()

    tk.Button(edit_window, text="OK", command=apply_change).pack()
    edit_window.focus_set()

def edit_string(i, new_value):
    replace_string(i, new_value)

    try:
        with open(dat_file_path, "r+b") as string_file:
            sort_string()
            rebuild_string(string_file)
    except Exception as e:
        print(f"Gagal memproses file: {e}")
        return

    success = backup_file(dat_file_path)
    if success:
        reset_variables()
        read_file()

        # ✅ Prompt sukses
        messagebox.showinfo(
            "Success",
            f"The string has been successfully updated."
        )


def backup_file(filepath):
    import os

    original = filepath
    new_output = filepath.replace(".dat", "-NEW.dat")
    backup = filepath + ".bak"

    if not os.path.exists(new_output):
        print(f"Gagal: {new_output} tidak ditemukan.")
        return False

    try:
        # Hapus backup lama jika sudah ada
        if os.path.exists(backup):
            os.remove(backup)
            print(f"Backup lama {backup} dihapus.")

        # Rename file asli ke .bak
        if os.path.exists(original):
            os.rename(original, backup)
            print(f"{original} berhasil dibackup menjadi {backup}")

        # Ganti nama file -NEW jadi file asli
        os.rename(new_output, original)
        print(f"{new_output} berhasil diubah menjadi {original}")
        return True

    except Exception as e:
        print(f"Terjadi kesalahan saat backup file: {e}")
        return False


def remove_file():
    selected_index = string_listbox.curselection()
    if not selected_index:
        messagebox.showinfo("Info", "No item selected to remove.")
        return

    i = selected_index[0]
    id_value = string_id[i]
    string_value = string[i]

    confirm = messagebox.askyesno(
        "Confirm Delete",
        f"Are you sure you want to remove this string?\n\nID: {id_value}\nValue: {string_value}"
    )

    if confirm:
        remove_string(i)

        try:
            with open(dat_file_path, "r+b") as string_file:
                sort_string()
                rebuild_string(string_file)
        except Exception as e:
            print(f"Gagal memproses file: {e}")
            return

        success = backup_file(dat_file_path)
        if success:
            reset_variables()
            read_file()

            # ✅ Prompt setelah penghapusan berhasil
            messagebox.showinfo(
                "Success",
                f"The string has been successfully removed."
            )

def open_add_new_window():
    add_window = tk.Toplevel(root)
    add_window.title("Add New String")
    add_window.geometry("400x200")
    add_window.grab_set()  # Modal - kunci window utama

    # Label + Spinbox untuk ID
    tk.Label(add_window, text="ID:").pack(pady=(15, 0))
    id_var = tk.IntVar(value=0)
    tk.Spinbox(add_window, from_=0, to=999999, textvariable=id_var, width=10).pack()

    # Label + Entry untuk Value
    tk.Label(add_window, text="Value:").pack(pady=(10, 0))
    value_var = tk.StringVar()
    tk.Entry(add_window, textvariable=value_var, width=50).pack(padx=20)

    # OK button
    def add_string():
        new_id = id_var.get()
        new_value = value_var.get()

        if new_value == "":
            messagebox.showwarning("Warning", "Value cannot be empty.")
            return

        if new_id in string_id:
            messagebox.showerror("Error", f"ID {new_id} already exists.")
            return

        # Tambahkan ke memori
        add_new_string(new_id, new_value)

        # Rebuild dan backup
        try:
            with open(dat_file_path, "r+b") as string_file:
                sort_string()
                rebuild_string(string_file)
        except Exception as e:
            print(f"Gagal memproses file: {e}")
            return

        success = backup_file(dat_file_path)
        if success:
            reset_variables()
            read_file()

            messagebox.showinfo(
                "Success",
                "The new string has been successfully added."
            )

        add_window.destroy()

    tk.Button(add_window, text="OK", command=add_string).pack(pady=15)
    add_window.focus_set()


def rebuild_file():
    try:
        with open(dat_file_path, "r+b") as string_file:
            sort_string()
            rebuild_string(string_file)
    except Exception as e:
        print(f"Gagal memproses file: {e}")
        return

    success = backup_file(dat_file_path)
    if success:
        reset_variables()
        read_file()

        # ✅ Prompt sukses
        messagebox.showinfo(
            "Success",
            f"The string has been successfully updated."
        )


# ========== GUI ==========
# File browse
tk.Label(root, text="String File:").grid(row=0, column=0, padx=10, pady=10)
file_entry = tk.Entry(root, textvariable=file_path_var, width=50)
file_entry.grid(row=0, column=1, padx=10, pady=10)
browse_button = tk.Button(root, text="Browse", command=browse_file)
browse_button.grid(row=0, column=2, padx=10, pady=10)

# Listbox
tk.Label(root).grid(row=1, column=0, padx=10, pady=10)
string_listbox = tk.Listbox(root, selectmode=tk.SINGLE, height=15, width=80)
string_listbox.grid(row=1, column=1, columnspan=2, padx=10, pady=10)
string_listbox.bind("<Double-Button-1>", on_listbox_double_click)

# Button frame
button_frame = tk.Frame(root)
button_frame.grid(row=2, column=1, padx=10, pady=10)

tk.Button(button_frame, text="Remove", command=remove_file).pack(side=tk.LEFT, padx=(0, 10))
add_button = tk.Button(button_frame, text="Add New", command=open_add_new_window)
add_button.pack(side=tk.LEFT, padx=(0, 10))
add_button.config(state=tk.DISABLED)  # Awalnya disable
tk.Button(button_frame, text="Rebuild", command=rebuild_file).pack(side=tk.LEFT)

root.mainloop()
