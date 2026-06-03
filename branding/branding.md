# renaissance Branding

```css
/* ============================================================
   BRAND — renaissance (YouTube)
   ============================================================ */

[data-brand="renaissance"] {
  --brand-primary: #4A235A;
  --brand-secondary: #F9E79F;
  --brand-accent: #F9E79F;
  --brand-bg: #0D0D1A;
  --brand-text: #E8E0EC;
  --brand-muted: #9B8EA0;
  --brand-font-heading: Georgia, "Times New Roman", serif;
  --brand-font-body: Georgia, "Times New Roman", serif;
  --brand-border: #F9E79F;
  --brand-radius: 4px;
}

[data-brand="renaissance"] h1 {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 2.5rem;
  font-weight: 700;
  color: #F9E79F;
  line-height: 1.2;
  letter-spacing: 0.5px;
  font-style: italic;
}

[data-brand="renaissance"] h2 {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.625rem;
  font-weight: 700;
  color: #F9E79F;
  line-height: 1.3;
}

[data-brand="renaissance"] h3 {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.125rem;
  font-weight: 600;
  color: #E8E0EC;
  line-height: 1.4;
  font-style: italic;
}

[data-brand="renaissance"] p,
[data-brand="renaissance"] li {
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1rem;
  font-weight: 400;
  color: #E8E0EC;
  line-height: 1.85;
}

/* ============================================================
   SHARED UTILITY CLASSES
   ============================================================ */

.brand-card {
  background: var(--brand-bg);
  color: var(--brand-text);
  border: 1px solid var(--brand-border);
  border-radius: var(--brand-radius);
  padding: 1.5rem;
}

.brand-btn {
  background: var(--brand-primary);
  color: var(--brand-bg);
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: var(--brand-radius);
  font-family: var(--brand-font-body);
  font-size: 0.875rem;
  cursor: pointer;
}

.brand-btn:hover {
  opacity: 0.9;
}

.brand-heading {
  font-family: var(--brand-font-heading);
  color: var(--brand-primary);
  line-height: 1.2;
}

.brand-link {
  color: var(--brand-primary);
  text-decoration: underline;
  text-decoration-color: var(--brand-accent);
}

.brand-muted {
  color: var(--brand-muted);
}

.brand-accent {
  color: var(--brand-accent);
}

.brand-post {
  background: var(--brand-bg);
  color: var(--brand-text);
  border: 1px solid var(--brand-border);
  border-radius: var(--brand-radius);
  padding: 1.25rem;
  font-family: var(--brand-font-body);
  max-width: 600px;
}

.brand-post h3 {
  font-family: var(--brand-font-heading);
  color: var(--brand-primary);
  margin: 0 0 0.5rem;
}

.brand-post .meta {
  color: var(--brand-muted);
  font-size: 0.8rem;
}

.brand-hashtag {
  color: var(--brand-primary);
  opacity: 0.8;
  font-size: 0.8rem;
}
```
