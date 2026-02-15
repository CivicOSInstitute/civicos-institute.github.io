---
layout: default
title: Home
---

<section class="hero">
  <div class="wrapper">
    <img src="/assets/images/logo.png" alt="CivicOS Institute Logo" style="max-height: 120px; width: auto; margin-bottom: 20px;">
    <p class="tagline">
      Advancing civic technology, open data, and digital public infrastructure 
      for more transparent, accountable, and accessible democratic institutions.
    </p>
    <p style="margin-top: 30px;">
      <a href="/about/" class="btn">Learn More</a>
      <a href="https://www.gofundme.com/f/help-launch-the-civicos-institute" class="btn btn-primary" style="margin-left: 15px;">Support Our Work</a>
    </p>
    <p style="margin-top: 20px;">
      <a href="https://x.com/CivicOSinstitut" class="btn" style="background: #000; color: #fff;">Follow us on X</a>
    </p>
  </div>
</section>

<section class="latest-news">
  <div class="wrapper">
    <h2>Latest in GovTech & AI Policy</h2>
    <div id="top-stories">
      <div class="loading-small">Loading...</div>
    </div>
    <p style="text-align: center; margin-top: 20px;">
      <a href="/news.html" class="btn">View All News</a>
    </p>
  </div>
</section>

<section class="newsletter-section">
  <div class="wrapper">
    <h2>Stay in the Loop</h2>
    <p class="newsletter-tagline">Weekly insights on how technology is reshaping public institutions — plus updates on our work to make government work better for everyone.</p>
    <button class="btn btn-primary" onclick="openNewsletterModal()">Subscribe to Our Newsletter</button>
  </div>
</section>

<!-- Newsletter Modal -->
<div id="newsletterModal" class="modal">
  <div class="modal-content">
    <span class="close" onclick="closeNewsletterModal()">&times;</span>
    <h3>Subscribe to Our Newsletter</h3>
    <p>Get weekly updates delivered to your inbox.</p>
    <form id="newsletterForm" action="https://formspree.io/f/mbdaobda" method="POST">
      <input type="email" name="email" placeholder="Enter your email" required class="form-input">
      <input type="text" name="name" placeholder="Your name (optional)" class="form-input">
      <button type="submit" class="btn btn-primary" style="width: 100%;">Subscribe</button>
    </form>
    <p class="form-note">We respect your privacy. Unsubscribe anytime.</p>
  </div>
</div>

<div class="wrapper">
  <div class="mission-box">
    <h2>Our Mission</h2>
    <p style="font-size: 1.1rem; margin-bottom: 0;">
      CivicOS Institute is a nonprofit research organization dedicated to developing open-source 
      platforms, educating policymakers, and building communities of practice around civic technology 
      and open government. We believe that collective impact requires shared accountability and 
      that technology should serve the public interest.
    </p>
  </div>

  <h2>Focus Areas</h2>
  
  <div class="focus-grid">
    <div class="focus-card">
      <h3>Research</h3>
      <p>
        Conducting cutting-edge research in civic technology, open data systems, 
        and digital public infrastructure to inform policy and practice.
      </p>
    </div>
    
    <div class="focus-card">
      <h3>Open Source</h3>
      <p>
        Developing and maintaining open-source software platforms that enable 
        civic engagement, transparency, and democratic participation.
      </p>
    </div>
    
    <div class="focus-card">
      <h3>Education</h3>
      <p>
        Educating the public, policymakers, and technologists on best practices 
        in civic technology and open government standards.
      </p>
    </div>
    
    <div class="focus-card">
      <h3>Collaboration</h3>
      <p>
        Partnering with public sector entities, academic institutions, and civil 
        society to improve civic systems and democratic institutions.
      </p>
    </div>
  </div>

  <h2>Current Status</h2>
  
  <p>
    <span class="status-badge pending">Organization in Formation</span>
  </p>
  
  <p>
    CivicOS Institute is currently incorporated in Florida and has submitted our 
    application for 501(c)(3) federal tax-exempt status to the IRS. We expect to 
    receive our determination letter within 8-12 weeks.
  </p>
  
  <p>
    In the meantime, we are actively developing our research agenda, building partnerships, 
    and laying the groundwork for our initial projects. We welcome collaboration with 
    researchers, technologists, government officials, and civic organizations who share 
    our commitment to improving democratic institutions through technology.
  </p>

  <h2>Get Involved</h2>
  
  <p>
    There are many ways to support the CivicOS Institute:
  </p>
  
  <ul>
    <li><strong>Donate:</strong> Help fund our research and development efforts</li>
    <li><strong>Collaborate:</strong> Partner with us on research projects</li>
    <li><strong>Contribute:</strong> Participate in our open-source development</li>
    <li><strong>Connect:</strong> Share your expertise and insights</li>
  </ul>
  
  <p style="margin-top: 30px; text-align: center;">
    <a href="/contact/" class="btn btn-primary">Contact Us</a>
  </p>
