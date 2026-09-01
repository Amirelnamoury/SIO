"""Research seeds recorded during the 2026-09-01 web review.

Gold entries were visually reviewed for the V3 design bible. Indexed entries were
observed in live Siteinspire category results and are broad-corpus references, not
Gold Standards.
"""

GOLD_REFERENCES = (
    ("Franklin Azzi", "https://www.franklinazzi.fr/", "architecture"),
    ("KieranTimberlake", "https://kierantimberlake.com/", "architecture"),
    ("Atelier Oslo", "https://atelieroslo.no/", "architecture"),
    ("Walker Warner", "https://walkerwarner.com/", "architecture"),
    ("Barr Build", "https://www.barrbuild.co.uk/", "construction"),
    ("HUT Architecture", "https://hutarchitecture.com/", "architecture"),
    ("HUTS", "https://huts.com/", "construction"),
    ("Alchemy Architects", "https://alchemyarch.com/", "architecture"),
    ("DBI Consultants", "https://dbi-cc.com/", "construction"),
    ("Focal Glow", "https://focalglow.co/", "ecommerce"),
    ("Heller Studio", "https://www.heller.studio/home", "furniture"),
    ("Zucchetti", "https://www.zucchettidesign.it/en", "furniture"),
    ("ZETR", "https://www.zetr.co/us", "ecommerce"),
    ("Studio Giancarlo Valle", "https://giancarlovalle.com/", "furniture"),
    ("Daytrip", "https://daytrip.studio/", "architecture"),
    ("CIVILIAN", "https://www.civilianprojects.com/", "architecture"),
    ("Svenskt Tenn", "https://www.svenskttenn.com/", "ecommerce"),
    ("Fortuny", "https://fortuny.com/", "ecommerce"),
    ("Office AIO", "https://office-aio.com/", "architecture"),
    ("Modern House Australia", "https://www.modernhouse.co/", "real_estate"),
    ("Norm Architects", "https://normcph.com/", "architecture"),
    ("Space Copenhagen", "https://spacecph.dk/", "architecture"),
    ("Snohetta", "https://www.snohetta.com/", "architecture"),
    ("OMA", "https://www.oma.com/", "architecture"),
    ("BIG", "https://big.dk/", "architecture"),
    ("Herzog & de Meuron", "https://www.herzogdemeuron.com/", "architecture"),
    ("Olson Kundig", "https://olsonkundig.com/", "architecture"),
    ("Studio Gang", "https://studiogang.com/", "architecture"),
    ("The Modern House", "https://themodernhouse.com/", "real_estate"),
    ("Unseen Studio", "https://unseen.co/", "interactive"),
)

INDEXED_REFERENCES = {
    "construction": (
        "The American Housing Corporation", "Liljewall", "Huts", "The Red", "Harris", "Smith Innovation",
        "DBI Construction Consultants", "Alchemy", "Samara", "Bakstad Construction", "Barr Build",
        "Veragouth e Xilema", "Ferrumpipe", "Leve Hytter", "Maman Corp", "Linesight", "Van Acker",
        "American Copper Buildings", "Snøhetta Construction", "Bauhaus Habitat", "Material Cultures",
        "Rural Office", "Workshop Architecture", "New Foundation", "Concrete Collaborative",
        "Common Knowledge", "Buildner", "Mass Timber Institute", "Brick by Brick", "Field Conditions",
    ),
    "hospitality": (
        "Brooklyn Storehouse", "RIGA", "The Beams", "The Damai", "Versus Hotels", "Ennismore", "The OWO",
        "San Felice", "IZZA Marrakech", "Six", "Saint-Gaudens", "Chalet L'Arctique", "Landa Burgos",
        "Find Sanctuary", "Schulhaus Tirol", "Wanderful Chalet", "Piaule Catskill", "Thyme", "Chateau Boll",
        "Ebb Dunedin", "Sommerro", "Ahotels", "The Scott Resort & Spa", "Coco Hotel", "Michelberger Hotel",
        "Purs", "Saint Kate", "Grand Hotel a Villa Feltrinelli", "The Plough", "Flinders Hotel", "Hotel Rottner",
        "Spiritland", "86 Cannon", "Hotel Casa", "Kronborg Castle",
    ),
    "ecommerce": (
        "Lift Type", "Focal Glow", "Estudio Niksen", "Funner", "CENEE", "Coutumes", "KOPPEN",
        "In Common With", "Ruadh", "Svenskt Tenn", "Little Sesame", "Packbags", "Willett", "Marine Serre",
        "Period Paris", "Huey Lightshop", "Metamorphoses", "Perfumer H", "Stone Island", "Kultur 5",
        "NON STANDARD", "Myna Snacks", "GoodMood", "Caley Golf", "JNPR", "Brandblack", "Great Wrap",
        "207 Ouest", "Potluck", "Advene", "In Substance", "Oui Non Editions", "Alipo", "Miche Coffee",
        "Remedy", "Sakara Life", "Rotate", "Garden Variety", "Kinful", "Regrets Only",
    ),
    "technology": (
        "Idle", "Everyday", "Portal", "Squarespace Foundations", "AI in Design Report 2026", "Daylight",
        "Semaloop", "Cohere", "dev agents", "Flow", "IEEE Spectrum", "Zenith VC", "AngelList",
        "Plain Sight Ventures", "CETE-P", "Stereolabs", "1X Technologies", "Together AI", "GenCell",
        "Interstellar Lab", "Crucible Moments", "Sequoia Design Lab", "Festina", "Shopify Ventures",
        "Sequoia Atlas", "Adept", "Electric Air", "Machine Discovery", "Evervault", "Song Sleuth",
        "Array", "Precision", "Planetscale", "Heartbeat Drum Machine", "Mobbin",
    ),
    "education": (
        "Pattern Breaking", "Langmobile", "Cafe Robot", "Whitehead Institute", "Det Kongelige Akademi",
        "The Wellesley 100", "Future London Academy", "The Pickering Group", "The Art Center",
        "Harvard Gazette", "Stanford d.school", "Engaged Cornell", "MIT Media Lab", "Learning Music Ableton",
        "Santa Fe Institute", "Sharjah Art Foundation", "Harvard Graduate School of Design", "CFDA",
        "Mt Cuba Center", "Bronx Arts", "ArtCenter College of Design", "UCLA Arts Architecture",
        "Science Friday", "Arzamas", "Fabrica", "Institut Franco-Chinois de Lyon", "Cornell University",
        "Schoolrunner", "Young and Hungry", "Future London Academy Online",
    ),
    "interactive": (
        "MONOLOG", "Alex Zarour", "Tavano Vincent", "Jordan Robson", "Otherkind", "Bodeyco",
        "Bureau Nicolas Leuliet", "Corentin Bernadou", "Arthur Petrillo", "Design Business Company",
        "Anna Parellada", "Alchemy Digital", "Romain Granai", "Andrew Trousdale", "Jake Dow-Smith Studio",
        "Tom Zelmanski", "Pedro Duarte", "Emele Collab", "MARCD", "Sergey Lisovskiy", "Koal Studio",
        "Forms Supply", "September Works", "Input Logic", "Adrien M Studio", "MILL3", "Unveil",
        "SAY Studio", "Human After All", "Figma", "Fuzzco", "Baast Studio", "Daniel Sun", "Dash Digital",
        "Bryn Taylor", "Active Theory", "Resn", "Lusion", "The Monolith Project", "Immersive Garden",
    ),
}
