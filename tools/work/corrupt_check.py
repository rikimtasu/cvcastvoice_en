import os

f = r"D:\Documents\CVCastingVoice\tools\work\EBOOT.elf"
d = open(f, "rb").read()
print("size:", len(d))
nfffd = d.count(b"\xef\xbf\xbd")
print("U+FFFD occurrences:", nfffd, "(%.2f%%)" % (100.0 * nfffd * 3 / len(d)))
print("header:", d[:0x40].hex(" "))
high = sum(1 for b in d[:100000] if b >= 0x80)
print("high bytes in first 100k:", high)

