import React, { useState } from "react";
import {
  Globe,
  Search,
  ExternalLink,
  Database,
  Terminal,
  MapPin,
  Mail,
  User,
  Shield,
  Layers,
  Archive,
  Building,
  Phone,
  Code,
  Filter,
} from "lucide-react";

interface SourcesCatalogProps {
  currentTarget?: string;
}

interface OSINTSource {
  id: string;
  name: string;
  category: string;
  description: string;
  url: string;
  searchUrlTemplate?: string;
  badge?: string;
}

const OSINT_SOURCES: OSINTSource[] = [
  // Search Engines & Dorks
  {
    id: "google_dorks",
    name: "Google Intelligence Dorking",
    category: "Search Engines",
    description: "Search engine dorks for indexing public directories, documents, and subdomains.",
    url: "https://www.google.com",
    searchUrlTemplate: "https://www.google.com/search?q=site%3A{target}+OR+%22{target}%22",
    badge: "Core",
  },
  {
    id: "duckduckgo",
    name: "DuckDuckGo",
    category: "Search Engines",
    description: "Private search engine without tracker tracking or localized filter bubbles.",
    url: "https://duckduckgo.com",
    searchUrlTemplate: "https://duckduckgo.com/?q=%22{target}%22",
  },
  {
    id: "yandex",
    name: "Yandex Search",
    category: "Search Engines",
    description: "High-accuracy search engine especially strong in Eastern Europe and international domains.",
    url: "https://yandex.com",
    searchUrlTemplate: "https://yandex.com/search/?text=%22{target}%22",
  },
  {
    id: "startpage",
    name: "Startpage",
    category: "Search Engines",
    description: "Google search results delivered with strict privacy protections and no logging.",
    url: "https://www.startpage.com",
    searchUrlTemplate: "https://www.startpage.com/sp/search?query=%22{target}%22",
  },

  // Domains, Subdomains & DNS
  {
    id: "crtsh",
    name: "crt.sh Certificate Transparency",
    category: "Domain & DNS",
    description: "Free public Certificate Transparency log search for discovering every issued SSL/TLS subdomain.",
    url: "https://crt.sh",
    searchUrlTemplate: "https://crt.sh/?q={target}",
    badge: "Passive Scout",
  },
  {
    id: "dnsdumpster",
    name: "DNSDumpster",
    category: "Domain & DNS",
    description: "Domain research tool that discovers DNS records, MX routing, and network maps.",
    url: "https://dnsdumpster.com",
    searchUrlTemplate: "https://dnsdumpster.com/",
  },
  {
    id: "securitytrails",
    name: "SecurityTrails",
    category: "Domain & DNS",
    description: "Historical DNS records and domain intelligence database.",
    url: "https://securitytrails.com",
    searchUrlTemplate: "https://securitytrails.com/domain/{target}/dns",
  },
  {
    id: "urlscan",
    name: "urlscan.io",
    category: "Domain & DNS",
    description: "Free public website scanner and domain relationship analyzer.",
    url: "https://urlscan.io",
    searchUrlTemplate: "https://urlscan.io/search/#page.domain%3A{target}",
  },
  {
    id: "virustotal",
    name: "VirusTotal Community",
    category: "Domain & DNS",
    description: "Aggregated domain reputation, passive DNS, and community detection graph.",
    url: "https://www.virustotal.com",
    searchUrlTemplate: "https://www.virustotal.com/gui/domain/{target}",
  },

  // IP, Network & ASN
  {
    id: "bgpview",
    name: "BGPView",
    category: "IP & Network",
    description: "Autonomous System (ASN) lookup, BGP prefix announcements, and upstream routing telemetry.",
    url: "https://bgpview.io",
    searchUrlTemplate: "https://bgpview.io/search/{target}",
    badge: "Network",
  },
  {
    id: "he_bgp",
    name: "Hurricane Electric BGP Toolkit",
    category: "IP & Network",
    description: "Authoritative internet routing, prefix allocations, and ASN peering graphs.",
    url: "https://bgp.he.net",
    searchUrlTemplate: "https://bgp.he.net/ip/{target}",
  },
  {
    id: "ipinfo",
    name: "IPinfo.io",
    category: "IP & Network",
    description: "Fast public IP geolocation, hosting provider, and carrier allocation details.",
    url: "https://ipinfo.io",
    searchUrlTemplate: "https://ipinfo.io/{target}",
  },
  {
    id: "abuseipdb",
    name: "AbuseIPDB",
    category: "IP & Network",
    description: "Central IP address reputation database with crowd-sourced abuse reports.",
    url: "https://www.abuseipdb.com",
    searchUrlTemplate: "https://www.abuseipdb.com/check/{target}",
  },

  // Usernames & Identity
  {
    id: "whatsmyname",
    name: "WhatsMyName Web",
    category: "Usernames",
    description: "Fast multi-platform username enumeration across 500+ public websites.",
    url: "https://whatsmyname.app",
    searchUrlTemplate: "https://whatsmyname.app/?q={target}",
    badge: "Sherlock/WMN",
  },
  {
    id: "namechk",
    name: "Namechk",
    category: "Usernames",
    description: "Public username availability and social media presence scanner.",
    url: "https://namechk.com",
    searchUrlTemplate: "https://namechk.com",
  },
  {
    id: "github_search",
    name: "GitHub Code & User Search",
    category: "Usernames",
    description: "Public repositories, commit logs, author email associations, and developer personas.",
    url: "https://github.com",
    searchUrlTemplate: "https://github.com/search?q={target}&type=users",
  },

  // Email & Breaches
  {
    id: "hibp",
    name: "Have I Been Pwned",
    category: "Email & Breaches",
    description: "Safe, lawful check for public breach metadata and paste references.",
    url: "https://haveibeenpwned.com",
    searchUrlTemplate: "https://haveibeenpwned.com/account/{target}",
    badge: "Integrity",
  },
  {
    id: "hunter",
    name: "Hunter.io Email Finder",
    category: "Email & Breaches",
    description: "Discovers corporate email naming formats and verified domain email contacts.",
    url: "https://hunter.io",
    searchUrlTemplate: "https://hunter.io/try/search/{target}",
  },

  // Geolocation & Mapping
  {
    id: "osm",
    name: "OpenStreetMap",
    category: "Geolocation",
    description: "Open geographic map database with high-resolution coordinates and building data.",
    url: "https://www.openstreetmap.org",
    searchUrlTemplate: "https://www.openstreetmap.org/search?query={target}",
  },
  {
    id: "suncalc",
    name: "SunCalc Solar Position",
    category: "Geolocation",
    description: "Solar trajectory, shadow length, and sunrise/sunset verification for photo geolocation.",
    url: "https://www.suncalc.org",
  },
  {
    id: "dualmaps",
    name: "DualMaps Combined Imagery",
    category: "Geolocation",
    description: "Simultaneous aerial imagery, street level views, and topographic maps.",
    url: "https://www.dualmaps.com",
  },

  // Archives & Historical Footprints
  {
    id: "wayback",
    name: "Wayback Machine",
    category: "Archives",
    description: "Digital archive of the World Wide Web with over 800 billion saved public snapshots.",
    url: "https://web.archive.org",
    searchUrlTemplate: "https://web.archive.org/web/*/{target}",
    badge: "Zero Trace",
  },
  {
    id: "archive_today",
    name: "Archive.today",
    category: "Archives",
    description: "On-demand webpage snapshot archive, resistant to paywalls and live site takedowns.",
    url: "https://archive.today",
    searchUrlTemplate: "https://archive.today/{target}",
  },

  // Corporate & Government Registries
  {
    id: "opencorporates",
    name: "OpenCorporates",
    category: "Corporate",
    description: "The largest open database of companies and corporate officers in the world.",
    url: "https://opencorporates.com",
    searchUrlTemplate: "https://opencorporates.com/companies?q={target}",
  },
  {
    id: "sec_edgar",
    name: "SEC EDGAR Filings",
    category: "Corporate",
    description: "Official United States SEC corporate regulatory disclosures and 10-K filings.",
    url: "https://www.sec.gov/edgar/searchedgar/companysearch",
    searchUrlTemplate: "https://www.sec.gov/edgar/searchedgar/companysearch?q={target}",
  },
];

