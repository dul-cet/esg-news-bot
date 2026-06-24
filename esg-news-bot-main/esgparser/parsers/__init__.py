from .esgnews import Parse_EsgnewscomRuNews, Parse_EsgnewscomEnNews
from .govkz import Parse_GovkznewsRu, Parse_GovkznewsKz
from .informkz import Parse_informkzRuNews
from .newsapi import Parse_NewsAPI_ESG
from .tengrinews import Parse_Tengrinews
from .rssfeeds import Parse_RSSFeeds
from .generic_site import Parse_GenericSite
from .esgworld import ESGWorldParser

__all__ = [
    'Parse_EsgnewscomRuNews',
    'Parse_EsgnewscomEnNews',
    'Parse_GovkznewsRu',
    'Parse_GovkznewsKz',
    'Parse_informkzRuNews',
    'Parse_NewsAPI_ESG',
    'Parse_Tengrinews',
    'Parse_RSSFeeds',
    'Parse_GenericSite',
]
