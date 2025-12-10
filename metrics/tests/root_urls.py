from django.urls import get_resolver

def test_root_urls_include_metrics():
    resolver = get_resolver()
    all_url_names = [name for name in resolver.reverse_dict.keys() if isinstance(name, str)]

    assert "system_metrics" in all_url_names
