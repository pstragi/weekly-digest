import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "nata.pstragowska@gmail.com")
SENDER_NAME = os.getenv("SENDER_NAME", "News Digest")

MAX_ARTICLES_PER_CATEGORY = 3  # 2 English + 1 Polish per category
LOOKBACK_HOURS = 96            # default for manual runs; schedule overrides this

DEBUG_MAX_ARTICLES = None  # set to e.g. 20 to cap articles during debugging

INTERESTS = {
    "MARKETING": {
        "emoji": "📣",
        "description": (
            "Digital marketing, advertising, brand strategy, content marketing, "
            "SEO, social media growth, martech, influencer marketing, PR, "
            "growth hacking, performance marketing, email marketing"
        ),
    },
    "TECHNOLOGY": {
        "emoji": "💻",
        "description": (
            "AI and machine learning breakthroughs, startups and funding rounds, "
            "software products, cybersecurity, digital transformation, "
            "automation, tech industry news, product launches"
        ),
    },
    "SCIENCE": {
        "emoji": "🔬",
        "description": (
            "Scientific discoveries and research papers, biology, physics, "
            "climate science, space exploration, medicine and health research, "
            "genetics, neuroscience, academic studies with real-world impact"
        ),
    },
    "SOCIAL_SCIENCES": {
        "emoji": "🧠",
        "description": (
            "Psychology, sociology, human behavior, cognitive science, "
            "mental health trends, social phenomena, culture, relationships, "
            "behavioral economics, social psychology experiments and findings"
        ),
    },
    "SPORT": {
        "emoji": "⚽",
        "description": (
            "Sports news and results, football, tennis, athletics, cycling, "
            "championships and tournaments, sports science, athlete stories, "
            "fitness trends with a sports angle"
        ),
    },
    "WELLBEING": {
        "emoji": "🌱",
        "description": (
            "Health optimization, nutrition science, self-development, "
            "mindfulness and meditation, productivity systems, sleep science, "
            "stress management, personal growth, biohacking, longevity research"
        ),
    },
    "CRYPTO": {
        "emoji": "₿",
        "description": (
            "Cryptocurrency markets, Bitcoin, Ethereum, DeFi, NFTs, blockchain technology, "
            "Web3, crypto regulation, exchange news, tokenomics, on-chain analytics, "
            "crypto investing and trading trends, stablecoins, Layer 2 networks"
        ),
    },
}

