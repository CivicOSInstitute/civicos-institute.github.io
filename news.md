---
layout: default
title: News
---

<div class="wrapper">
  <h1>GovTech & AI Policy News</h1>
  <p class="tagline">Live aggregation of news at the intersection of government, technology, and artificial intelligence.</p>
  
  <div id="news-container">
    <div class="loading">Loading latest news...</div>
  </div>
  
  <div class="news-sources">
    <h3>Sources</h3>
    <ul>
      <li><a href="https://fedscoop.com" target="_blank">FedScoop</a> — Federal technology news</li>
      <li><a href="https://nextgov.com" target="_blank">NextGov</a> — Federal IT and cybersecurity</li>
      <li><a href="https://www.govexec.com" target="_blank">Government Executive</a> — Federal management</li>
      <li><a href="https://www.route-fifty.com" target="_blank">Route Fifty</a> — State & local government tech</li>
      <li><a href="https://techpolicy.press" target="_blank">Tech Policy Press</a> — Technology & democracy</li>
    </ul>
  </div>
</div>

<script>
// RSS Feed sources
const feeds = [
  { name: "FedScoop", url: "https://fedscoop.com/feed/" },
  { name: "NextGov", url: "https://www.nextgov.com/feed/" },
  { name: "Government Executive", url: "https://www.govexec.com/feed/" },
  { name: "Route Fifty", url: "https://www.route-fifty.com/feed/" },
  { name: "Tech Policy Press", url: "https://techpolicy.press/feed" }
];

const newsContainer = document.getElementById('news-container');
const allItems = [];

// Fetch RSS via rss2json API
async function fetchFeed(feed) {
  try {
    const response = await fetch(`https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(feed.url)}`);
    const data = await response.json();
    if (data.status === 'ok' && data.items) {
      return data.items.map(item => ({
        ...item,
        source: feed.name,
        pubDate: new Date(item.pubDate)
      }));
    }
    return [];
  } catch (error) {
    console.error(`Error fetching ${feed.name}:`, error);
    return [];
  }
}

// Load all feeds and render
async function loadNews() {
  newsContainer.innerHTML = '<div class="loading">Loading latest news...</div>';
  
  const feedPromises = feeds.map(fetchFeed);
  const results = await Promise.allSettled(feedPromises);
  
  results.forEach(result => {
    if (result.status === 'fulfilled') {
      allItems.push(...result.value);
    }
  });
  
  // Sort by date, newest first
  allItems.sort((a, b) => b.pubDate - a.pubDate);
  
  // Take top 30 items
  const recentItems = allItems.slice(0, 30);
  
  if (recentItems.length === 0) {
    newsContainer.innerHTML = '<div class="error">Unable to load news feeds. Please try again later.</div>';
    return;
  }
  
  // Render items
  const html = recentItems.map(item => {
    const dateStr = item.pubDate.toLocaleDateString('en-US', { 
      month: 'short', day: 'numeric', year: 'numeric' 
    });
    // Strip HTML tags from description
    const description = item.description?.replace(/<[^>]*>/g, '').substring(0, 200) + '...' || '';
    
    return `
      <article class="news-item">
        <div class="news-meta">
          <span class="news-source">${item.source}</span>
          <span class="news-date">${dateStr}</span>
        </div>
        <h2 class="news-title">
          <a href="${item.link}" target="_blank" rel="noopener noreferrer">${item.title}</a>
        </h2>
        <p class="news-description">${description}</p>
      </article>
    `;
  }).join('');
  
  newsContainer.innerHTML = html;
}

// Load on page load
loadNews();
</script>

<style>
.loading {
  text-align: center;
  padding: 40px;
  color: #666;
  font-style: italic;
}

.error {
  text-align: center;
  padding: 40px;
  color: #d32f2f;
}

.news-item {
  border-bottom: 1px solid #e0e0e0;
  padding: 20px 0;
}

.news-item:last-child {
  border-bottom: none;
}

.news-meta {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 8px;
}

.news-source {
  font-weight: 600;
  color: #1565c0;
  margin-right: 15px;
}

.news-date {
  color: #888;
}

.news-title {
  font-size: 1.25rem;
  margin: 0 0 10px 0;
  line-height: 1.3;
}

.news-title a {
  color: #212529;
  text-decoration: none;
  transition: color 0.2s;
}

.news-title a:hover {
  color: #1565c0;
}

.news-description {
  color: #555;
  line-height: 1.5;
  margin: 0;
}

.news-sources {
  margin-top: 40px;
  padding-top: 30px;
  border-top: 2px solid #e0e0e0;
}

.news-sources h3 {
  margin-bottom: 15px;
}

.news-sources ul {
  list-style: none;
  padding: 0;
}

.news-sources li {
  padding: 5px 0;
}

.news-sources a {
  color: #1565c0;
  text-decoration: none;
}

.news-sources a:hover {
  text-decoration: underline;
}
</style>
