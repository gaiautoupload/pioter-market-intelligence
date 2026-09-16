"""One daily run: collect -> export -> discover model -> validated analysis.
No order entry, no automatic website deployment.
"""
import sys, os, json, time
from pathlib import Path
import collect, analyze

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
  try:analyze.main(snapshot)
  except Exception as exc:
   collect.atomic(collect.ROOT/'data/last-analysis-error.json',{'snapshot_id':snapshot['snapshot_id'],'error':str(exc)})
   print('Data saved; model analysis failed: '+str(exc),file=sys.stderr)
   return 2
 return 0

if __name__=='__main__':raise SystemExit(main())
