import struct

d = open(r"D:\Documents\CVCastingVoice\tools\work\EBOOT_decrypted.elf", "rb").read()
# The ELF header fields that are pure low-bytes survived. Re-read carefully.
print("e_ident:", d[:16].hex(" "))
e_type = struct.unpack_from(">H", d, 0x10)[0]
e_machine = struct.unpack_from(">H", d, 0x12)[0]
print("e_type=0x%x e_machine=0x%x" % (e_type, e_machine))
# e_entry at 0x18 (8 bytes) - high bytes likely corrupted
print("e_entry raw:", d[0x18:0x20].hex(" "))
print("e_phoff raw:", d[0x20:0x28].hex(" "))
print("e_shoff raw:", d[0x28:0x30].hex(" "))
print("e_flags:", d[0x30:0x34].hex(" "))
ehsize = struct.unpack_from(">H", d, 0x34)[0]
phentsize = struct.unpack_from(">H", d, 0x36)[0]
phnum = struct.unpack_from(">H", d, 0x38)[0]
shentsize = struct.unpack_from(">H", d, 0x3A)[0]
shnum = struct.unpack_from(">H", d, 0x3C)[0]
shstrndx = struct.unpack_from(">H", d, 0x3E)[0]
print("ehsize=%d phentsize=%d phnum=%d shentsize=%d shnum=%d shstrndx=%d"
      % (ehsize, phentsize, phnum, shentsize, shnum, shstrndx))
