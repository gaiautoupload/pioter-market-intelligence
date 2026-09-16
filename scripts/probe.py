import urllib.request, json, concurrent.futures, pathlib
URLS={
'taifex':'https://openapi.taifex.com.tw/swagger.json',
'twse':'https://openapi.twse.com.tw/v1/swagger.json',
'hkibor':'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/hk-interbank-ir-daily?segment=hibor.fixing&pagesize=3',
'hkfx':'https://api.hkma.gov.hk/public/market-data-and-statistics/monthly-statistical-bulletin/er-ir/er-eeri-daily?pagesize=3',
'futures':'https://openapi.taifex.com.tw/v1/DailyMarketReportFut',
'pcr':'https://openapi.taifex.com.tw/v1/PutCallRatio',
'institution':'https://openapi.taifex.com.tw/v1/MarketDataOfMajorInstitutionalTradersDividedByFuturesAndOptionsBytheDate',
'spot':'https://www.twse.com.tw/fund/BFI82U?response=json',
}
def run(item):
 k,u=item
 try:
  raw=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'PioterResearch/1.0'}),timeout=30).read(); d=json.loads(raw)
  pathlib.Path('probe').mkdir(exist_ok=True); pathlib.Path('probe',k+'.json').write_bytes(raw)
  if 'paths' in d: d={p:v.get('get',{}).get('summary') for p,v in d['paths'].items()}
  elif isinstance(d,list): d={'count':len(d),'sample':d[:2]}
  return k,d
 except Exception as e:return k,str(e)
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 for k,d in pool.map(run,URLS.items()):print(k,json.dumps(d,ensure_ascii=False)[:14000])
