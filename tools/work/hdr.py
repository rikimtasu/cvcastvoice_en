import struct
d = open(r"D:\Documents\CVCastingVoice\tools\work\EBOOT_decrypted.elf", "rb").read(0x80)
for o in range(0, 0x80, 16):
    print("%04x  %s" % (o, d[o:o + 16].hex(" ")))