# Authority scores (1–10) per source per category.
# Higher = more credible/relevant for that category.
# is_popular_feed: True = dedicated trending/most-read feed → 10% score boost.
SOURCES = [

    # ── MARKETING — English ────────────────────────────────────────────────────
    {
        "name": "Marketing Dive",
        "rss": "https://www.marketingdive.com/feeds/news/",
        "language": "en",
        "authority": {
            "MARKETING": 10, "TECHNOLOGY": 6, "SCIENCE": 2,
            "SOCIAL_SCIENCES": 3, "SPORT": 1, "WELLBEING": 2,
        },
    },
    {
        "name": "Marketing Week",
        "rss": "https://www.marketingweek.com/feed/",
        "language": "en",
        "authority": {
            "MARKETING": 9, "TECHNOLOGY": 4, "SCIENCE": 2,
            "SOCIAL_SCIENCES": 3, "SPORT": 1, "WELLBEING": 2,
        },
    },
    {
        "name": "Marketing Brew",
        "rss": "https://www.marketingbrew.com/rss",
        "language": "en",
        "authority": {
            "MARKETING": 9, "TECHNOLOGY": 5, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 1, "WELLBEING": 1,
        },
    },
    {
        "name": "The Drum",
        "rss": "https://www.thedrum.com/rss",
        "language": "en",
        "authority": {
            "MARKETING": 9, "TECHNOLOGY": 4, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 3, "SPORT": 2, "WELLBEING": 2,
        },
    },
    {
        "name": "Digiday",
        "rss": "https://digiday.com/feed/",
        "language": "en",
        "authority": {
            "MARKETING": 9, "TECHNOLOGY": 6, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 1, "WELLBEING": 1,
        },
    },

    # ── MARKETING — Polish ─────────────────────────────────────────────────────
    {
        "name": "Sprawny Marketing",
        "rss": "https://sprawnymarketing.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 9, "TECHNOLOGY": 4, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 3, "SPORT": 1, "WELLBEING": 3,
        },
    },
    {
        "name": "Nowy Marketing",
        "rss": "https://nowymarketing.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 9, "TECHNOLOGY": 4, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 1, "WELLBEING": 1,
        },
    },
    {
        "name": "Marketing przy Kawie",
        "rss": "https://marketingprzykawie.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 8, "TECHNOLOGY": 3, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 1, "WELLBEING": 1,
        },
    },
    {
        "name": "Interaktywnie.com",
        "rss": "https://interaktywnie.com/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 7, "TECHNOLOGY": 5, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 1, "WELLBEING": 1,
        },
    },
    {
        "name": "Proto.pl",
        "rss": "https://www.proto.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 7, "TECHNOLOGY": 4, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 3, "SPORT": 1, "WELLBEING": 1,
        },
    },

    # ── TECHNOLOGY — English ───────────────────────────────────────────────────
    {
        "name": "TechCrunch",
        "rss": "https://techcrunch.com/feed/",
        "language": "en",
        "authority": {
            "MARKETING": 6, "TECHNOLOGY": 10, "SCIENCE": 4,
            "SOCIAL_SCIENCES": 3, "SPORT": 1, "WELLBEING": 2,
        },
    },
    {
        "name": "MIT Technology Review",
        "rss": "https://www.technologyreview.com/feed/",
        "language": "en",
        "authority": {
            "MARKETING": 4, "TECHNOLOGY": 10, "SCIENCE": 9,
            "SOCIAL_SCIENCES": 5, "SPORT": 1, "WELLBEING": 4,
        },
    },
    {
        "name": "Wired",
        "rss": "https://www.wired.com/feed/rss",
        "language": "en",
        "authority": {
            "MARKETING": 5, "TECHNOLOGY": 9, "SCIENCE": 7,
            "SOCIAL_SCIENCES": 5, "SPORT": 2, "WELLBEING": 4,
        },
    },
    {
        "name": "Ars Technica",
        "rss": "https://feeds.arstechnica.com/arstechnica/index",
        "language": "en",
        "authority": {
            "MARKETING": 3, "TECHNOLOGY": 9, "SCIENCE": 7,
            "SOCIAL_SCIENCES": 3, "SPORT": 2, "WELLBEING": 3,
        },
    },
    {
        "name": "The Verge",
        "rss": "https://www.theverge.com/rss/index.xml",
        "language": "en",
        "authority": {
            "MARKETING": 4, "TECHNOLOGY": 9, "SCIENCE": 5,
            "SOCIAL_SCIENCES": 4, "SPORT": 2, "WELLBEING": 3,
        },
    },

    # ── TECHNOLOGY — Polish ────────────────────────────────────────────────────
    {
        "name": "Spider's Web",
        "rss": "https://spidersweb.pl/feed",
        "language": "pl",
        "authority": {
            "MARKETING": 4, "TECHNOLOGY": 8, "SCIENCE": 4,
            "SOCIAL_SCIENCES": 3, "SPORT": 2, "WELLBEING": 3,
        },
    },
    {
        "name": "Antyweb",
        "rss": "https://antyweb.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 3, "TECHNOLOGY": 8, "SCIENCE": 4,
            "SOCIAL_SCIENCES": 2, "SPORT": 2, "WELLBEING": 3,
        },
    },
    {
        "name": "ITwiz",
        "rss": "https://itwiz.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 3, "TECHNOLOGY": 8, "SCIENCE": 3,
            "SOCIAL_SCIENCES": 2, "SPORT": 1, "WELLBEING": 2,
        },
    },
    {
        "name": "MobileTrends",
        "rss": "https://mobiletrends.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 4, "TECHNOLOGY": 7, "SCIENCE": 2,
            "SOCIAL_SCIENCES": 2, "SPORT": 1, "WELLBEING": 2,
        },
    },
    {
        "name": "Benchmark.pl",
        "rss": "https://benchmark.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 7, "SCIENCE": 3,
            "SOCIAL_SCIENCES": 2, "SPORT": 1, "WELLBEING": 2,
        },
    },

    # ── SCIENCE — English ──────────────────────────────────────────────────────
    # ScienceDaily Top comes before the main feed so its is_popular_feed flag
    # wins deduplication when the same article appears in both feeds.
    {
        "name": "ScienceDaily Top",
        "rss": "https://www.sciencedaily.com/rss/top/science.xml",
        "language": "en",
        "is_popular_feed": True,
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 5, "SCIENCE": 9,
            "SOCIAL_SCIENCES": 6, "SPORT": 2, "WELLBEING": 6,
        },
    },
    {
        "name": "Nature",
        "rss": "https://www.nature.com/nature.rss",
        "language": "en",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 6, "SCIENCE": 10,
            "SOCIAL_SCIENCES": 7, "SPORT": 1, "WELLBEING": 7,
        },
    },
    {
        "name": "Science AAAS",
        "rss": "https://www.science.org/rss/news_current.xml",
        "language": "en",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 6, "SCIENCE": 10,
            "SOCIAL_SCIENCES": 7, "SPORT": 2, "WELLBEING": 6,
        },
    },
    {
        "name": "Scientific American",
        "rss": "https://rss.sciam.com/ScientificAmerican-Global",
        "language": "en",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 7, "SCIENCE": 10,
            "SOCIAL_SCIENCES": 7, "SPORT": 2, "WELLBEING": 6,
        },
    },
    {
        "name": "Science News",
        "rss": "https://www.sciencenews.org/feed",
        "language": "en",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 5, "SCIENCE": 9,
            "SOCIAL_SCIENCES": 6, "SPORT": 2, "WELLBEING": 5,
        },
    },
    {
        "name": "ScienceDaily",
        "rss": "https://www.sciencedaily.com/rss/all.xml",
        "language": "en",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 5, "SCIENCE": 9,
            "SOCIAL_SCIENCES": 6, "SPORT": 2, "WELLBEING": 6,
        },
    },

    # ── SCIENCE — Polish ───────────────────────────────────────────────────────
    {
        "name": "Nauka w Polsce",
        "rss": "https://naukawpolsce.pl/rss.xml",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 4, "SCIENCE": 9,
            "SOCIAL_SCIENCES": 6, "SPORT": 1, "WELLBEING": 5,
        },
    },
    {
        "name": "Pulsar",
        "rss": "https://www.projektpulsar.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 5, "SCIENCE": 8,
            "SOCIAL_SCIENCES": 5, "SPORT": 1, "WELLBEING": 4,
        },
    },
    {
        "name": "Dziennik Naukowy",
        "rss": "https://dzienniknaukowy.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 4, "SCIENCE": 8,
            "SOCIAL_SCIENCES": 5, "SPORT": 1, "WELLBEING": 4,
        },
    },
    {
        "name": "Focus",
        "rss": "https://www.focus.pl/rss",
        "language": "pl",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 5, "SCIENCE": 7,
            "SOCIAL_SCIENCES": 6, "SPORT": 3, "WELLBEING": 5,
        },
    },
    {
        "name": "Wiedza i Życie",
        "rss": "https://www.wiedzaizycie.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 5, "SCIENCE": 8,
            "SOCIAL_SCIENCES": 6, "SPORT": 2, "WELLBEING": 6,
        },
    },

    # ── SOCIAL SCIENCES — English ──────────────────────────────────────────────
    {
        "name": "Psychology Today",
        "rss": "https://feeds.feedburner.com/PsychologyToday",
        "language": "en",
        "authority": {
            "MARKETING": 3, "TECHNOLOGY": 2, "SCIENCE": 6,
            "SOCIAL_SCIENCES": 10, "SPORT": 2, "WELLBEING": 9,
        },
    },
    {
        "name": "PsyPost",
        "rss": "https://www.psypost.org/feed",
        "language": "en",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 3, "SCIENCE": 7,
            "SOCIAL_SCIENCES": 10, "SPORT": 2, "WELLBEING": 7,
        },
    },
    {
        "name": "Greater Good Berkeley",
        "rss": "https://greatergood.berkeley.edu/feeds/rss",
        "language": "en",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 2, "SCIENCE": 6,
            "SOCIAL_SCIENCES": 9, "SPORT": 2, "WELLBEING": 9,
        },
    },
    {
        "name": "APA PsycPORT",
        "rss": "https://www.apa.org/pubs/highlights/psycport/rss.xml",
        "language": "en",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 2, "SCIENCE": 6,
            "SOCIAL_SCIENCES": 10, "SPORT": 2, "WELLBEING": 7,
        },
    },
    {
        "name": "BPS Research Digest",
        "rss": "https://digest.bps.org.uk/feed/",
        "language": "en",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 2, "SCIENCE": 6,
            "SOCIAL_SCIENCES": 10, "SPORT": 2, "WELLBEING": 6,
        },
    },

    # ── SOCIAL SCIENCES — Polish ───────────────────────────────────────────────
    {
        "name": "Przekroj",
        "rss": "https://przekroj.org/feed",
        "language": "pl",
        "authority": {
            "MARKETING": 3, "TECHNOLOGY": 4, "SCIENCE": 8,
            "SOCIAL_SCIENCES": 9, "SPORT": 3, "WELLBEING": 7,
        },
    },
    {
        "name": "Charaktery",
        "rss": "https://charaktery.eu/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 2, "SCIENCE": 5,
            "SOCIAL_SCIENCES": 10, "SPORT": 1, "WELLBEING": 8,
        },
    },
    {
        "name": "Psychologia w Praktyce",
        "rss": "https://psychologiawpraktyce.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 2, "SCIENCE": 5,
            "SOCIAL_SCIENCES": 9, "SPORT": 1, "WELLBEING": 8,
        },
    },
    {
        "name": "Strefa Psyche SWPS",
        "rss": "https://www.swps.pl/strefa-psyche/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 2, "SCIENCE": 5,
            "SOCIAL_SCIENCES": 9, "SPORT": 1, "WELLBEING": 7,
        },
    },
    {
        "name": "Psychologia Behawioralna",
        "rss": "https://www.psychologiabehawioralna.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 2, "SCIENCE": 5,
            "SOCIAL_SCIENCES": 9, "SPORT": 1, "WELLBEING": 7,
        },
    },
    {
        "name": "Psychologia-Spoleczna.pl",
        "rss": "http://www.psychologia-spoleczna.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 2, "SCIENCE": 6,
            "SOCIAL_SCIENCES": 9, "SPORT": 1, "WELLBEING": 6,
        },
    },

    # ── SPORT — English ────────────────────────────────────────────────────────
    {
        "name": "BBC Sport",
        "rss": "https://feeds.bbci.co.uk/sport/rss.xml",
        "language": "en",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 1, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 10, "WELLBEING": 3,
        },
    },
    {
        "name": "ESPN",
        "rss": "https://www.espn.com/espn/rss/news",
        "language": "en",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 2, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 9, "WELLBEING": 3,
        },
    },
    {
        "name": "Sports Illustrated",
        "rss": "https://www.si.com/rss/si_topstories.rss",
        "language": "en",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 1, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 9, "WELLBEING": 3,
        },
    },

    # ── SPORT — Polish ─────────────────────────────────────────────────────────
    {
        "name": "Sportowe Fakty",
        "rss": "https://sportowefakty.wp.pl/rss.xml",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 1, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 9, "WELLBEING": 2,
        },
    },
    {
        "name": "Weszlo.com",
        "rss": "https://weszlo.com/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 1, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 9, "WELLBEING": 2,
        },
    },
    {
        "name": "Przeglad Sportowy",
        "rss": "https://przegladsportowy.onet.pl/rss.xml",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 1, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 9, "WELLBEING": 2,
        },
    },
    {
        "name": "TVP Sport",
        "rss": "https://sport.tvp.pl/rss.xml",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 1, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 8, "WELLBEING": 2,
        },
    },
    {
        "name": "Onet Sport",
        "rss": "https://sport.onet.pl/rss.xml",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 1, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 2, "SPORT": 8, "WELLBEING": 2,
        },
    },

    # ── WELLBEING — English ────────────────────────────────────────────────────
    {
        "name": "Healthline Nutrition",
        "rss": "https://www.healthline.com/rss/nutrition",
        "language": "en",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 2, "SCIENCE": 6,
            "SOCIAL_SCIENCES": 4, "SPORT": 3, "WELLBEING": 10,
        },
    },
    # Greater Good Berkeley listed above also serves WELLBEING (authority score 9)

    # ── WELLBEING — Polish ─────────────────────────────────────────────────────
    {
        "name": "Poradnik Zdrowie",
        "rss": "https://www.poradnikzdrowie.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 2, "SCIENCE": 5,
            "SOCIAL_SCIENCES": 4, "SPORT": 3, "WELLBEING": 9,
        },
    },
    {
        "name": "enel Zdrowie",
        "rss": "https://enel.pl/enelzdrowie/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 2, "SCIENCE": 5,
            "SOCIAL_SCIENCES": 4, "SPORT": 2, "WELLBEING": 8,
        },
    },
    {
        "name": "ABC Zdrowie",
        "rss": "https://www.abczdrowie.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 1, "SCIENCE": 4,
            "SOCIAL_SCIENCES": 3, "SPORT": 2, "WELLBEING": 8,
        },
    },
    {
        "name": "Wellbeing Polska",
        "rss": "https://wellbeingpolska.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 2, "SCIENCE": 4,
            "SOCIAL_SCIENCES": 6, "SPORT": 2, "WELLBEING": 9,
        },
    },
    {
        "name": "Naturalnie o Zdrowiu",
        "rss": "https://naturalnieozdrowiu.pl/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 1, "SCIENCE": 4,
            "SOCIAL_SCIENCES": 3, "SPORT": 2, "WELLBEING": 8,
        },
    },

    # ── CRYPTO — English ──────────────────────────────────────────────────────
    {
        "name": "CoinDesk",
        "rss": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "language": "en",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 6, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 1, "SPORT": 1, "WELLBEING": 1, "CRYPTO": 10,
        },
    },
    {
        "name": "Cointelegraph",
        "rss": "https://cointelegraph.com/rss",
        "language": "en",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 6, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 1, "SPORT": 1, "WELLBEING": 1, "CRYPTO": 10,
        },
    },
    {
        "name": "The Block",
        "rss": "https://www.theblock.co/rss.xml",
        "language": "en",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 6, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 1, "SPORT": 1, "WELLBEING": 1, "CRYPTO": 9,
        },
    },
    {
        "name": "Decrypt",
        "rss": "https://decrypt.co/feed",
        "language": "en",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 5, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 1, "SPORT": 1, "WELLBEING": 1, "CRYPTO": 9,
        },
    },
    {
        "name": "Blockworks",
        "rss": "https://blockworks.co/feed",
        "language": "en",
        "authority": {
            "MARKETING": 2, "TECHNOLOGY": 5, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 1, "SPORT": 1, "WELLBEING": 1, "CRYPTO": 8,
        },
    },

    # ── CRYPTO — Polish ────────────────────────────────────────────────────────
    {
        "name": "BitHub.pl",
        "rss": "https://bithub.pl/feed",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 4, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 1, "SPORT": 1, "WELLBEING": 1, "CRYPTO": 9,
        },
    },
    {
        "name": "BeInCrypto PL",
        "rss": "https://pl.beincrypto.com/feed/",
        "language": "pl",
        "authority": {
            "MARKETING": 1, "TECHNOLOGY": 4, "SCIENCE": 1,
            "SOCIAL_SCIENCES": 1, "SPORT": 1, "WELLBEING": 1, "CRYPTO": 9,
        },
    },
]
