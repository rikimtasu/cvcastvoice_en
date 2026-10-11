import json,sys
b=int(sys.argv[1])
src=json.load(open(f'batches/batch_{b:04d}.json',encoding='utf-8'))
for k in sorted(src,key=lambda x:int(x)):
    jp=src[k]['jp']
    flag='L' if jp.startswith('\u3000') else 'N'
    print(f"{k}|{src[k]['b']}|{flag}|{jp.replace(chr(0x3000),'[I]')}")
