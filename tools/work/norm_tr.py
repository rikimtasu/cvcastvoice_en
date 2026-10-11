import io,json,sys,re,os
w=os.environ.get('CVC_CWD') or os.path.dirname(os.path.abspath(__file__))+os.sep
n=int(sys.argv[1])
sp=chr(0x3000)
b=json.loads(io.open(w+'batches/batch_%04d.json'%n,encoding='utf-8').read())
lines=[L for L in io.open(w+'tr/b%04d.txt'%n,encoding='utf-8').read().splitlines() if L.strip()]
out=[]
for L in lines:
    i,e=L.split('|',1)
    e=re.sub(chr(0x300c),chr(34),e); e=re.sub(chr(0x300d),chr(34),e)
    e=re.sub(chr(0x300e),chr(34),e); e=re.sub(chr(0x300f),chr(34),e)
    e=re.sub(chr(0xff08),chr(40),e); e=re.sub(chr(0xff09),chr(41),e)
    e=re.sub(chr(0xff5e),chr(126),e); e=re.sub(chr(0x2026),chr(46)*3,e)
    e=re.sub(chr(0x2019),chr(39),e); e=re.sub(chr(0x2018),chr(39),e)
    e=re.sub(chr(0x201c),chr(34),e); e=re.sub(chr(0x201d),chr(34),e)
    e=re.sub(chr(0x2015),chr(45)*2,e); e=re.sub(chr(0x2014),chr(45)*2,e)
    e=re.sub(chr(0x301c),chr(126),e)
    e=re.sub('[^\x00-\x7f]','',e)
    want=b[i]['jp'].startswith(sp)
    e=e.lstrip(' ')
    if want: e=' '+e
    out.append(i+'|'+e)
io.open(w+'tr/b%04d.txt'%n,'w',encoding='utf-8',newline='\n').write('\n'.join(out)+'\n')
print('norm',n,len(out))
