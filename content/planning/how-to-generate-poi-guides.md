# How to Generate Points of Interest Guides for Tour Segments

**NAE 2025 Project Documentation**

*A workflow for creating comprehensive POI guides with interactive maps*

---

## Quick Start

**What you'll create:**
- Detailed markdown POI guide (example: [Stages 96-100](nae25_stages_96-100_poi.md))
- CSV file with GPS coordinates (example: [attractions CSV](nae25_stages_96-100_attractions.csv))
- Interactive Google My Maps (example: [Stages 96-100 Map](https://www.google.com/maps/d/edit?mid=1zCfQQpARMXAqfcIlmfyXn0VxWPjQlYg&usp=sharing))

**Time required:** 2-4 hours per 5-stage section

**Tools needed:**
- Ride with GPS account (for NAE routes)
- Google account (for My Maps)
- Claude AI or similar research assistant
- Text editor

---

## Overview

This document explains the process used to create comprehensive POI (Points of Interest) guides for bicycle tour segments. The workflow was developed for NAE 2025 (North American Epic) and uses Stages 96-100 (Mexico City to Oaxaca) as a working example.

The process combines route data analysis, web research, and mapping tools to create:
1. A detailed markdown guide with historical/cultural information
2. A CSV file with GPS coordinates for mapping
3. An interactive Google My Maps visualization

## Step 1: Gather Route Data

### Export Routes from Ride with GPS

**For NAE 2025, routes are available via the tour event page:**

1. **Access the Event:**
   - Open [NAE25 Event on Ride with GPS](https://ridewithgps.com/events/303231-2025-north-american-epic?privacy_code=pZsFqEDhutNEJRxM2OKlQFTg3ZzsRWku)
   - Browse to find your specific stage(s)

2. **Export Individual Stage:**
   - Click on a route/stage
   - Click **More** menu (three dots)
   - Select **Export as file**
   - Choose **Google Earth (KML)**
   - Download the `.kml` file
   - Repeat for each stage in your section

**Alternative Export Options:**
- **GPX format** works fine but creates larger files
- **KML is recommended** - more lightweight and faster to upload to Google My Maps

### Consolidate Multiple Routes (Optional)

If you want a single KML file containing multiple stages:

1. **Create Temporary Map:**
   - Go to [Google My Maps](https://www.google.com/maps/d/)
   - Click **Create a New Map** (red button, upper left)
   - Title it (e.g., "NAE25_Stages_96-100")

2. **Import Each Stage:**
   - Under first "Untitled Layer", click **Import**
   - Upload KML from first stage
   - Layer name changes to route name from Ride with GPS
   - Click **Add layer** button
   - Repeat import for each additional stage

3. **Export Combined KML:**
   - Click three-dot menu next to map title (in legend)
   - Select **Export to KML/KMZ**
   - Choose **Entire Map**
   - Check **"Export as KML instead of KMZ"**
   - Download
   - File saves as `[map-title].kml` (e.g., `NAE25_Stages_96-100.kml`)

**What You Need:**
- KML route file(s) from Ride with GPS or tour operator
- Itinerary with stage details (dates, distances, cities)
- Basic knowledge of the region you'll be cycling through

**Example Files Used in This Guide:**
- `NAE_stages_96-100.kml` - Combined route geometry for 5 stages
- `nae25_sections811.csv` - Stage details including dates, distances, elevation

## Step 2: Parse the Route File

**Purpose:** Extract key waypoints and understand the route geography.

**Using Python (optional):**
```python
import xml.etree.ElementTree as ET

def parse_kml(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    stages = []
    for placemark in root.findall('.//kml:Placemark', ns):
        name = placemark.find('kml:name', ns).text
        coords = placemark.find('.//kml:LineString/kml:coordinates', ns)
        # Extract start/end coordinates
        # ... processing logic
    return stages
```

**Manual Alternative:**
- Open KML in Google Earth or similar tool
- Note the start/end cities for each stage
- Record approximate route path

## Step 3: Research Points of Interest

**Using Claude (or similar AI assistant):**

Provide the context:
```
I have a bicycle tour from [Start City] to [End City] over [X] days.
Here are the stages:
[paste stage data]

Can you find points of interest along this route?
```

**Research Strategy:**
1. **Major destinations:** Historical sites, UNESCO sites, museums
2. **Route attractions:** Sites visible/accessible from the cycling route
3. **Rest day cities:** Activities and events for rest days
4. **Cultural context:** Regional history, traditions, cuisine
5. **Practical info:** Markets, viewpoints, craft villages

**Key Search Patterns:**
- "[City name] attractions history"
- "[Region] archaeological sites cycling"
- "[City] [specific dates] events festivals"
- GPS coordinates for major sites

## Step 4: Structure the Markdown Document

**Recommended Structure:**

```markdown
# Tour Section: Points of Interest
## [Start] to [End]
**Dates**

**[View Interactive Map - Tour Name](LINK)**

---

## Route Overview
[Table with stages, dates, distances]

---

## Stage XX: [City A] to [City B]
**Date**

### Major Highlights
- Site 1 with details
- Site 2 with details

### Route Notes
- Terrain, elevation, conditions

---

## Rest Day Events
### [City] - [Date]
- Events happening
- Recommended activities

---

## Regional Context
- Cultural information
- Historical timeline
- Practical tips
```

**Content Guidelines:**
- Be specific with dates (your actual travel dates)
- Include GPS coordinates for major sites
- Add practical details (opening hours, access, costs where known)
- Provide cultural context (history, significance)
- Note timing considerations (e.g., post-festival periods)

## Step 5: Create CSV for Mapping

**Format:**
```csv
Name,Location,Brief Description
Site Name,"lat, lon","Description under 200 chars"
```

**Key Points:**
- Use decimal degrees format: `19.0575, -98.3019`
- Keep descriptions concise (Google My Maps has character limits)
- Include 15-25 sites for a multi-day tour section
- Order logically (by geography or chronology)

**Finding Coordinates:**

Web search: `"[Site name]" GPS coordinates lat lon`

Common patterns:
- Official sites often list coordinates
- Wikipedia has coordinates for major sites
- Google Maps: right-click → "What's here?"

**Tools:**
- latitude.to - Shows coordinates from Wikipedia
- gps-coordinates.net - Search by address
- Google Maps - Right-click for coordinates

## Step 6: Create Google My Maps

**Instructions for End Users:**

1. **Import CSV:**
   - Go to [Google My Maps](https://www.google.com/maps/d/)
   - Click "Create a New Map"
   - Name your map (e.g., "NAE 2025 Stages 96-100")
   - Click "Import" in left panel
   - Upload your CSV file

2. **Configure Import:**
   - **Position columns**: Select "Location"
   - **Marker title**: Select "Name"
   - Google auto-parses "lat, lon" format

3. **Customize Map:**
   - Click on layer name to rename
   - Click on individual markers to edit
   - Change marker colors/icons by category
   - Add route lines (draw or import GPX)
   - Add photos to markers

4. **Share Map:**
   - Click "Share" button
   - Set visibility (Anyone with link / Public)
   - Copy sharing link
   - Get embed code if needed

5. **Map URL Format:**
   - Edit URL: `https://www.google.com/maps/d/edit?mid=YOUR_MAP_ID&usp=sharing`
   - View URL: `https://www.google.com/maps/d/viewer?mid=YOUR_MAP_ID&usp=sharing`

## Step 7: Link Map in Documentation

Add to the top of your markdown file:

```markdown
# Tour Section: Points of Interest

**[View Interactive Map - Tour Name](https://www.google.com/maps/d/edit?mid=YOUR_MAP_ID)**

---
```

## Tips for Success

**Research:**
- Use specific date searches for events: "[City] November 2025 events"
- Check local tourism sites and museum websites
- Look for "things to do" and "attractions near [city]" articles
- Cross-reference multiple sources for coordinates

**Writing:**
- Write for your audience (fellow cyclists, not general tourists)
- Include practical cycling considerations (terrain, weather, rest stops)
- Note seasonal factors (festivals, weather, tourist crowds)
- Add personal context (why this matters to your tour)

**Mapping:**
- Group markers by category (Archaeological, Museums, Markets, etc.)
- Use different colors for different categories
- Include nearby facilities (bike shops, hospitals) if relevant
- Test the map on mobile (where riders will actually use it)

**Collaboration:**
- Share editable links with tour group for contributions
- Encourage others to add local knowledge
- Create template CSV for other tour sections
- Document your process for future segments

## Example Output

**Markdown Document:**
- Comprehensive POI guide (500-1000 lines)
- Organized by stage and category
- Includes historical context, practical info, cultural notes
- Links to interactive map

**CSV File:**
- 20-30 key attractions
- Ready for Google My Maps import
- GPS coordinates in decimal degrees

**Google My Maps:**
- Interactive visualization
- Color-coded by category
- Shareable with tour group
- Mobile-accessible during tour

## Automating for Multiple Segments

For tour operators or repeat use:

1. **Template Approach:**
   - Create markdown template with consistent structure
   - Develop CSV template with standard fields
   - Document research workflow

2. **Batch Processing:**
   - Process multiple KML files at once
   - Create Python script to extract waypoints
   - Generate skeleton markdown files

3. **Collaborative Research:**
   - Assign segments to different riders
   - Use GitHub for version control
   - Create pull request workflow for contributions

4. **Integration:**
   - Link POI guides in tour documentation
   - Embed maps in tour website/blog
   - Export to GPX for bike computers
   - Generate printable PDF versions

## Resources

**Mapping Tools:**
- Google My Maps - Interactive maps
- Google Earth - KML visualization
- GPSVisualizer - Route conversion
- Ride with GPS - Cycling-specific routes

**Research Sources:**
- UNESCO World Heritage list
- Wikipedia (with coordinates)
- Local tourism websites
- TripAdvisor (for practical details)
- Atlas Obscura (unique attractions)
- AllTrails (hiking/viewpoints)

**Data Formats:**
- KML - Route files from tour operators
- GPX - GPS exchange format
- CSV - Spreadsheet data
- GeoJSON - Geographic data (advanced)

## Version History

**v2.0 - November 2025**
- Added detailed Ride with GPS export instructions
- Documented KML consolidation workflow
- Cleaned up formatting and structure
- Added Quick Start section with examples
- Collaborative documentation by NAE 2025 riders

**v1.0 - November 2025**
- Initial process documentation
- Based on NAE 2025 Stages 96-100 workflow (Mexico City to Oaxaca)
- Used Claude AI for research and content generation
- Google My Maps for visualization

---

**Contributors:**
- Mike (NAE 2025 sectional rider, Stages 83-128)
- Process refined through real-world tour planning

**Example Outputs:**
- [Stages 96-100 POI Guide](nae25_stages_96-100_poi.md)
- [Stages 96-100 Attractions CSV](nae25_stages_96-100_attractions.csv)
- [Stages 96-100 Interactive Map](https://www.google.com/maps/d/edit?mid=1zCfQQpARMXAqfcIlmfyXn0VxWPjQlYg&usp=sharing)

---

*This process can be adapted for any multi-day tour segment. The key is combining route data, thorough research, and interactive mapping to create a useful resource for tour participants.*
