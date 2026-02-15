# CivicOS Institute Website

[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://civicos-institute.org)

Official website for CivicOS Institute, a nonprofit research organization dedicated to civic technology, open data systems, and digital public infrastructure.

## Live Site

**URL:** https://civicos-institute.org

## Built With

- **Jekyll** - Static site generator
- **GitHub Pages** - Hosting
- **Minima Theme** - Base theme with custom styling
- **SCSS** - Custom styles

## Structure

```
.
├── _config.yml          # Jekyll configuration
├── _layouts/
│   └── default.html     # Main layout template
├── assets/
│   └── css/
│       └── style.scss   # Custom styles
├── index.md             # Homepage
├── about.md             # About page
├── research.md          # Research & projects
├── contact.md           # Contact page
├── CNAME                # Custom domain config
└── README.md            # This file
```

## Local Development

1. **Install dependencies:**
   ```bash
   bundle install
   ```

2. **Run locally:**
   ```bash
   bundle exec jekyll serve
   ```

3. **View at:** http://localhost:4000

## Content Updates

To update content, edit the Markdown files:
- `index.md` - Homepage
- `about.md` - About page
- `research.md` - Research page
- `contact.md` - Contact page

Changes pushed to the `main` branch will automatically deploy to the live site.

## Customization

- Edit `_config.yml` for site settings
- Modify `assets/css/style.scss` for styling
- Update `_layouts/default.html` for structure

## License

Content: © 2025 CivicOS Institute

Code: MIT License

## Contributing

This is the official website repository for CivicOS Institute. For corrections or suggestions, please open an issue or contact us at NCerbone@civicos-institute.org.

---

**CivicOS Institute**  
A Florida nonprofit corporation in formation.  
501(c)(3) status pending.
