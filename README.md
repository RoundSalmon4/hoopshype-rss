# HoopsHype RSS Feeds

Auto-generated RSS feeds for NBA trade rumors and free agency buzz from HoopsHype.

## Features

- **Rumor tracking** - Latest NBA trade rumors and free agency news
- **Team-specific feeds** - Separate feeds for all 30 NBA teams
- **Auto-updated** - Refreshes every 30 minutes via GitHub Actions

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

This project uses the HoopsHype website's Next.js data route to fetch the latest rumors,
organizes them by team, and generates RSS 2.0 XML files. The feeds are updated every 30
minutes via a scheduled GitHub Actions workflow.

## License

MIT
