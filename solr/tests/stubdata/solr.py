# coding=utf-8
"""
solr stubdata
"""

example_solr_response = r'''{
  "responseHeader":{
    "status":0,
    "QTime":3,
    "params":{
      "indent":"true",
      "q":"first_author:\"Sudilovsky\"",
      "wt":"json",
      "rows":"28"}},
  "response":{"numFound":1,"start":0,"docs":[
      {
        "arxiv_class": [
          "Astrophysics - Cosmology and Nongalactic Astrophysics"
        ],
        "alternate_bibcode": [
          "2013arXiv1302.6362S"
        ],
        "identifier": [
          "2013arXiv1302.6362S",
          "2013A&A...552A.143S",
          "10.1051/0004-6361/201321247",
          "arXiv:1302.6362",
          "2013arXiv1302.6362S",
          "10.1051/0004-6361/201321247"
        ],
        "pubdate": "2013-04-00",
        "first_author": "Sudilovsky, V.",
        "abstract": "There is evidence of an overdensity of strong intervening MgII absorption line systems distributed along the lines of sight toward gamma-ray burst (GRB) afterglows relative to quasar sight-lines. If this excess is real, one should also expect an overdensity of field galaxies around GRB sight-lines, as strong MgII tends to trace these sources. In this work, we test this expectation by calculating the two point angular correlation function of galaxies within 120'' (~470 h<SUP>-1</SUP><SUB>71</SUB> Kpc at ⟨ z ⟩ ~ 0.4) of GRB afterglows. We compare the gamma-ray burst optical and near-infrared detector (GROND) GRB afterglow sample - one of the largest and most homogeneous samples of GRB fields - with galaxies and active galactic nuclei found in the COSMOS-30 photometric catalog. We find no significant signal of anomalous clustering of galaxies at an estimated median redshift of z ~ 0.3 around GRB sight-lines, down to K<SUB>AB</SUB> 〈 19.3. This result is contrary to the expectations from the MgII excess derived from GRB afterglow spectroscopy, although many confirmed galaxy counterparts to MgII absorbers may be too faint to detect in our sample - especially those at z 〉 1. We note that the addition of higher sensitivity Spitzer/IRAC or HST/WFC3 data for even a subset of our sample would increase this survey's depth by several orders of magnitude, simultaneously increasing statistics and enabling the investigation of a much larger redshift space.Table 1 is available in electronic form at <A href=\"http://www.aanda.org\">http://www.aanda.org</A>",
        "citation": [
          "2013A&A...556A..23E"
        ],
        "links_data": [
          "{\"title\":\"\", \"type\":\"preprint\", \"instances\":\"\", \"access\":\"open\"}",
          "{\"title\":\"\", \"type\":\"ned\", \"instances\":\"85\", \"access\":\"\"}",
          "{\"title\":\"\", \"type\":\"postscript\", \"instances\":\"\", \"access\":\"\"}",
          "{\"title\":\"\", \"type\":\"electr\", \"instances\":\"\", \"access\":\"open\"}",
          "{\"title\":\"\", \"type\":\"simbad\", \"instances\":\"74\", \"access\":\"\"}",
          "{\"title\":\"\", \"type\":\"pdf\", \"instances\":\"\", \"access\":\"open\"}"
        ],
        "read_count": 7,
        "doctype": "article",
        "first_author_norm": "Sudilovsky, V",
        "keyword_norm": [
          "gamma rays",
          "galaxies statistics",
          "-"
        ],
        "year": "2013",
        "id": "1989757",
        "recid": 1989757,
        "simbid": [
          2419335,
          3748384,
          3897892,
          4029905,
          4071640,
          4087910,
          4091155,
          4091849,
          4145163,
          4166887,
          4166893,
          4166896,
          4167217,
          4478702,
          4503059,
          4503067,
          4536382,
          4551567,
          4551571,
          4686319,
          4686331,
          4694762,
          4843017,
          4843147,
          4865002,
          4904765,
          4946650,
          4981687,
          4981909,
          4981958,
          4983018,
          4983019,
          4985338,
          4986069,
          5133621,
          5133623,
          5150122,
          5150194,
          5186455,
          5261857,
          5268009,
          5278461,
          5344125,
          5348414,
          5374459,
          5451933,
          5473226,
          5541212,
          5549409,
          5549644,
          5551748,
          5653701,
          6170431,
          6173855,
          6178869,
          6297519,
          6328439,
          6328447,
          6328941,
          6328943,
          6328944,
          6339494,
          6340031,
          6341924,
          6344974,
          6356206,
          6356273,
          6366816,
          6939035,
          7809493,
          7881243,
          7884930,
          7945460,
          7945464
        ],
        "bibcode": "2013A&A...552A.143S",
        "classic_factor": 3891,
        "reference": [
          "1977ApJ...217..385G",
          "1980lssu.book.....P",
          "1984A&A...132..389P",
          "1993ApJ...412...64L",
          "1994ApJ...429..582C",
          "1995AJ....110.1316B",
          "1995AJ....110.2519S",
          "1995ApJ...441L..39B",
          "1996A&AS..117..393B",
          "1998PASP..110..863P",
          "1999MNRAS.310..540A",
          "2000ApJ...543..577C",
          "2002ApJ...575..587B",
          "2004ApJ...614...84B",
          "2005MNRAS.362..245J",
          "2006A&A...457..841I",
          "2006ApJ...642...63L",
          "2006ApJ...642..636L",
          "2006ApJ...648...95P",
          "2006ApJ...648L..93P",
          "2006MNRAS.371..495B",
          "2006PASP..118.1711W",
          "2007Ap&SS.312..325F",
          "2007ApJ...659..218P",
          "2007ApJ...669..741S",
          "2007ApJ...671..622T",
          "2008ApJ...679.1144L",
          "2008PASP..120..405G",
          "2009A&A...503..771V",
          "2009ApJ...690.1236I",
          "2009ApJ...690.1250S",
          "2009ApJ...691..152C",
          "2009ApJ...691..182S",
          "2009ApJ...697..345C",
          "2009ApJ...697.1634R",
          "2009ApJ...699...56S",
          "2009hst..prop12307L",
          "2009hst..prop12378L",
          "2010ApJ...711..495B",
          "2010ApJ...720.1513K",
          "2010RAA....10..533W",
          "2011A&A...526A..30G",
          "2011A&A...534A.108K",
          "2011ApJ...742...61S",
          "2011ApJ...743...10B",
          "2011ApJ...743L..34K",
          "2011MNRAS.414..209W",
          "2012A&A...539A.113E",
          "2012A&A...542A.103B",
          "2012A&A...546A..20S",
          "2012ApJ...749...68S",
          "2012ApJ...752...62J",
          "2012ApJ...754...46T",
          "2012ApJ...754..139R",
          "2012ApJ...761..112M",
          "2012MNRAS.419.3553L",
          "2012MNRAS.421.1671B",
          "2012arXiv1211.6215Z",
          "2012arXiv1211.6528C",
          "2012sptz.prop90062P",
          "2013ApJ...764....9M",
          "2013arXiv1301.5903P"
        ],
        "aff": [
          "Max-Planck-Institut für extraterrestrische Physik, Giessenbachstrasse, 85748, Garching bei München, Germany",
          "Max-Planck-Institut für extraterrestrische Physik, Giessenbachstrasse, 85748, Garching bei München, Germany",
          "Max-Planck-Institut für extraterrestrische Physik, Giessenbachstrasse, 85748, Garching bei München, Germany",
          "Max-Planck-Institut für extraterrestrische Physik, Giessenbachstrasse, 85748, Garching bei München, Germany",
          "Max-Planck-Institut für extraterrestrische Physik, Giessenbachstrasse, 85748, Garching bei München, Germany",
          "GEPI, Observatoire de Paris, CNRS, Univ. Paris Diderot, 5 place Jules Jannsen, 92195, Meudon, France; INAF, Osservatorio Astronomico di Brera, via E. Bianchi 46, 23807, Merate, Italy",
          "Max-Planck-Institut für extraterrestrische Physik, Giessenbachstrasse, 85748, Garching bei München, Germany",
          "Max-Planck-Institut für extraterrestrische Physik, Giessenbachstrasse, 85748, Garching bei München, Germany",
          "Dark Cosmology Centre, Niels Bohr Institute, University of Copenhagen, Juliane Maries Vej 30, 2100, Copenhagen, Denmark",
          "Thüringer Landessternwarte Tautenburg, Sternwarte 5, 07778, Tautenburg, Germany",
          "Thüringer Landessternwarte Tautenburg, Sternwarte 5, 07778, Tautenburg, Germany",
          "Thüringer Landessternwarte Tautenburg, Sternwarte 5, 07778, Tautenburg, Germany",
          "Institute of Experimental and Applied Physics, Czech Technical University in Prague, Horská 3a/22, 128 00, Prague 2, Czech Republic",
          "Thüringer Landessternwarte Tautenburg, Sternwarte 5, 07778, Tautenburg, Germany"
        ],
        "keyword_schema": [
          "Astronomy",
          "Astronomy",
          "arXiv"
        ],
        "reader": [
            "these are the readers"
        ],
        "keyword_facet": [
          "gamma rays",
          "galaxies statistics"
        ],
        "pub_raw": "Astronomy & Astrophysics, Volume 552, id.A143, <NUMPAGES>8</NUMPAGES> pp.",
        "body": "this is the fulltext",
        "simbtype": [
          "Other",
          "Star"
        ],
        "simbad_object_facet_hier": [
          "0/Other",
          "1/Other/2419335",
          "0/Other",
          "1/Other/3748384",
          "0/Other",
          "1/Other/3897892",
          "0/Other",
          "1/Other/4029905",
          "0/Other",
          "1/Other/4071640",
          "0/Other",
          "1/Other/4087910",
          "0/Other",
          "1/Other/4091155",
          "0/Other",
          "1/Other/4091849",
          "0/Other",
          "1/Other/4145163",
          "0/Other",
          "1/Other/4166887",
          "0/Other",
          "1/Other/4166893",
          "0/Other",
          "1/Other/4166896",
          "0/Other",
          "1/Other/4167217",
          "0/Other",
          "1/Other/4478702",
          "0/Other",
          "1/Other/4503059",
          "0/Other",
          "1/Other/4503067",
          "0/Other",
          "1/Other/4536382",
          "0/Other",
          "1/Other/4551567",
          "0/Other",
          "1/Other/4551571",
          "0/Other",
          "1/Other/4686319",
          "0/Other",
          "1/Other/4686331",
          "0/Other",
          "1/Other/4694762",
          "0/Other",
          "1/Other/4843017",
          "0/Other",
          "1/Other/4843147",
          "0/Other",
          "1/Other/4865002",
          "0/Other",
          "1/Other/4904765",
          "0/Other",
          "1/Other/4946650",
          "0/Other",
          "1/Other/4981687",
          "0/Other",
          "1/Other/4981909",
          "0/Other",
          "1/Other/4981958",
          "0/Other",
          "1/Other/4983018",
          "0/Other",
          "1/Other/4983019",
          "0/Other",
          "1/Other/4985338",
          "0/Other",
          "1/Other/4986069",
          "0/Other",
          "1/Other/5133621",
          "0/Other",
          "1/Other/5133623",
          "0/Other",
          "1/Other/5150122",
          "0/Other",
          "1/Other/5150194",
          "0/Other",
          "1/Other/5186455",
          "0/Other",
          "1/Other/5261857",
          "0/Other",
          "1/Other/5268009",
          "0/Other",
          "1/Other/5278461",
          "0/Other",
          "1/Other/5344125",
          "0/Other",
          "1/Other/5348414",
          "0/Other",
          "1/Other/5374459",
          "0/Other",
          "1/Other/5451933",
          "0/Other",
          "1/Other/5473226",
          "0/Other",
          "1/Other/5541212",
          "0/Star",
          "1/Star/5549409",
          "0/Other",
          "1/Other/5549644",
          "0/Other",
          "1/Other/5551748",
          "0/Other",
          "1/Other/5653701",
          "0/Other",
          "1/Other/6170431",
          "0/Other",
          "1/Other/6173855",
          "0/Other",
          "1/Other/6178869",
          "0/Other",
          "1/Other/6297519",
          "0/Other",
          "1/Other/6328439",
          "0/Other",
          "1/Other/6328447",
          "0/Other",
          "1/Other/6328941",
          "0/Other",
          "1/Other/6328943",
          "0/Other",
          "1/Other/6328944",
          "0/Other",
          "1/Other/6339494",
          "0/Other",
          "1/Other/6340031",
          "0/Other",
          "1/Other/6341924",
          "0/Other",
          "1/Other/6344974",
          "0/Other",
          "1/Other/6356206",
          "0/Other",
          "1/Other/6356273",
          "0/Other",
          "1/Other/6366816",
          "0/Other",
          "1/Other/6939035",
          "0/Other",
          "1/Other/7809493",
          "0/Other",
          "1/Other/7881243",
          "0/Other",
          "1/Other/7884930",
          "0/Other",
          "1/Other/7945460",
          "0/Other",
          "1/Other/7945464"
        ],
        "pub": "Astronomy and Astrophysics",
        "volume": "552",
        "author_norm": [
          "Sudilovsky, V",
          "Greiner, J",
          "Rau, A",
          "Salvato, M",
          "Savaglio, S",
          "Vergani, S",
          "Schady, P",
          "Elliott, J",
          "Kruehler, T",
          "Kann, D",
          "Klose, S",
          "Rossi, A",
          "Filgas, R",
          "Schmidl, S"
        ],
        "date": "2013-04-01T00:00:00Z",
        "data": [
          "CDS",
          "NED"
        ],
        "doi": [
          "10.1051/0004-6361/201321247"
        ],
        "keyword": [
          "gamma-ray burst: general",
          "galaxies: statistics",
          "Astrophysics - Cosmology and Nongalactic Astrophysics"
        ],
        "database": [
          "astronomy"
        ],
        "ack": "We thank the anonymous referee for his or her helpful comments. We thank Sotoria Fotopoulou for insightful discussion regarding photometric calibration techniques, and David Gruber for his projection plotting routine. S.K., D.A.K., and A.R. acknowledge support by DFG grant Kl 766/16-1. S.S. acknowledges support through project M.FE.A.Ext 00003 of the MPG, and P.S. acknowledges support by DFG grant SA 2001/1-1. T.K. acknowledges support by the European Commission under the Marie Curie Intra-European Fellowship Programme. The Dark Cosmology Centre is funded by the Danish National Research Foundation.",
        "author": [
          "Sudilovsky, V.",
          "Greiner, J.",
          "Rau, A.",
          "Salvato, M.",
          "Savaglio, S.",
          "Vergani, S. D.",
          "Schady, P.",
          "Elliott, J.",
          "Krühler, T.",
          "Kann, D. A.",
          "Klose, S.",
          "Rossi, A.",
          "Filgas, R.",
          "Schmidl, S."
        ],
        "citation_count": 1,
        "email": [
          "vsudilov@mpe.mpg.de",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-"
        ],
        "cite_read_boost": 0.46,
        "eid": "A143",
        "orcid": [
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-",
          "-"
        ],
        "title": [
          "Clustering of galaxies around gamma-ray burst sight-lines"
        ],
        "property": [
          "OPENACCESS",
          "REFEREED",
          "EPRINT_OPENACCESS",
          "PUB_OPENACCESS",
          "ARTICLE"
        ],
        "page": [
          "A143"
        ],
        "_version_": 1506683556413309000,
        "indexstamp": "2015-07-14T14:50:04.718Z"
      },
      {
        "alternate_bibcode": [
          "2012PoS...152E..92S"
        ],
        "identifier": [
          "2012PoS...152E..92S",
          "2012PoS...152E..92S",
          "2012grb..confE..92S"
        ],
        "pubdate": "2012-00-00",
        "first_author": "Sudilovsky, V.",
        "pub": "-Ray Bursts 2012 Conference (GRB 2012)",
        "citation_count": 0,
        "first_author_norm": "Sudilovsky, V",
        "author_norm": [
          "Sudilovsky, V"
        ],
        "year": "2012",
        "date": "2012-01-01T00:00:00Z",
        "id": "1958231",
        "recid": 1958231,
        "page": [
          "92"
        ],
        "bibcode": "2012grb..confE..92S",
        "classic_factor": 0,
        "author": [
          "Sudilovsky, V."
        ],
        "aff": [
          "-"
        ],
        "database": [
          "astronomy"
        ],
        "doctype": "inproceedings",
        "read_count": 0,
        "pub_raw": "Proceedings of the Gamma-Ray Bursts 2012 Conference (GRB 2012). May 7-11, 2012. Munich, Germany. Published online at <A href=\"http://pos.sissa.it/cgi-bin/reader/conf.cgi?confid=152\">http://pos.sissa.it/cgi-bin/reader/conf.cgi?confid=152</A>, id.92",
        "cite_read_boost": 0.07,
        "eid": "92",
        "orcid": [
          "-"
        ],
        "title": [
          "Clustering of galaxies near GRB afterglows"
        ],
        "property": [
          "ARTICLE",
          "NOT REFEREED"
        ],
        "email": [
          "-"
        ],
        "_version_": 1506594082227486700,
        "indexstamp": "2015-07-13T15:08:00.949Z"
      },
      {
        "alternate_bibcode": [
          "2012GCN.13048....1S"
        ],
        "identifier": [
          "2012GCN.13048....1S",
          "2012GCN.13048....1S",
          "2012GCN..13048...1S"
        ],
        "simbtype": [
          "Other"
        ],
        "pubdate": "2012-00-00",
        "citation_count": 0,
        "first_author": "Sudilovsky, V.",
        "simbad_object_facet_hier": [
          "0/Other",
          "1/Other/6356273"
        ],
        "links_data": [
          "{\"title\":\"\", \"type\":\"simbad\", \"instances\":\"1\", \"access\":\"\"}",
          "{\"title\":\"\", \"type\":\"electr\", \"instances\":\"\", \"access\":\"\"}"
        ],
        "pub": "GRB Coordinates Network",
        "volume": "13048",
        "date": "2012-01-01T00:00:00Z",
        "author_norm": [
          "Sudilovsky, V",
          "Prinz, T",
          "Greiner, J"
        ],
        "year": "2012",
        "first_author_norm": "Sudilovsky, V",
        "data": [
          "CDS"
        ],
        "id": "1954472",
        "recid": 1954472,
        "simbid": [
          6356273
        ],
        "bibcode": "2012GCN..13048...1S",
        "classic_factor": 0,
        "author": [
          "Sudilovsky, V.",
          "Prinz, T.",
          "Greiner, J."
        ],
        "aff": [
          "-",
          "-",
          "-"
        ],
        "database": [
          "astronomy"
        ],
        "doctype": "newsletter",
        "read_count": 0,
        "pub_raw": "GRB Coordinates Network, Circular Service, 13048, 1 (2012)",
        "cite_read_boost": 0.22,
        "orcid": [
          "-",
          "-",
          "-"
        ],
        "title": [
          "GROND observations of GRB 120311A."
        ],
        "page": [
          "1"
        ],
        "property": [
          "NONARTICLE",
          "NOT REFEREED"
        ],
        "email": [
          "-",
          "-",
          "-"
        ],
        "_version_": 1506594074582319000,
        "indexstamp": "2015-07-13T15:07:54.122Z"
      },
      {
        "alternate_bibcode": [
          "2012GCN.13098....1S"
        ],
        "identifier": [
          "2012GCN.13098....1S",
          "2012GCN.13098....1S",
          "2012GCN..13098...1S"
        ],
        "simbtype": [
          "Other"
        ],
        "pubdate": "2012-00-00",
        "citation_count": 0,
        "first_author": "Sudilovsky, V.",
        "simbad_object_facet_hier": [
          "0/Other",
          "1/Other/6367520"
        ],
        "links_data": [
          "{\"title\":\"\", \"type\":\"simbad\", \"instances\":\"1\", \"access\":\"\"}",
          "{\"title\":\"\", \"type\":\"electr\", \"instances\":\"\", \"access\":\"\"}"
        ],
        "pub": "GRB Coordinates Network",
        "volume": "13098",
        "date": "2012-01-01T00:00:00Z",
        "author_norm": [
          "Sudilovsky, V",
          "Guelbenzu, A",
          "Greiner, J"
        ],
        "year": "2012",
        "first_author_norm": "Sudilovsky, V",
        "data": [
          "CDS"
        ],
        "id": "1954502",
        "recid": 1954502,
        "simbid": [
          6367520
        ],
        "bibcode": "2012GCN..13098...1S",
        "author": [
          "Sudilovsky, V.",
          "Guelbenzu, A. N.",
          "Greiner, J."
        ],
        "aff": [
          "-",
          "-",
          "-"
        ],
        "database": [
          "astronomy"
        ],
        "doctype": "newsletter",
        "read_count": 0,
        "pub_raw": "GRB Coordinates Network, Circular Service, 13098, 1 (2012)",
        "orcid": [
          "-",
          "-",
          "-"
        ],
        "title": [
          "GRB 120324A: GROND observations."
        ],
        "page": [
          "1"
        ],
        "property": [
          "NONARTICLE",
          "NOT REFEREED"
        ],
        "email": [
          "-",
          "-",
          "-"
        ],
        "_version_": 1506594074801471500,
        "indexstamp": "2015-07-13T15:07:54.361Z"
      },
      {
        "alternate_bibcode": [
          "2012GCN.13506....1S"
        ],
        "identifier": [
          "2012GCN.13506....1S",
          "2012GCN.13506....1S",
          "2012GCN..13506...1S"
        ],
        "simbtype": [
          "Other"
        ],
        "pubdate": "2012-00-00",
        "citation_count": 0,
        "first_author": "Sudilovsky, V.",
        "simbad_object_facet_hier": [
          "0/Other",
          "1/Other/7836246"
        ],
        "links_data": [
          "{\"title\":\"\", \"type\":\"simbad\", \"instances\":\"1\", \"access\":\"\"}",
          "{\"title\":\"\", \"type\":\"electr\", \"instances\":\"\", \"access\":\"\"}"
        ],
        "pub": "GRB Coordinates Network",
        "volume": "13506",
        "date": "2012-01-01T00:00:00Z",
        "author_norm": [
          "Sudilovsky, V",
          "Kann, D",
          "Greiner, J"
        ],
        "year": "2012",
        "first_author_norm": "Sudilovsky, V",
        "data": [
          "CDS"
        ],
        "id": "1954903",
        "recid": 1954903,
        "simbid": [
          7836246
        ],
        "bibcode": "2012GCN..13506...1S",
        "classic_factor": 0,
        "author": [
          "Sudilovsky, V.",
          "Kann, D. A.",
          "Greiner, J."
        ],
        "aff": [
          "-",
          "-",
          "-"
        ],
        "database": [
          "astronomy"
        ],
        "doctype": "newsletter",
        "read_count": 0,
        "pub_raw": "GRB Coordinates Network, Circular Service, 13506, 1 (2012)",
        "cite_read_boost": 0.11,
        "orcid": [
          "-",
          "-",
          "-"
        ],
        "title": [
          "GRB 120722A: GROND detection of the afterglow."
        ],
        "page": [
          "1"
        ],
        "property": [
          "NONARTICLE",
          "NOT REFEREED"
        ],
        "email": [
          "-",
          "-",
          "-"
        ],
        "_version_": 1506594075721072600,
        "indexstamp": "2015-07-13T15:07:55.235Z"
      },
      {
        "alternate_bibcode": [
          "2012GCN.13729....1S"
        ],
        "identifier": [
          "2012GCN.13729....1S",
          "2012GCN.13729....1S",
          "2012GCN..13729...1S"
        ],
        "simbtype": [
          "Other"
        ],
        "pubdate": "2012-00-00",
        "citation_count": 0,
        "first_author": "Sudilovsky, V.",
        "simbad_object_facet_hier": [
          "0/Other",
          "1/Other/7839082"
        ],
        "links_data": [
          "{\"title\":\"\", \"type\":\"simbad\", \"instances\":\"1\", \"access\":\"\"}",
          "{\"title\":\"\", \"type\":\"electr\", \"instances\":\"\", \"access\":\"\"}"
        ],
        "pub": "GRB Coordinates Network",
        "volume": "13729",
        "date": "2012-01-01T00:00:00Z",
        "author_norm": [
          "Sudilovsky, V",
          "Schmidl, S",
          "Kann, D",
          "Greiner, J"
        ],
        "year": "2012",
        "first_author_norm": "Sudilovsky, V",
        "data": [
          "CDS"
        ],
        "id": "1955155",
        "recid": 1955155,
        "simbid": [
          7839082
        ],
        "bibcode": "2012GCN..13729...1S",
        "classic_factor": 0,
        "author": [
          "Sudilovsky, V.",
          "Schmidl, S.",
          "Kann, D. A.",
          "Greiner, J."
        ],
        "aff": [
          "-",
          "-",
          "-",
          "-"
        ],
        "database": [
          "astronomy"
        ],
        "doctype": "newsletter",
        "read_count": 0,
        "pub_raw": "GRB Coordinates Network, Circular Service, 13729, 1 (2012)",
        "cite_read_boost": 0.07,
        "orcid": [
          "-",
          "-",
          "-",
          "-"
        ],
        "title": [
          "GRB 120909A: GROND detection of the afterglow."
        ],
        "page": [
          "1"
        ],
        "property": [
          "NONARTICLE",
          "NOT REFEREED"
        ],
        "email": [
          "-",
          "-",
          "-",
          "-"
        ],
        "_version_": 1506594076188737500,
        "indexstamp": "2015-07-13T15:07:55.666Z"
      },
      {
        "alternate_bibcode": [
          "2012GCN.13129....1S"
        ],
        "identifier": [
          "2012GCN.13129....1S",
          "2012GCN.13129....1S",
          "2012GCN..13129...1S"
        ],
        "simbad_object_facet_hier": [
          "0/Other",
          "1/Other/6368272"
        ],
        "simbtype": [
          "Other"
        ],
        "pubdate": "2012-00-00",
        "citation_count": 1,
        "first_author": "Sudilovsky, V.",
        "citation": [
          "2014A&A...564A..38D"
        ],
        "links_data": [
          "{\"title\":\"\", \"type\":\"simbad\", \"instances\":\"1\", \"access\":\"\"}",
          "{\"title\":\"\", \"type\":\"electr\", \"instances\":\"\", \"access\":\"\"}"
        ],
        "pub": "GRB Coordinates Network",
        "volume": "13129",
        "date": "2012-01-01T00:00:00Z",
        "author_norm": [
          "Sudilovsky, V",
          "Nicuesa Guelbenzu, A",
          "Greiner, J"
        ],
        "year": "2012",
        "first_author_norm": "Sudilovsky, V",
        "data": [
          "CDS"
        ],
        "id": "1954617",
        "recid": 1954617,
        "simbid": [
          6368272
        ],
        "bibcode": "2012GCN..13129...1S",
        "classic_factor": 3495,
        "author": [
          "Sudilovsky, V.",
          "Nicuesa Guelbenzu, A.",
          "Greiner, J."
        ],
        "aff": [
          "-",
          "-",
          "-"
        ],
        "database": [
          "astronomy"
        ],
        "doctype": "newsletter",
        "read_count": 0,
        "pub_raw": "GRB Coordinates Network, Circular Service, 13129, 1 (2012)",
        "cite_read_boost": 0.14,
        "orcid": [
          "-",
          "-",
          "-"
        ],
        "title": [
          "GROND observations of GRB 120327A."
        ],
        "page": [
          "1"
        ],
        "property": [
          "NONARTICLE",
          "NOT REFEREED"
        ],
        "email": [
          "-",
          "-",
          "-"
        ],
        "_version_": 1506594075067809800,
        "indexstamp": "2015-07-13T15:07:54.636Z"
      }
    ]
  }}
'''

