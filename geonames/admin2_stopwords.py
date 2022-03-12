import re


def trim_stopwords(s, stop_words):
    """Case-insensitive removal of stop phrases/words from a string
    >>> trim_stopwords('Depártment de Testing Test royale', ['depártment de', 'royale'])
    'Testing Test'
    """
    for stop in stop_words:
        if ' ' in stop:  # phrase
            s = re.sub(stop, '', s, flags=re.IGNORECASE)
        else:  # individual word
            s = s.split()
            for i, w in enumerate(s):
                if w.lower() == stop:
                    s.pop(i)
            s = ' '.join(s)
    return s.strip()


admin2_stopwords = [
    # with space
    'administrative okrug', 'administrativnyy okrug', 'gorodskoy okrug', 'urban okrug',
    'caza de', 'caza du', 'cercle de',
    'city council', 'commune of', 'daïra de', 'daïra d’', 'departamento de', 'departamento del',
    'distrito de', 'gradska četvrt', 'komissarov rayon', 'komuna e',
    'municipio de', 'municipiul provincia de', 'partido de', 'politischer bezirk',
    'province of', 'rrethi i', 'urban district', 'ward of',
    # join words
    'and', 'with', 'of',
    # UK
    'council', 'city', 'borough', 'district', 'county', 'metropolitan', 'royal', 'vale',
    # world
    'administrative', 'amphoe', 'arrondissement', 'autonomous', 'aūdany',
    'bashkia', 'cantón', 'cercle', 'circunscrição', 'comuna',
    'constituency', 'department', 'division', 'gemeente',
    'gorod', 'grad', 'huyện', 'i̇lçesi', 'járás', 'kabupaten',
    'kommun', 'kota', 'liwā’', 'locality', 'markaz',
    'miskrada', 'mis’krada', 'muang', 'mudīrīyat',
    'municipality', 'municipio', 'munitsip’alit’et’i',
    'nohiyai', 'nomós', 'obshtina', 'okres', 'općina', 'opština', 'oraş',
    'pagasts', 'parish', 'powiat',
    'prefecture', 'province', 'provincia', 'qalasy', 'qaḑā’',
    'raion', 'raioni', 'rajonas', 'rayon', 'region',
    'shahrestān-e', 'shahri', 'sub-prefecture', 'zone'
]
