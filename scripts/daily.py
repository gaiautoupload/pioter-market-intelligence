"""One daily run: collect -> export -> discover model -> validated analysis.
No order entry, no automatic website deployment.
"""
import sys, os, json, time
from pathlib import Path
import collect, analyze, equity

def main():
 lock_path=collect.ROOT/'data'/'daily.lock';lock_path.parent.mkdir(exist_ok=True)
 with lock_path.open('a+b') as lock:
  lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
  if os.name=='nt':
   import msvcrt
   try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
   except OSError:raise SystemExit('Another daily run is active')
  else:
   import fcntl
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  snapshot=collect.main()
  try:
   market=equity.main()
   snapshot['equity']={'generated_at':market['generated_at'],'observed_at':market['observed_at'],'stock_count':len(market['stocks']),'strategies':market['strategies']}
   snapshot['strategies']=market['strategies']
   collect.atomic(collect.ROOT/'dist/data/latest.json',snapshot)
  except Exception as exc:
   collect.atomic(collect.ROOT/'data/last-equity-error.json',{'snapshot_id':snapshot['snapshot_id'],'error':str(exc)})
   print('Macro data saved; TWSE equity collection failed: '+str(exc),file=sys.stderr)
  try:analyze.main(snapshot)
  except Exception as exc:
   collect.atomic(collect.ROOT/'data/last-analysis-error.json',{'snapshot_id':snapshot['snapshot_id'],'error':str(exc)})
   print('Data saved; model analysis failed: '+str(exc),file=sys.stderr)
   return 2
 if '--publish' in sys.argv:
  import publish_github
  publish_github.main()
 return 0

if __name__=='__main__':raise SystemExit(main())
