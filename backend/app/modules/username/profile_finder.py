"""Username Public Profile Intelligence Module for APEX OSINT.
Probes 125+ high-value public platforms across Gaming, Code/Engineering, Tech, Social,
Creative Portfolios, Music, Media, and Security communities.
Operates strictly through passive public HTTP endpoints with high-performance concurrent async probing.
"""

import asyncio
from typing import Dict, Any, List
import httpx
from app.core.security import SafeHTTPClient
from app.modules.base import (
    BaseOSINTModule,
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
)

# Supported public platforms catalog (125+ platforms across Gaming, Dev, Social, Creative, Media, and Security)
PLATFORM_CATALOG: List[Dict[str, Any]] = [
    # ==========================================
    # 1. Gaming & Esports Platforms
    # ==========================================
    {
        "name": "Steam Community",
        "url_pattern": "https://steamcommunity.com/id/{username}",
        "category": "Gaming & Esports",
        "check_status": [200],
        "absent_text": "The specified profile could not be found",
    },
    {
        "name": "Roblox",
        "url_pattern": "https://www.roblox.com/user.aspx?username={username}",
        "category": "Gaming & Esports",
        "check_status": [200],
        "absent_text": "Page cannot be found",
    },
    {
        "name": "Chess.com",
        "url_pattern": "https://api.chess.com/pub/player/{username}",
        "profile_url": "https://www.chess.com/member/{username}",
        "category": "Gaming & Strategy",
        "check_status": [200],
    },
    {
        "name": "Lichess",
        "url_pattern": "https://lichess.org/@/{username}",
        "category": "Gaming & Strategy",
        "check_status": [200],
        "absent_text": "Page not found",
    },
    {
        "name": "Osu!",
        "url_pattern": "https://osu.ppy.sh/users/{username}",
        "category": "Gaming & Rhythm",
        "check_status": [200],
    },
    {
        "name": "Speedrun.com",
        "url_pattern": "https://www.speedrun.com/user/{username}",
        "category": "Gaming & Leaderboards",
        "check_status": [200],
    },
    {
        "name": "NameMC (Minecraft)",
        "url_pattern": "https://namemc.com/profile/{username}",
        "category": "Gaming & Minecraft",
        "check_status": [200],
    },
    {
        "name": "Tracker.gg",
        "url_pattern": "https://tracker.gg/profile/{username}",
        "category": "Gaming & Esports",
        "check_status": [200],
    },
    {
        "name": "Kick Streaming",
        "url_pattern": "https://kick.com/{username}",
        "category": "Gaming & Streaming",
        "check_status": [200],
    },
    {
        "name": "Twitch",
        "url_pattern": "https://www.twitch.tv/{username}",
        "category": "Gaming & Streaming",
        "check_status": [200],
    },
    {
        "name": "itch.io",
        "url_pattern": "https://{username}.itch.io",
        "category": "Indie Gaming & Dev",
        "check_status": [200],
    },
    {
        "name": "Newgrounds",
        "url_pattern": "https://{username}.newgrounds.com",
        "category": "Gaming & Animation",
        "check_status": [200],
    },
    {
        "name": "Kongregate",
        "url_pattern": "https://www.kongregate.com/accounts/{username}",
        "category": "Gaming & Communities",
        "check_status": [200],
    },
    {
        "name": "RetroAchievements",
        "url_pattern": "https://retroachievements.org/user/{username}",
        "category": "Retro Gaming",
        "check_status": [200],
    },
    {
        "name": "ModDB",
        "url_pattern": "https://www.moddb.com/members/{username}",
        "category": "Gaming & Game Mods",
        "check_status": [200],
    },

    # ==========================================
    # 2. Code, Repositories & Engineering
    # ==========================================
    {
        "name": "GitHub",
        "url_pattern": "https://github.com/{username}",
        "category": "Code & Development",
        "check_status": [200],
    },
    {
        "name": "GitLab",
        "url_pattern": "https://gitlab.com/{username}",
        "category": "Code & Development",
        "check_status": [200],
    },
    {
        "name": "Bitbucket",
        "url_pattern": "https://bitbucket.org/{username}/",
        "category": "Code & Development",
        "check_status": [200],
    },
    {
        "name": "Codeberg",
        "url_pattern": "https://codeberg.org/{username}",
        "category": "Code & Development",
        "check_status": [200],
    },
    {
        "name": "SourceForge",
        "url_pattern": "https://sourceforge.net/u/{username}/profile/",
        "category": "Code & Development",
        "check_status": [200],
    },
    {
        "name": "LeetCode",
        "url_pattern": "https://leetcode.com/{username}/",
        "category": "Coding & Competitions",
        "check_status": [200],
    },
    {
        "name": "Codeforces",
        "url_pattern": "https://codeforces.com/profile/{username}",
        "category": "Coding & Competitions",
        "check_status": [200],
        "absent_text": "handle not found",
    },
    {
        "name": "HackerRank",
        "url_pattern": "https://www.hackerrank.com/{username}",
        "category": "Coding & Competitions",
        "check_status": [200],
    },
    {
        "name": "HackerEarth",
        "url_pattern": "https://www.hackerearth.com/@{username}",
        "category": "Coding & Competitions",
        "check_status": [200],
    },
    {
        "name": "CodeChef",
        "url_pattern": "https://www.codechef.com/users/{username}",
        "category": "Coding & Competitions",
        "check_status": [200],
    },
    {
        "name": "CodeWars",
        "url_pattern": "https://www.codewars.com/users/{username}",
        "category": "Coding & Competitions",
        "check_status": [200],
    },
    {
        "name": "Exercism",
        "url_pattern": "https://exercism.org/profiles/{username}",
        "category": "Coding & Practice",
        "check_status": [200],
    },
    {
        "name": "CodePen",
        "url_pattern": "https://codepen.io/{username}",
        "category": "Frontend Development",
        "check_status": [200],
    },
    {
        "name": "JSFiddle",
        "url_pattern": "https://jsfiddle.net/user/{username}/",
        "category": "Frontend Development",
        "check_status": [200],
    },
    {
        "name": "DockerHub",
        "url_pattern": "https://hub.docker.com/v2/users/{username}/",
        "profile_url": "https://hub.docker.com/u/{username}",
        "category": "Containers & Cloud",
        "check_status": [200],
    },
    {
        "name": "npm Registry",
        "url_pattern": "https://www.npmjs.com/~{username}",
        "category": "Package Ecosystems",
        "check_status": [200],
    },
    {
        "name": "PyPI",
        "url_pattern": "https://pypi.org/user/{username}/",
        "category": "Package Ecosystems",
        "check_status": [200],
    },
    {
        "name": "Crates.io (Rust)",
        "url_pattern": "https://crates.io/users/{username}",
        "category": "Package Ecosystems",
        "check_status": [200],
    },
    {
        "name": "RubyGems",
        "url_pattern": "https://rubygems.org/profiles/{username}",
        "category": "Package Ecosystems",
        "check_status": [200],
    },
    {
        "name": "Packagist (PHP)",
        "url_pattern": "https://packagist.org/users/{username}/",
        "category": "Package Ecosystems",
        "check_status": [200],
    },
    {
        "name": "Hex.pm (Elixir)",
        "url_pattern": "https://hex.pm/users/{username}",
        "category": "Package Ecosystems",
        "check_status": [200],
    },
    {
        "name": "Replit",
        "url_pattern": "https://replit.com/@{username}",
        "category": "Interactive Coding",
        "check_status": [200],
    },
    {
        "name": "Kaggle",
        "url_pattern": "https://www.kaggle.com/{username}",
        "category": "Data Science & AI",
        "check_status": [200],
    },
    {
        "name": "Hugging Face",
        "url_pattern": "https://huggingface.co/{username}",
        "category": "Data Science & AI",
        "check_status": [200],
    },
    {
        "name": "FreeCodeCamp",
        "url_pattern": "https://www.freecodecamp.org/{username}",
        "category": "Learning & Tech",
        "check_status": [200],
    },
    {
        "name": "Vercel",
        "url_pattern": "https://vercel.com/{username}",
        "category": "Cloud & Hosting",
        "check_status": [200],
    },

    # ==========================================
    # 3. Technology, Startups & Writing
    # ==========================================
    {
        "name": "HackerNews",
        "url_pattern": "https://news.ycombinator.com/user?id={username}",
        "category": "Technology Forum",
        "check_status": [200],
        "absent_text": "No such user",
    },
    {
        "name": "Dev.to",
        "url_pattern": "https://dev.to/{username}",
        "category": "Technical Writing",
        "check_status": [200],
    },
    {
        "name": "Medium",
        "url_pattern": "https://medium.com/@{username}",
        "category": "Publishing",
        "check_status": [200],
    },
    {
        "name": "Hashnode",
        "url_pattern": "https://hashnode.com/@{username}",
        "category": "Technical Writing",
        "check_status": [200],
    },
    {
        "name": "Substack",
        "url_pattern": "https://{username}.substack.com",
        "category": "Publishing & Newsletters",
        "check_status": [200],
    },
    {
        "name": "ProductHunt",
        "url_pattern": "https://www.producthunt.com/@{username}",
        "category": "Startups & Products",
        "check_status": [200],
    },
    {
        "name": "Lobste.rs",
        "url_pattern": "https://lobste.rs/u/{username}",
        "category": "Technology Forum",
        "check_status": [200],
    },
    {
        "name": "Devpost",
        "url_pattern": "https://devpost.com/{username}",
        "category": "Hackathons & Projects",
        "check_status": [200],
    },

    # ==========================================
    # 4. Social & Community Networks
    # ==========================================
    {
        "name": "Reddit",
        "url_pattern": "https://www.reddit.com/user/{username}/about.json",
        "profile_url": "https://www.reddit.com/user/{username}",
        "category": "Social & Communities",
        "check_status": [200],
    },
    {
        "name": "Twitter / X",
        "url_pattern": "https://x.com/{username}",
        "category": "Social & Communities",
        "check_status": [200],
    },
    {
        "name": "Mastodon Social",
        "url_pattern": "https://mastodon.social/@{username}",
        "category": "Decentralized Social",
        "check_status": [200],
    },
    {
        "name": "Telegram Public",
        "url_pattern": "https://t.me/{username}",
        "category": "Messaging & Channels",
        "check_status": [200],
        "absent_text": "If you have Telegram, you can view and join",
    },
    {
        "name": "Bluesky Social",
        "url_pattern": "https://bsky.app/profile/{username}.bsky.social",
        "category": "Decentralized Social",
        "check_status": [200],
    },
    {
        "name": "Threads",
        "url_pattern": "https://www.threads.net/@{username}",
        "category": "Social & Communities",
        "check_status": [200],
    },
    {
        "name": "Pinterest",
        "url_pattern": "https://www.pinterest.com/{username}/",
        "category": "Visual Media",
        "check_status": [200],
    },
    {
        "name": "Tumblr",
        "url_pattern": "https://{username}.tumblr.com",
        "category": "Social & Microblogging",
        "check_status": [200],
    },
    {
        "name": "Flickr",
        "url_pattern": "https://www.flickr.com/people/{username}",
        "category": "Photography & Social",
        "check_status": [200],
    },
    {
        "name": "Quora",
        "url_pattern": "https://www.quora.com/profile/{username}",
        "category": "Q&A & Discussion",
        "check_status": [200],
    },
    {
        "name": "AskFM",
        "url_pattern": "https://ask.fm/{username}",
        "category": "Social & Q&A",
        "check_status": [200],
    },
    {
        "name": "Disqus",
        "url_pattern": "https://disqus.com/by/{username}/",
        "category": "Commenting Platform",
        "check_status": [200],
    },

    # ==========================================
    # 5. Identity, Portfolios & Bio Links
    # ==========================================
    {
        "name": "Keybase",
        "url_pattern": "https://keybase.io/{username}",
        "category": "Identity & Cryptography",
        "check_status": [200],
    },
    {
        "name": "Gravatar",
        "url_pattern": "https://gravatar.com/{username}",
        "category": "Global Avatar & Identity",
        "check_status": [200],
    },
    {
        "name": "Linktree",
        "url_pattern": "https://linktr.ee/{username}",
        "category": "Bio Link",
        "check_status": [200],
    },
    {
        "name": "Beacons.ai",
        "url_pattern": "https://beacons.ai/{username}",
        "category": "Bio Link",
        "check_status": [200],
    },
    {
        "name": "Carrd",
        "url_pattern": "https://{username}.carrd.co",
        "category": "One-Page Sites",
        "check_status": [200],
    },
    {
        "name": "About.me",
        "url_pattern": "https://about.me/{username}",
        "category": "Personal Profile",
        "check_status": [200],
    },
    {
        "name": "Bio.link",
        "url_pattern": "https://bio.link/{username}",
        "category": "Bio Link",
        "check_status": [200],
    },
    {
        "name": "Buy Me a Coffee",
        "url_pattern": "https://www.buymeacoffee.com/{username}",
        "category": "Creator Funding",
        "check_status": [200],
    },
    {
        "name": "Patreon",
        "url_pattern": "https://www.patreon.com/{username}",
        "category": "Creator Funding",
        "check_status": [200],
    },
    {
        "name": "Ko-fi",
        "url_pattern": "https://ko-fi.com/{username}",
        "category": "Creator Funding",
        "check_status": [200],
    },

    # ==========================================
    # 6. Creative, Design & 3D Art
    # ==========================================
    {
        "name": "Behance",
        "url_pattern": "https://www.behance.net/{username}",
        "category": "Creative Portfolios",
        "check_status": [200],
    },
    {
        "name": "Dribbble",
        "url_pattern": "https://dribbble.com/{username}",
        "category": "Creative Portfolios",
        "check_status": [200],
    },
    {
        "name": "ArtStation",
        "url_pattern": "https://www.artstation.com/{username}",
        "category": "Digital Art & 3D",
        "check_status": [200],
    },
    {
        "name": "DeviantArt",
        "url_pattern": "https://www.deviantart.com/{username}",
        "category": "Digital Art",
        "check_status": [200],
    },
    {
        "name": "Unsplash",
        "url_pattern": "https://unsplash.com/@{username}",
        "category": "Photography",
        "check_status": [200],
    },
    {
        "name": "500px",
        "url_pattern": "https://500px.com/p/{username}",
        "category": "Photography",
        "check_status": [200],
    },
    {
        "name": "VSCO",
        "url_pattern": "https://vsco.co/{username}/gallery",
        "category": "Photography & Visuals",
        "check_status": [200],
    },
    {
        "name": "Sketchfab (3D)",
        "url_pattern": "https://sketchfab.com/{username}",
        "category": "3D Models & VR",
        "check_status": [200],
    },

    # ==========================================
    # 7. Audio, Music & Podcasts
    # ==========================================
    {
        "name": "SoundCloud",
        "url_pattern": "https://soundcloud.com/{username}",
        "category": "Audio & Music",
        "check_status": [200],
    },
    {
        "name": "Spotify Artist/User",
        "url_pattern": "https://open.spotify.com/user/{username}",
        "category": "Audio & Music",
        "check_status": [200],
    },
    {
        "name": "Bandcamp",
        "url_pattern": "https://bandcamp.com/{username}",
        "category": "Audio & Music",
        "check_status": [200],
    },
    {
        "name": "Mixcloud",
        "url_pattern": "https://www.mixcloud.com/{username}/",
        "category": "DJ Mixes & Radio",
        "check_status": [200],
    },
    {
        "name": "Audiomack",
        "url_pattern": "https://audiomack.com/{username}",
        "category": "Audio & Music",
        "check_status": [200],
    },
    {
        "name": "Last.fm",
        "url_pattern": "https://www.last.fm/user/{username}",
        "category": "Music Scrobbling",
        "check_status": [200],
    },

    # ==========================================
    # 8. Video, Books & Entertainment
    # ==========================================
    {
        "name": "YouTube",
        "url_pattern": "https://www.youtube.com/@{username}",
        "category": "Video & Media",
        "check_status": [200],
    },
    {
        "name": "Vimeo",
        "url_pattern": "https://vimeo.com/{username}",
        "category": "Video & Media",
        "check_status": [200],
    },
    {
        "name": "Dailymotion",
        "url_pattern": "https://www.dailymotion.com/{username}",
        "category": "Video & Media",
        "check_status": [200],
    },
    {
        "name": "Letterboxd",
        "url_pattern": "https://letterboxd.com/{username}/",
        "category": "Film & Cinema",
        "check_status": [200],
    },
    {
        "name": "Goodreads",
        "url_pattern": "https://www.goodreads.com/{username}",
        "category": "Books & Literature",
        "check_status": [200],
    },
    {
        "name": "Trakt.tv",
        "url_pattern": "https://trakt.tv/users/{username}",
        "category": "TV & Film Tracking",
        "check_status": [200],
    },
    {
        "name": "MyAnimeList",
        "url_pattern": "https://myanimelist.net/profile/{username}",
        "category": "Anime & Manga",
        "check_status": [200],
    },
    {
        "name": "AniList",
        "url_pattern": "https://anilist.co/user/{username}/",
        "category": "Anime & Manga",
        "check_status": [200],
    },

    # ==========================================
    # 9. Security, Research & Bug Bounty
    # ==========================================
    {
        "name": "HackerOne",
        "url_pattern": "https://hackerone.com/{username}",
        "category": "Security & Bug Bounty",
        "check_status": [200],
    },
    {
        "name": "Bugcrowd",
        "url_pattern": "https://bugcrowd.com/{username}",
        "category": "Security & Bug Bounty",
        "check_status": [200],
    },
    {
        "name": "CTFtime",
        "url_pattern": "https://ctftime.org/user/{username}",
        "category": "Security & CTF",
        "check_status": [200],
    },
    {
        "name": "Pastebin",
        "url_pattern": "https://pastebin.com/u/{username}",
        "category": "Code & Text Sharing",
        "check_status": [200],
    },

    # ==========================================
    # 10. Additional Gaming, Dev, 3D & Community
    # ==========================================
    {
        "name": "Nexus Mods",
        "url_pattern": "https://www.nexusmods.com/users/{username}",
        "category": "Gaming & Game Mods",
        "check_status": [200],
    },
    {
        "name": "SteamGifts",
        "url_pattern": "https://www.steamgifts.com/user/{username}",
        "category": "Gaming & Communities",
        "check_status": [200],
    },
    {
        "name": "GOG (Good Old Games)",
        "url_pattern": "https://www.gog.com/u/{username}",
        "category": "Gaming & Digital Store",
        "check_status": [200],
    },
    {
        "name": "PlayTracker",
        "url_pattern": "https://playtracker.net/user/{username}",
        "category": "Gaming & Stats",
        "check_status": [200],
    },
    {
        "name": "Flightradar24",
        "url_pattern": "https://my.flightradar24.com/{username}",
        "category": "Aviation & Tracking",
        "check_status": [200],
    },
    {
        "name": "SourceHut",
        "url_pattern": "https://sr.ht/~{username}",
        "category": "Code & Development",
        "check_status": [200],
    },
    {
        "name": "Glitch",
        "url_pattern": "https://glitch.com/@{username}",
        "category": "Interactive Coding",
        "check_status": [200],
    },
    {
        "name": "CodeFactor",
        "url_pattern": "https://www.codefactor.io/profile/{username}",
        "category": "Code Quality & Dev",
        "check_status": [200],
    },
    {
        "name": "Travis CI",
        "url_pattern": "https://travis-ci.com/github/{username}",
        "category": "CI/CD & DevOps",
        "check_status": [200],
    },
    {
        "name": "Observable",
        "url_pattern": "https://observablehq.com/@{username}",
        "category": "Data Science & Viz",
        "check_status": [200],
    },
    {
        "name": "Gumroad",
        "url_pattern": "https://{username}.gumroad.com",
        "category": "Creator Funding & Sales",
        "check_status": [200],
    },
    {
        "name": "OpenSea",
        "url_pattern": "https://opensea.io/{username}",
        "category": "Web3 & Digital Assets",
        "check_status": [200],
    },
    {
        "name": "Lemmy",
        "url_pattern": "https://lemmy.world/u/{username}",
        "category": "Federated Social",
        "check_status": [200],
    },
    {
        "name": "V2EX",
        "url_pattern": "https://www.v2ex.com/member/{username}",
        "category": "Technology Forum",
        "check_status": [200],
    },
    {
        "name": "Steemit",
        "url_pattern": "https://steemit.com/@{username}",
        "category": "Decentralized Social",
        "check_status": [200],
    },
    {
        "name": "Hive Blog",
        "url_pattern": "https://hive.blog/@{username}",
        "category": "Decentralized Social",
        "check_status": [200],
    },
    {
        "name": "Wikipedia Contributor",
        "url_pattern": "https://en.wikipedia.org/wiki/User:{username}",
        "category": "Encyclopedic Collaboration",
        "check_status": [200],
    },
    {
        "name": "Fandom / Wikia",
        "url_pattern": "https://community.fandom.com/wiki/User:{username}",
        "category": "Fandom & Communities",
        "check_status": [200],
    },
    {
        "name": "SoundClick",
        "url_pattern": "https://www.soundclick.com/{username}",
        "category": "Audio & Music",
        "check_status": [200],
    },
    {
        "name": "Libre.fm",
        "url_pattern": "https://libre.fm/user/{username}",
        "category": "Music Scrobbling",
        "check_status": [200],
    },
    {
        "name": "Tripadvisor",
        "url_pattern": "https://www.tripadvisor.com/Profile/{username}",
        "category": "Travel & Reviews",
        "check_status": [200],
    },
    {
        "name": "Strava Athlete",
        "url_pattern": "https://www.strava.com/athletes/{username}",
        "category": "Fitness & Outdoor",
        "check_status": [200],
    },
    {
        "name": "AllTrails",
        "url_pattern": "https://www.alltrails.com/members/{username}",
        "category": "Fitness & Outdoor",
        "check_status": [200],
    },
    {
        "name": "Geocaching",
        "url_pattern": "https://www.geocaching.com/p/default.aspx?u={username}",
        "category": "Outdoor & Geocaching",
        "check_status": [200],
    },
    {
        "name": "Instructables",
        "url_pattern": "https://www.instructables.com/member/{username}/",
        "category": "DIY & Engineering",
        "check_status": [200],
    },
    {
        "name": "Thingiverse",
        "url_pattern": "https://www.thingiverse.com/{username}/designs",
        "category": "3D Printing & CAD",
        "check_status": [200],
    },
    {
        "name": "Printables",
        "url_pattern": "https://www.printables.com/@{username}",
        "category": "3D Printing & CAD",
        "check_status": [200],
    },
    {
        "name": "Cults3D",
        "url_pattern": "https://cults3d.com/en/users/{username}/creations",
        "category": "3D Printing & CAD",
        "check_status": [200],
    },
]


