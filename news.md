---
layout: default
title: News
---

<div class="wrapper">
  <h1>GovTech & AI Policy News</h1>
  <p class="tagline">Daily curated news at the intersection of government, technology, and artificial intelligence.</p>
  
  {% include news-widget.html %}
  
  <div class="news-footer">
    <p><strong>Sources:</strong> GovTech, StateScoop, FedScoop, NextGov, Government Executive, Route Fifty, Tech Policy Press, Code for America, Sunlight Foundation, MIT Tech Review</p>
    <p class="update-note">Updated daily at 7 AM EST | Also posted to <a href="https://discord.gg/tECtT9zeTT">Discord #civic-tech-news</a></p>
  </div>
</div>

<style>
.news-footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
  color: #666;
  font-size: 0.9rem;
}

.news-footer p {
  margin: 10px 0;
}

.update-note {
  font-style: italic;
}

.update-note a {
  color: #1565c0;
  text-decoration: none;
}

.update-note a:hover {
  text-decoration: underline;
}
</style>
