import zipfile, sys, os, re
src, dst = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(src) as z:
    for info in z.infolist():
        name = info.filename
        if not (info.flag_bits & 0x800):
            try: name = name.encode('cp437').decode('utf-8')
            except Exception: pass
        name = re.sub(r'#U([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1),16)), name)
        if name.endswith('/'): continue
        base = os.path.basename(name)
        folder = os.path.basename(os.path.dirname(name))
        out = os.path.join(dst, folder, base)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out,'wb') as f: f.write(z.read(info))
        print(out, info.file_size)