class UsernameProfileFinderModule(BaseOSINTModule):
    """Deep Multi-Platform Public Identity & Presence Prober."""

    name = "username_profile_finder"
    display_name = "Public Multi-Platform Identity Prober"
    description = (
        "High-performance parallel OSINT prober scanning 125+ public platforms across Gaming, "
        "Developer ecosystems, Social networks, Creative portfolios, and Security directories."
    )
    category = "USERNAME"
    target_types = ["USERNAME", "PERSON"]
    rate_limit = 10.0
    source = "Public Web & Platform Endpoints"
    license = "Public Domain / Lawful OSINT"

    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        finding = NormalizedFinding()
        username = target_value.strip().lstrip("@")

        finding.primary_entity = NormalizedEntity(
            type="USERNAME",
            value=username,
            normalized_value=username.lower(),
            confidence=1.0,
        )

        found_profiles: List[Dict[str, Any]] = []
        all_probed_sites: List[Dict[str, Any]] = []

        # High-concurrency worker pool with shared connection pool
        semaphore = asyncio.Semaphore(35)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/json,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        limits = httpx.Limits(max_keepalive_connections=50, max_connections=80)

        async with httpx.AsyncClient(timeout=3.5, limits=limits, headers=headers, follow_redirects=False, verify=False) as client:
            async def check_platform(plat: Dict[str, Any]):
                url = plat["url_pattern"].format(username=username)
                public_url = plat.get("profile_url", url).format(username=username)
                status_label = "NOT_FOUND"
                status_code = None

                async with semaphore:
                    try:
                        resp = await client.get(url)
                        status_code = resp.status_code
                        if resp.status_code in plat["check_status"]:
                            # Check absent text
                            if "absent_text" in plat and plat["absent_text"].lower() in resp.text.lower():
                                status_label = "NOT_FOUND"
                            else:
                                status_label = "FOUND"
                                found_profiles.append({
                                    "platform": plat["name"],
                                    "category": plat["category"],
                                    "url": public_url,
                                    "status_code": resp.status_code,
                                })
                        elif resp.status_code == 429:
                            status_label = "RATE_LIMITED"
                        else:
                            status_label = "NOT_FOUND"
                    except Exception:
                        status_label = "NOT_FOUND"

                all_probed_sites.append({
                    "platform": plat["name"],
                    "category": plat["category"],
                    "url": public_url,
                    "status": status_label,
                    "status_code": status_code,
                })

            # Concurrently probe all platforms in parallel
            await asyncio.gather(*(check_platform(p) for p in PLATFORM_CATALOG))

            # Deep Identity Extraction on confirmed platforms
            # If GitHub is found, extract public bio, location, name, and website
            if any(p["platform"] == "GitHub" for p in found_profiles):
                try:
                    gh_api_resp = await client.get(f"https://api.github.com/users/{username}")
                    if gh_api_resp.status_code == 200:
                        gh_data = gh_api_resp.json()
                        gh_name = gh_data.get("name")
                        gh_loc = gh_data.get("location")
                        gh_blog = gh_data.get("blog")
                        gh_company = gh_data.get("company")
                        gh_bio = gh_data.get("bio")

                        if gh_name:
                            finding.discovered_entities.append(
                                NormalizedEntity(
                                    type="PERSON",
                                    value=gh_name,
                                    normalized_value=gh_name.lower(),
                                    confidence=0.92,
                                    metadata={"source": "GitHub Profile"}
                                )
                            )
                        if gh_loc:
                            finding.discovered_entities.append(
                                NormalizedEntity(
                                    type="LOCATION",
                                    value=gh_loc,
                                    normalized_value=gh_loc.lower(),
                                    confidence=0.88,
                                    metadata={"source": "GitHub Profile"}
                                )
                            )
                        if gh_blog:
                            clean_blog = gh_blog.strip()
                            if not clean_blog.startswith("http"):
                                clean_blog = f"https://{clean_blog}"
                            finding.discovered_entities.append(
                                NormalizedEntity(
                                    type="URL",
                                    value=clean_blog,
                                    normalized_value=clean_blog.lower(),
                                    confidence=0.90,
                                    metadata={"source": "GitHub Profile"}
                                )
                            )
                        if gh_company:
                            clean_company = gh_company.lstrip("@").strip()
                            finding.discovered_entities.append(
                                NormalizedEntity(
                                    type="ORGANIZATION",
                                    value=clean_company,
                                    normalized_value=clean_company.lower(),
                                    confidence=0.85,
                                    metadata={"source": "GitHub Profile"}
                                )
                            )
                except Exception:
                    pass

        # Sort found profiles by category and platform
        found_profiles.sort(key=lambda x: (x["category"], x["platform"]))

        evidence_snippet = (
            f"Deep-scanned {len(PLATFORM_CATALOG)} public platforms for handle '{username}'. "
            f"Verified {len(found_profiles)} active endpoints across gaming, tech, social, and code ecosystems: "
            f"{', '.join(p['platform'] for p in found_profiles[:8])}"
            f"{'...' if len(found_profiles) > 8 else ''}."
        )

        finding.evidence.append(
            NormalizedEvidence(
                source_name="Multi-Platform Identity Prober (125+ Ecosystems)",
                source_type="SOCIAL_PROFILE",
                source_url=None,
                snippet=evidence_snippet,
                collection_method="HTTP_FAST_SCAN",
                confidence=0.94,
                epistemic_label="OBSERVED",
                raw_payload={
                    "username": username,
                    "total_probed": len(PLATFORM_CATALOG),
                    "found_count": len(found_profiles),
                    "verified_matches": found_profiles,
                    "all_probed_sites": all_probed_sites,
                },
                related_entity_values=[username]
            )
        )

        for prof in found_profiles:
            plat_name = prof["platform"]
            p_url = prof["url"]

            prof_entity = NormalizedEntity(
                type="SOCIAL_PROFILE",
                value=f"{plat_name} (@{username})",
                normalized_value=p_url,
                confidence=0.92,
                metadata={
                    "platform": plat_name,
                    "url": p_url,
                    "category": prof["category"],
                    "status_code": prof["status_code"],
                }
            )
            finding.discovered_entities.append(prof_entity)
            finding.relationships.append(
                NormalizedRelationship(
                    source_value=username,
                    source_type="USERNAME",
                    target_value=f"{plat_name} (@{username})",
                    target_type="SOCIAL_PROFILE",
                    relation_type="ASSOCIATED_WITH",
                    confidence=0.92,
                    evidence_indices=[0]
                )
            )

        return finding
