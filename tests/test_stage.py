import importlib.util
import pytest
from gems26.common import ROOT

spec=importlib.util.spec_from_file_location('stage_site',ROOT/'scripts/stage_site.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

@pytest.mark.parametrize('dest',[ROOT,ROOT/'.git',ROOT/'.cache',ROOT/'docs'])
def test_refuse_dangerous_staging_destinations(dest):
    with pytest.raises(ValueError):module.stage(dest)

def test_workflow_not_a_scraper_or_competition_uploader():
    text=(ROOT/'.github/workflows/pages.yml').read_text()
    assert 'schedule:' in text;assert 'refresh_source_feed.py' in text;assert 'feed-last-good' in text
    assert 'drivendata.org' not in text;assert 'git push' not in text
    assert 'persist-credentials: false' in text;assert '.cache/pages-site' in text
    assert '--index-url https://download.pytorch.org/whl/cpu' in text


def test_staged_publication_includes_linked_tests_not_private_bulk():
    out=module.stage(ROOT/'.cache/stage-unit-test')
    assert (out/'tests/test_metric.py').is_file()
    assert (out/'data/input_manifest.json').is_file()
    assert not (out/'.git').exists();assert not (out/'data/raw').exists()
    assert not (out/'artifacts').exists();assert not (out/'node_modules').exists()