</div>

<script>
// Fetch top 3 stories for homepage
async function loadTopStories() {
  const container = document.getElementById('top-stories');
  
  const feeds = [
    { name: "FedScoop", url: "https://fedscoop.com/feed/" },
    { name: "NextGov", url: "https://www.nextgov.com/feed/" },
    { name: "Government Executive", url: "https://www.govexec.com/feed/" },
    { name: "Route Fifty", url: "https://www.route-fifty.com/feed/" },
    { name: "Tech Policy Press", url: "https://techpolicy.press/feed" }
  ];
  
  const allItems = [];
  
  const feedPromises = feeds.map(async (feed) => {
    try {
      const response = await fetch(`https://api.rss2json.com/v1/api.json?rss_url=${encodeURIComponent(feed.url)}`);
      const data = await response.json();
      if (data.status === 'ok' && data.items) {
        return data.items.map(item => ({
          title: item.title,
          link: item.link,
          source: feed.name,
          pubDate: new Date(item.pubDate)
        }));
      }
      return [];
    } catch (error) {
      return [];
    }
  });
  
  const results = await Promise.allSettled(feedPromises);
  results.forEach(result => {
    if (result.status === 'fulfilled') {
      allItems.push(...result.value);
    }
  });
  
  allItems.sort((a, b) => b.pubDate - a.pubDate);
  const top3 = allItems.slice(0, 3);
  
  if (top3.length > 0) {
    container.innerHTML = top3.map(item => {
      const dateStr = item.pubDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      return `
        <article class="story-item">
          <span class="story-source">${item.source}</span>
          <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="story-link">${item.title}</a>
          <span class="story-date">${dateStr}</span>
        </article>
      `;
    }).join('');
  } else {
    container.innerHTML = '<p class="no-stories">Unable to load stories. <a href="/news.html">View news page →</a></p>';
  }
}

loadTopStories();

// Newsletter Modal Functions
function openNewsletterModal() {
  document.getElementById('newsletterModal').style.display = 'block';
}

function closeNewsletterModal() {
  document.getElementById('newsletterModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
  const modal = document.getElementById('newsletterModal');
  if (event.target == modal) {
    modal.style.display = 'none';
  }
}
</script>

<style>
.latest-news {
  background: #f8f9fa;
  padding: 40px 0;
  margin-bottom: 40px;
}

.latest-news h2 {
  text-align: center;
  margin-bottom: 25px;
  font-size: 1.5rem;
}

.loading-small {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 20px;
}

.story-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px 0;
  border-bottom: 1px solid #e0e0e0;
}

.story-item:last-child {
  border-bottom: none;
}

.story-source {
  font-size: 0.75rem;
  font-weight: 600;
  color: #1565c0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  min-width: 100px;
  flex-shrink: 0;
}

.story-link {
  flex: 1;
  color: #212529;
  text-decoration: none;
  font-weight: 500;
  line-height: 1.4;
}

.story-link:hover {
  color: #1565c0;
}

.story-date {
  font-size: 0.85rem;
  color: #888;
  white-space: nowrap;
}

.no-stories {
  text-align: center;
  color: #666;
}

@media (max-width: 600px) {
  .story-item {
    flex-direction: column;
    gap: 5px;
  }
  
  .story-source {
    min-width: auto;
  }
  
  .story-date {
    align-self: flex-start;
  }
}

/* Newsletter Section */
.newsletter-section {
  background: linear-gradient(135deg, #1e3a5f 0%, #2c4a6e 100%);
  color: white;
  padding: 50px 0;
  text-align: center;
  margin-bottom: 40px;
}

.newsletter-section h2 {
  color: white;
  margin-bottom: 15px;
}

.newsletter-tagline {
  font-size: 1.1rem;
  opacity: 0.9;
  max-width: 600px;
  margin: 0 auto 25px auto;
  line-height: 1.5;
}

/* Modal Styles */
.modal {
  display: none;
  position: fixed;
  z-index: 1000;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
}

.modal-content {
  background-color: white;
  margin: 10% auto;
  padding: 30px;
  border-radius: 8px;
  width: 90%;
  max-width: 450px;
  position: relative;
}

.modal-content h3 {
  color: #1e3a5f;
  margin-top: 0;
}

.modal-content p {
  color: #555;
  margin-bottom: 20px;
}

.close {
  color: #aaa;
  float: right;
  font-size: 28px;
  font-weight: bold;
  position: absolute;
  right: 15px;
  top: 10px;
  cursor: pointer;
}

.close:hover,
.close:focus {
  color: #000;
  text-decoration: none;
  cursor: pointer;
}

.form-input {
  width: 100%;
  padding: 12px;
  margin-bottom: 15px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 1rem;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #1e3a5f;
}

.form-note {
  font-size: 0.85rem;
  color: #888;
  margin-top: 15px;
  margin-bottom: 0;
}
</style>
