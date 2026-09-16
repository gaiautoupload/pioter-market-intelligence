"""Local-only dashboard with same-origin analysis endpoint. No arbitrary proxy."""
import json, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from collect import ROOT
import analyze
LOCK=threading.Lock()
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT/'dist'),**kwargs)
 def end_headers(self):
  self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store');super().end_headers()
 def reply(self,status,data):
  raw=json.dumps(data,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  if self.path!='/api/analyze':return self.reply(404,{'error':'Not found'})
  if self.headers.get('Host') not in ('127.0.0.1:8765','localhost:8765'):return self.reply(403,{'error':'Invalid host'})
  origin=self.headers.get('Origin')
  if origin and origin not in ('http://127.0.0.1:8765','http://localhost:8765'):return self.reply(403,{'error':'Invalid origin'})
  if self.headers.get('Content-Type')!='application/json':return self.reply(415,{'error':'JSON required'})
  if not LOCK.acquire(blocking=False):return self.reply(409,{'error':'已有分析執行中'})
  try:
   size=int(self.headers.get('Content-Length','0'))
   if size<=0 or size>10000:return self.reply(413,{'error':'Invalid request size'})
   body=json.loads(self.rfile.read(size));snapshot=json.loads((ROOT/'dist/data/latest.json').read_text(encoding='utf-8'))
   if body.get('snapshot_id')!=snapshot['snapshot_id']:return self.reply(409,{'error':'資料已更新，請重新載入頁面'})
   self.reply(200,analyze.main(snapshot))
  except Exception as exc:self.reply(502,{'error':'分析未完成：'+str(exc)})
  finally:LOCK.release()

if __name__=='__main__':
 print('Pioter local server: http://127.0.0.1:8765',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
