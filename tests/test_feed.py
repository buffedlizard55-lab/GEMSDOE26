import json
import requests
import pytest
from gems26.feed import assert_permitted,refresh,ENDPOINTS

@pytest.mark.parametrize('url',['https://www.drivendata.org/','https://api.drivendata.org/x','https://DRIVENDATA.ORG./','http://www.sciencebase.gov/x','https://evil.test/x','https://www.sciencebase.gov.evil.test/x','https://x:secret@www.sciencebase.gov/x'])
def test_no_automatic_competition_or_unknown_access(url):
    with pytest.raises(ValueError):assert_permitted(url)


def test_failures_retain_good_snapshot_and_never_follow_redirects():
    old={'items':{k:{'last_good':{'checked_utc':'2026-01-01T00:00:00Z','title':k}} for k in ENDPOINTS}}
    seen=[]
    def get(url,**kwargs):
        seen.append(url);assert kwargs['allow_redirects'] is False;raise requests.exceptions.SSLError('TLS blocked')
    new=refresh(old,get=get);assert not new['all_refreshes_succeeded'];assert len(seen)==len(ENDPOINTS)
    for k in ENDPOINTS:
        assert new['items'][k]['last_good']==old['items'][k]['last_good'];assert new['items'][k]['status']=='error_last_good_retained'
    assert old['items'][next(iter(ENDPOINTS))]['last_good']['checked_utc']=='2026-01-01T00:00:00Z'


def test_success_schema_and_response_fingerprint():
    class Response:
        status_code=200
        def __init__(self,j):self.j=j;self.content=json.dumps(j).encode()
        def json(self):return self.j
    def get(url,**kwargs):
        if 'sciencebase' in url:return Response({'id':'657e1d85d34e23d3533209f7','title':'GeoDAWN','provenance':{'lastUpdated':'2025-02-28T23:02:25Z'}})
        if 'datacite' in url:return Response({'data':{'id':'10.15121/1881483','attributes':{'doi':'10.15121/1881483','titles':[{'title':'INGENIOUS'}],'updated':'2025-03-07T03:05:37Z'}}})
        return Response({'total':7,'items':[{},{}]})
    new=refresh({},get=get);assert new['all_refreshes_succeeded']
    for row in new['items'].values():assert len(row['last_good']['response_sha256'])==64


def test_redirect_not_a_false_success():
    class Response:status_code=302;content=b''
    assert not refresh({},get=lambda *a,**k:Response())['all_refreshes_succeeded']

@pytest.mark.parametrize('source,data', [('geodawn',{'id':'657e1d85d34e23d3533209f7','title':'x','provenance':None}),('gdr_registry',{'data':None}),('gdr_registry',{'data':{'id':'10.15121/1881483','attributes':{'doi':'10.15121/1881483','titles':[None],'updated':'today'}}})])
def test_schema_failure_preserves_last_good(source,data):
    class Response:
        status_code=200;content=b'{}'
        def json(self):return data
    old={'items':{source:{'last_good':{'checked_utc':'old'}}}}
    new=refresh(old,get=lambda *a,**k:Response())
    assert new['items'][source]['status']=='error_last_good_retained';assert new['items'][source]['last_good']=={'checked_utc':'old'}
