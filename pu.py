 #!/usr/bin/env python3
import ctypes
import argparse
from pathlib import Path
import os
import sys

# Пути к логам
WTMP_FILE = Path("/var/log/wtmp")
LASTLOG_FILE = Path("/var/log/lastlog")
WTMP_BAK = Path("/var/log/wtmp.bak")
LASTLOG_BAK = Path("/var/log/lastlog.bak")

# ---- STRUCT DEFINITIONS ----

class ExitStatus(ctypes.Structure):
    _fields_ = [("e_termination", ctypes.c_short),
                ("e_exit", ctypes.c_short)]

class Utmpx(ctypes.Structure):
    _fields_ = [
        ("ut_type", ctypes.c_short),
        ("ut_pid", ctypes.c_int),
        ("ut_line", ctypes.c_char * 32),
        ("ut_id", ctypes.c_char * 4),
        ("ut_user", ctypes.c_char * 32),
        ("ut_host", ctypes.c_char * 256),
        ("ut_exit", ExitStatus),
        ("ut_session", ctypes.c_int),
        ("ut_tv_sec", ctypes.c_int),
        ("ut_tv_usec", ctypes.c_int),
        ("__unused", ctypes.c_char * 36)
    ]

class Lastlog(ctypes.Structure):
    _fields_ = [
        ("ll_time", ctypes.c_uint32),
        ("ll_line", ctypes.c_char * 32),
        ("ll_host", ctypes.c_char * 256)
    ]

UTMPX_SIZE = ctypes.sizeof(Utmpx)
LASTLOG_SIZE = ctypes.sizeof(Lastlog)

# ---- UTILITY FUNCTIONS ----

def check_file_access(path):
    if not path.exists():
        print(f"[ERROR] Файл {path} не найден.")
        return False
    if not os.access(path, os.R_OK):
        print(f"[ERROR] Нет прав на чтение файла {path}.")
        return False
    if not os.access(path, os.W_OK):
        print(f"[ERROR] Нет прав на запись файла {path}.")
        return False
    return True

def backup_file(original, backup):
    try:
        original.replace(backup)
        print(f"[INFO] Создана резервная копия {backup}")
    except Exception as e:
        print(f"[ERROR] Не удалось создать резервную копию {original}: {e}")
        sys.exit(1)

# ---- PARSING AND CLEANING ----

def clean_wtmp(bad_hosts):
    if not check_file_access(WTMP_FILE):
        return

    backup_file(WTMP_FILE, WTMP_BAK)

    total_size = WTMP_BAK.stat().st_size
    total_records = total_size // UTMPX_SIZE

    with open(WTMP_BAK, 'rb') as f:
        data = f.read()

    new_data = bytearray()
    for i in range(total_records):
        offset = i * UTMPX_SIZE
        rec_bytes = data[offset:offset+UTMPX_SIZE]
        rec = Utmpx.from_buffer_copy(rec_bytes)
        host = rec.ut_host.decode(errors='ignore').strip('\x00')
        if host in bad_hosts:
            # обнуляем запись
            rec = Utmpx()  # создаём пустую структуру
        new_data += bytes(rec)

    with open(WTMP_FILE, 'wb') as f:
        f.write(new_data)

    if WTMP_BAK.exists():
        WTMP_BAK.unlink()
        print(f"[INFO] Резервная копия {WTMP_BAK} удалена.")

def clean_lastlog(bad_hosts):
    if not check_file_access(LASTLOG_FILE):
        return

    backup_file(LASTLOG_FILE, LASTLOG_BAK)

    total_size = LASTLOG_BAK.stat().st_size
    total_records = total_size // LASTLOG_SIZE

    with open(LASTLOG_BAK, 'rb') as f:
        data = f.read()

    new_data = bytearray()
    for i in range(total_records):
        offset = i * LASTLOG_SIZE
        rec_bytes = data[offset:offset+LASTLOG_SIZE]
        rec = Lastlog.from_buffer_copy(rec_bytes)
        host = rec.ll_host.decode(errors='ignore').strip('\x00')
        if host in bad_hosts:
            rec = Lastlog()  # обнуляем запись
        new_data += bytes(rec)

    with open(LASTLOG_FILE, 'wb') as f:
        f.write(new_data)

    if LASTLOG_BAK.exists():
        LASTLOG_BAK.unlink()
        print(f"[INFO] Резервная копия {LASTLOG_BAK} удалена.")

# ---- MAIN ----

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean wtmp and lastlog by bad hosts")
    parser.add_argument('hosts', nargs='+', help="List of bad hosts to remove")
    args = parser.parse_args()

    print(f"[INFO] UTMPX_SIZE: {UTMPX_SIZE}, LASTLOG_SIZE: {LASTLOG_SIZE}")
    print("[INFO] Начинаем очистку /var/log/wtmp...")
    clean_wtmp(args.hosts)
    print("[INFO] Начинаем очистку /var/log/lastlog...")
    clean_lastlog(args.hosts)
    print("[INFO] Очистка завершена.")
