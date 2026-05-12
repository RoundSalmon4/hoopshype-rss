# HoopsHype RSS Feeds

Auto-generated RSS feeds for NBA trade rumors and free agency buzz from HoopsHype.

## Features

- **Rumor tracking** - Latest NBA trade rumors and free agency news
- **Team-specific feeds** - Separate feeds for all 30 NBA teams
- **Auto-updated** - Updated via GitHub Actions on demand
- **Backfill support** - Fetches all available rumors from the last 48 hours on every run
- **Dedup** - Previously-seen rumors are tracked to prevent duplicates

## Feeds Available

### All Rumors Feed
- `/rss/all.xml` - All NBA rumors in one feed

### Team Feeds
- `/rss/teams/<abbrev>.xml` (e.g., `/rss/teams/lal.xml`, `/rss/teams/bos.xml`)

### Team Abbreviations

| Team | Abbrev | Team | Abbrev |
|------|--------|------|--------|
| Atlanta Hawks | atl | Miami Heat | mia |
| Boston Celtics | bos | Milwaukee Bucks | mil |
| Brooklyn Nets | bkn | Minnesota Timberwolves | min |
| Charlotte Hornets | cha | New Orleans Pelicans | nop |
| Chicago Bulls | chi | New York Knicks | nyk |
| Cleveland Cavaliers | cle | Oklahoma City Thunder | okc |
| Dallas Mavericks | dal | Orlando Magic | orl |
| Denver Nuggets | den | Philadelphia 76ers | phi |
| Detroit Pistons | det | Phoenix Suns | phx |
| Golden State Warriors | gsw | Portland Trail Blazers | por |
| Houston Rockets | hou | Sacramento Kings | sac |
| Indiana Pacers | ind | San Antonio Spurs | sas |
| Los Angeles Clippers | lac | Toronto Raptors | tor |
| Los Angeles Lakers | lal | Utah Jazz | uta |
| Memphis Grizzlies | mem | Washington Wizards | was |

## Example Feed URLs

- All rumors: `https://raw.githubusercontent.com/RoundSalmon4/hoopshype-rss/main/rss/all.xml`
- Lakers rumors: `https://raw.githubusercontent.com/RoundSalmon4/hoopshype-rss/main/rss/teams/lal.xml`
- Celtics rumors: `https://raw.githubusercontent.com/RoundSalmon4/hoopshype-rss/main/rss/teams/bos.xml`

## How It Works

A GitHub Actions workflow fetches HoopsHype's news sitemap to discover all recently
published rumor article URLs. For each new article (not previously seen), the script
scrapes the article page, extracts team association from embedded JSON-LD metadata,
and generates RSS 2.0 XML files organized by team.

## Limitations

- **Team coverage depends on tagging.** A rumor appears in a team feed only if
  HoopsHype's JSON-LD keyword metadata includes that team's name. General
  league-wide rumors may not go into any team feed.
- **Only the last 48 hours of rumors are fetched** (from the news sitemap). Older
  articles are not backfilled beyond this window.

## License

MIT