const CATEGORIES = [
  "ALL",
  "Search Engines",
  "Domain & DNS",
  "IP & Network",
  "Usernames",
  "Email & Breaches",
  "Geolocation",
  "Archives",
  "Corporate",
];

export const SourcesCatalog: React.FC<SourcesCatalogProps> = ({ currentTarget = "" }) => {
  const [activeCategory, setActiveCategory] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [targetOverride, setTargetOverride] = useState(currentTarget);

  const filteredSources = OSINT_SOURCES.filter((s) => {
    if (activeCategory !== "ALL" && s.category !== activeCategory) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        s.name.toLowerCase().includes(q) ||
        s.description.toLowerCase().includes(q) ||
        s.category.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const getTargetUrl = (source: OSINTSource) => {
    if (!source.searchUrlTemplate) return source.url;
    const t = targetOverride.trim() || "example.com";
    return source.searchUrlTemplate.replace("{target}", encodeURIComponent(t));
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#080b12] overflow-y-auto select-text font-sans p-6">
      <div className="max-w-7xl mx-auto w-full space-y-6">
        {/* Header */}
        <div className="bg-[#0e1424] border border-[#1b253d] rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-mono mb-2">
                <Database className="w-3.5 h-3.5" />
                <span>OSINTSEARCH.ORG INTELLIGENCE DIRECTORY</span>
              </div>
              <h1 className="text-xl md:text-2xl font-bold font-mono text-slate-100">
                Curated Global OSINT Sources & Search Engines
              </h1>
              <p className="text-xs text-slate-400 font-mono mt-1 max-w-2xl">
                Comprehensive directory of verified public intelligence resources, search engines, and passive scouts.
                Generates exact pivot query URLs for your target with zero trace.
              </p>
            </div>

            {/* Quick target input */}
            <div className="bg-[#141d33] border border-[#223152] rounded-xl p-3 flex items-center space-x-2.5">
              <span className="text-xs text-slate-400 font-mono whitespace-nowrap">Pivot Target:</span>
              <input
                type="text"
                value={targetOverride}
                onChange={(e) => setTargetOverride(e.target.value)}
                placeholder="domain, user, or IP..."
                className="bg-[#0b101c] border border-[#26375c] rounded-lg px-2.5 py-1 text-xs font-mono text-sky-300 placeholder-slate-500 focus:outline-none focus:border-sky-500 w-44"
              />
            </div>
          </div>

          {/* Category Tabs & Filter Search */}
          <div className="mt-6 pt-5 border-t border-[#1b253d] flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-1.5">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-3 py-1 rounded-lg text-xs font-mono transition-colors ${
                    activeCategory === cat
                      ? "bg-sky-500 text-slate-950 font-bold shadow-sm"
                      : "bg-[#141d33] text-slate-400 hover:text-slate-200 hover:bg-[#1a2642] border border-[#202e4d]"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search catalog..."
                className="bg-[#141d33] border border-[#202e4d] rounded-lg pl-8 pr-3 py-1.5 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 w-52"
              />
            </div>
          </div>
        </div>

        {/* Source Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSources.map((source) => {
            const pivotUrl = getTargetUrl(source);
            return (
              <div
                key={source.id}
                className="bg-[#0d1220] border border-[#192238] hover:border-sky-500/50 rounded-xl p-4 flex flex-col justify-between transition-all group shadow-sm hover:shadow-lg"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                      <h3 className="text-sm font-bold font-mono text-slate-100 group-hover:text-sky-300 transition-colors">
                        {source.name}
                      </h3>
                    </div>
                    {source.badge && (
                      <span className="px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/30 text-[10px] font-mono font-semibold">
                        {source.badge}
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mt-1">
                    {source.category}
                  </span>
                  <p className="text-xs text-slate-300 font-sans mt-2.5 leading-relaxed">
                    {source.description}
                  </p>
                </div>

                <div className="mt-5 pt-3 border-t border-[#161e31] flex items-center justify-between">
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[11px] font-mono text-slate-400 hover:text-slate-200 transition-colors"
                  >
                    Direct Site
                  </a>

                  <a
                    href={pivotUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-xs font-mono font-semibold transition-all group-hover:bg-sky-500 group-hover:text-slate-950"
                  >
                    <span>Launch Pivot</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
