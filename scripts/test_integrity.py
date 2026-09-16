import unittest, json
from datetime import timedelta
import collect, analyze

class IntegrityTests(unittest.TestCase):
 def test_missing_is_not_zero(self):
  for value in [None,'-','NULL',float('nan')]:
   with self.assertRaises((ValueError,TypeError)):collect.number(value)
  self.assertEqual(collect.number('0'),0)
 def test_future_excluded_and_basis_points(self):
  today=collect.TODAY
  m=collect.metric('us10','10Y','global','%',[(str(today-timedelta(days=1)),4.96),(str(today),4.97),(str(today+timedelta(days=1)),10)],'treasury','close',change_kind='bp')
  self.assertEqual(m['value'],4.97);self.assertEqual(m['delta'],1)
 def test_stale_is_explicit(self):
  m=collect.metric('vix','VIX','global','index',[(str(collect.TODAY-timedelta(days=12)),20)],'vix','close')
  self.assertEqual(m['status'],'stale')
 def test_borrowing_schema_mismatch_rejected(self):
  with self.assertRaises(ValueError):collect.parse('lending',json.dumps({'stat':'OK','fields':['changed'],'data':[]}).encode())
 def test_foreign_contract_filter(self):
  rows=[{'Date':collect.TODAY.strftime('%Y%m%d'),'ContractCode':'臺股期貨','Item':'外資及陸資','OpenInterest(Long)':'100','OpenInterest(Short)':'200','OpenInterest(Net)':'-100'}, {'Date':collect.TODAY.strftime('%Y%m%d'),'ContractCode':'小型臺指期貨','Item':'外資及陸資','OpenInterest(Long)':'900','OpenInterest(Short)':'0','OpenInterest(Net)':'900'}]
  result=collect.parse('foreign',json.dumps(rows).encode());self.assertEqual(next(m['value'] for m in result if m['id']=='foreign_net'),-100)
 def test_real_snapshot_semantics(self):
  s=json.loads((collect.ROOT/'dist/data/latest.json').read_text(encoding='utf8'));m={m['id']:m for m in s['metrics']}
  self.assertEqual(len(m),len(s['metrics']))
  if all(m[k]['value'] is not None for k in ['foreign_long','foreign_short','foreign_net']):self.assertAlmostEqual(m['foreign_long']['value']-m['foreign_short']['value'],m['foreign_net']['value'])
  if all(m[k]['value'] is not None for k in ['pcr','put_oi','call_oi']):self.assertAlmostEqual(m['put_oi']['value']/m['call_oi']['value']*100,m['pcr']['value'],places=2)
  for item in s['metrics']:
   if item['value'] is not None:self.assertTrue(item['source_url']);self.assertLessEqual(item['observed_at'],str(collect.TODAY))
 def test_model_cannot_invent_evidence(self):
  result={'summary':{'international_capital':'Unknown','taiwan_capital':'Unknown','systemic_risk':'Unknown','one_line':'test'},'short_term':dict.fromkeys(['direction','base_scenario','risk_scenario','bullish_trigger','bearish_trigger'],'test'),'medium_term':dict.fromkeys(['direction','base_scenario','risk_scenario','bullish_trigger','bearish_trigger'],'test'),'evidence':[{'metric_id':'fake','value':9,'observed_at':str(collect.TODAY)}],'divergences':[],'missing_data':[],'stocks':[]}
  with self.assertRaises(ValueError):analyze.validate(result,{'metrics':[],'strategies':[]})
 def test_exaggerated_model_claim_is_flagged(self):
  result={'summary':{'one_line':'殖利率急升'},'evidence':[],'short_term':{'bullish_trigger':'50以上','bearish_trigger':'下跌'},'medium_term':{'bullish_trigger':'上升','bearish_trigger':'下跌'}}
  self.assertEqual(analyze.flag_review(result)['review_status'],'needs_review')

if __name__=='__main__':unittest.main()
