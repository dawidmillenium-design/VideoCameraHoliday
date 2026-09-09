#!/usr/bin/env python3
"""
Internal Linking Engine - Automatic Internal Linking with Graph Analysis

Creates a content graph from all pages across 11 languages, uses TF-IDF + cosine
similarity to find related content, identifies orphaned pages, and suggests
contextual internal links while maintaining language-specific isolation.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

# Try to import optional dependencies
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


@dataclass
class PageNode:
    """Represents a page in the content graph."""
    url: str
    file_path: str
    language: str
    title: str
    content_text: str
    incoming_links: int = 0
    outgoing_links: int = 0
    is_orphaned: bool = False
    link_priority: float = 0.0  # Higher = more important to link to


@dataclass
class LinkSuggestion:
    """A suggested internal link."""
    source_url: str
    source_file: str
    target_url: str
    target_file: str
    anchor_text: str
    relevance_score: float
    priority: str  # high, medium, low
    context: str = ""  # Surrounding text for placement


@dataclass
class InternalLinkingReport:
    """Complete internal linking analysis report."""
    total_pages: int
    pages_by_language: Dict[str, int]
    orphaned_pages: List[PageNode]
    link_suggestions: List[LinkSuggestion]
    linking_map: Dict[str, List[Dict[str, Any]]]
    statistics: Dict[str, Any]


class InternalLinkingEngine:
    """
    Automatic Internal Linking Engine with Graph Analysis.

    Features:
    - Creates content graph from all pages across 11 languages
    - Uses TF-IDF + cosine similarity to find related content
    - Identifies orphaned pages with <3 internal links
    - Suggests 5-10 contextual internal links per page
    - Prioritizes links to high-conversion pages
    - Maintains language-specific linking (no cross-linking except hreflang)
    """

    # Minimum links to not be considered orphaned
    ORPHAN_THRESHOLD = 3

    # Number of link suggestions per page
    SUGGESTIONS_PER_PAGE_MIN = 5
    SUGGESTIONS_PER_PAGE_MAX = 10

    # Supported languages
    SUPPORTED_LANGUAGES = [
        'es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'ko-KR', 'zh-CN',
        'ar-SA', 'hi-IN', 'it-IT', 'tr-TR', 'ru-RU'
    ]

    # High-conversion URL patterns (prioritize these for linking)
    HIGH_CONVERSION_PATTERNS = [
        r'/buy/', r'/review/', r'/best-', r'/vs-', r'/comparison',
        r'/guide/', r'/tutorial', r'/how-to', r'/price'
    ]

    # Anchor text stop words to avoid
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been'
    }

    def __init__(self, root_dir: str = ".", base_url: str = ""):
        """
        Initialize the linking engine.

        Args:
            root_dir: Root directory of the website
            base_url: Base URL of the website
        """
        self.root_dir = Path(root_dir).resolve()
        self.base_url = base_url.rstrip('/')
        self.pages: Dict[str, PageNode] = {}
        self.language_pages: Dict[str, List[PageNode]] = defaultdict(list)
        self.existing_links: Dict[str, Set[str]] = defaultdict(set)

        if not SKLEARN_AVAILABLE:
            print("⚠️  Warning: scikit-learn not installed. Install with: pip install scikit-learn")

    def extract_language_from_path(self, file_path: Path) -> str:
        """Extract language code from file path."""
        parts = file_path.relative_to(self.root_dir).parts

        # Check for language folder (e.g., /es-ES/, /fr-FR/)
        for part in parts:
            if part in self.SUPPORTED_LANGUAGES:
                return part

        # Default to English/primary
        return 'en-US'

    def extract_text_from_html(self, html_content: str) -> str:
        """Extract plain text from HTML content."""
        # Remove script and style elements
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        # Remove comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text[:10000]  # Limit length for performance

    def extract_title(self, html_content: str) -> str:
        """Extract page title from HTML."""
        match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

        # Fallback to H1
        match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

        return "Untitled"

    def extract_existing_links(self, html_content: str, source_url: str) -> Set[str]:
        """Extract existing internal links from HTML content."""
        links = set()

        # Find all href attributes
        href_matches = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>', html_content, re.IGNORECASE)

        for href in href_matches:
            # Skip external links, anchors, mailto, tel, javascript
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:', '//')):
                continue

            # Convert relative to absolute
            if not href.startswith(('http://', 'https://')):
                if self.base_url:
                    href = urljoin(self.base_url + '/', href)
                else:
                    href = '/' + href.lstrip('/')

            links.add(href)

        return links

    def scan_pages(self, pattern: str = "**/*.html") -> None:
        """
        Scan all HTML pages and build content graph.

        Args:
            pattern: Glob pattern for HTML files
        """
        html_files = list(self.root_dir.glob(pattern))

        # Exclude common non-content directories
        exclude_dirs = {'node_modules', 'venv', '.git', '__pycache__', '_site', 'city-through-the-lens-backup'}
        html_files = [f for f in html_files if not any(excl in f.parts for excl in exclude_dirs)]

        print(f"📄 Scanning {len(html_files)} HTML files...")

        for file_path in html_files:
            try:
                content = file_path.read_text(encoding='utf-8', errors='replace')

                # Extract metadata
                language = self.extract_language_from_path(file_path)
                title = self.extract_title(content)
                text = self.extract_text_from_html(content)

                # Generate URL from file path
                rel_path = file_path.relative_to(self.root_dir)
                if rel_path.name == 'index.html':
                    url_path = str(rel_path.parent)
                else:
                    url_path = str(rel_path.with_suffix(''))
                url_path = url_path.replace('\\', '/')

                if self.base_url:
                    url = f"{self.base_url}/{url_path}".rstrip('/')
                else:
                    url = '/' + url_path.lstrip('/')

                # Create page node
                node = PageNode(
                    url=url,
                    file_path=str(file_path),
                    language=language,
                    title=title,
                    content_text=text
                )

                # Track existing links
                existing = self.extract_existing_links(content, url)
                node.outgoing_links = len(existing)
                self.existing_links[url] = existing

                self.pages[url] = node
                self.language_pages[language].append(node)

            except Exception as e:
                print(f"⚠️  Error processing {file_path}: {e}")

        # Calculate incoming links
        for source_url, targets in self.existing_links.items():
            for target_url in targets:
                if target_url in self.pages:
                    self.pages[target_url].incoming_links += 1

        # Identify orphaned pages (<3 incoming links)
        for url, node in self.pages.items():
            if node.incoming_links < self.ORPHAN_THRESHOLD:
                node.is_orphaned = True

        print(f"✅ Found {len(self.pages)} pages across {len(self.language_pages)} languages")
        orphan_count = sum(1 for n in self.pages.values() if n.is_orphaned)
        print(f"⚠️  Found {orphan_count} orphaned pages (<{self.ORPHAN_THRESHOLD} incoming links)")

    def calculate_high_conversion_priority(self, url: str) -> float:
        """Calculate priority score for high-conversion pages."""
        score = 0.0

        for pattern in self.HIGH_CONVERSION_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                score += 0.2

        return min(score, 1.0)

    def extract_anchor_candidates(self, text: str, max_length: int = 60) -> List[str]:
        """Extract potential anchor text from content."""
        candidates = []

        # Extract noun phrases (simplified: capitalized words and multi-word sequences)
        words = text.split()

        # Look for meaningful phrases (3-6 words)
        for i in range(len(words) - 2):
            phrase_words = words[i:i+4]

            # Filter out stop words
            meaningful = [w for w in phrase_words if w.lower() not in self.STOP_WORDS and len(w) > 3]

            if len(meaningful) >= 2:
                phrase = ' '.join(meaningful[:4])
                if len(phrase) <= max_length:
                    candidates.append(phrase)

        # Return most frequent candidates
        from collections import Counter
        counter = Counter(candidates)
        return [phrase for phrase, _ in counter.most_common(20)]

    def find_related_pages(self, source_node: PageNode, limit: int = 10) -> List[Tuple[PageNode, float]]:
        """
        Find pages related to source using TF-IDF + cosine similarity.

        Args:
            source_node: Source page node
            limit: Maximum number of related pages to return

        Returns:
            List of (PageNode, similarity_score) tuples
        """
        if not SKLEARN_AVAILABLE:
            # Fallback: simple keyword matching
            return self._fallback_similarity(source_node, limit)

        try:
            # Get pages in same language
            lang_pages = self.language_pages.get(source_node.language, [])

            if len(lang_pages) < 2:
                return []

            # Prepare documents
            documents = [source_node.content_text]
            page_nodes = [source_node]

            for node in lang_pages:
                if node.url != source_node.url:
                    documents.append(node.content_text)
                    page_nodes.append(node)

            # Calculate TF-IDF
            vectorizer = TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                stop_words='english',
                min_df=2,
                max_df=0.8
            )

            tfidf_matrix = vectorizer.fit_transform(documents)

            # Calculate cosine similarity between source and all others
            source_vector = tfidf_matrix[0:1]
            other_vectors = tfidf_matrix[1:]
            similarities = cosine_similarity(source_vector, other_vectors)[0]

            # Sort by similarity
            results = []
            for idx, sim in enumerate(similarities):
                if sim > 0.1:  # Minimum threshold
                    results.append((page_nodes[idx + 1], float(sim)))

            # Sort descending and limit
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:limit]

        except Exception as e:
            print(f"⚠️  Similarity calculation error: {e}")
            return self._fallback_similarity(source_node, limit)

    def _fallback_similarity(self, source_node: PageNode, limit: int) -> List[Tuple[PageNode, float]]:
        """Fallback similarity using keyword overlap."""
        lang_pages = self.language_pages.get(source_node.language, [])
        source_words = set(source_node.content_text.lower().split())

        results = []
        for node in lang_pages:
            if node.url == source_node.url:
                continue

            target_words = set(node.content_text.lower().split())
            overlap = len(source_words & target_words) / max(len(source_words | target_words), 1)

            if overlap > 0.05:
                results.append((node, overlap))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def generate_link_suggestions(self) -> List[LinkSuggestion]:
        """Generate internal link suggestions for all pages."""
        suggestions = []

        print("🔗 Generating link suggestions...")

        for url, source_node in self.pages.items():
            # Find related pages
            related = self.find_related_pages(source_node, limit=self.SUGGESTIONS_PER_PAGE_MAX * 2)

            suggestion_count = 0
            for target_node, similarity in related:
                # Skip if link already exists
                if target_node.url in self.existing_links.get(url, set()):
                    continue

                # Determine priority
                conversion_priority = self.calculate_high_conversion_priority(target_node.url)
                orphan_bonus = 0.3 if target_node.is_orphaned else 0
                combined_score = similarity * 0.7 + conversion_priority * 0.2 + orphan_bonus * 0.1

                if combined_score < 0.15:
                    continue

                # Generate anchor text
                anchor_candidates = self.extract_anchor_candidates(target_node.content_text)
                anchor_text = anchor_candidates[0] if anchor_candidates else target_node.title

                # Determine priority level
                if combined_score > 0.6 or target_node.is_orphaned:
                    priority = "high"
                elif combined_score > 0.3:
                    priority = "medium"
                else:
                    priority = "low"

                suggestion = LinkSuggestion(
                    source_url=url,
                    source_file=source_node.file_path,
                    target_url=target_node.url,
                    target_file=target_node.file_path,
                    anchor_text=anchor_text[:60],
                    relevance_score=round(combined_score, 3),
                    priority=priority,
                    context=f"Related content: {target_node.title}"
                )

                suggestions.append(suggestion)
                suggestion_count += 1

                if suggestion_count >= self.SUGGESTIONS_PER_PAGE_MAX:
                    break

        print(f"✅ Generated {len(suggestions)} link suggestions")
        return suggestions

    def generate_linking_map(self, suggestions: List[LinkSuggestion]) -> Dict[str, List[Dict[str, Any]]]:
        """Generate the final internal linking map."""
        linking_map = defaultdict(list)

        for suggestion in suggestions:
            linking_map[suggestion.source_url].append({
                "target": suggestion.target_url,
                "target_file": suggestion.target_file,
                "anchor_text": suggestion.anchor_text,
                "priority": suggestion.priority,
                "relevance_score": suggestion.relevance_score,
                "context": suggestion.context
            })

        # Sort each source's links by priority and score
        for source_url in linking_map:
            linking_map[source_url].sort(
                key=lambda x: ({"high": 0, "medium": 1, "low": 2}[x["priority"]], -x["relevance_score"])
            )

        return dict(linking_map)

    def analyze(self, output_file: Optional[str] = None) -> InternalLinkingReport:
        """
        Run complete internal linking analysis.

        Args:
            output_file: Optional path to save JSON report

        Returns:
            InternalLinkingReport with all findings
        """
        # Scan all pages
        self.scan_pages()

        # Generate suggestions
        suggestions = self.generate_link_suggestions()

        # Generate linking map
        linking_map = self.generate_linking_map(suggestions)

        # Collect orphaned pages
        orphaned_pages = [node for node in self.pages.values() if node.is_orphaned]

        # Calculate statistics
        stats = {
            "total_pages": len(self.pages),
            "orphaned_pages": len(orphaned_pages),
            "total_suggestions": len(suggestions),
            "avg_suggestions_per_page": len(suggestions) / max(len(self.pages), 1),
            "pages_with_high_priority_links": sum(
                1 for s in suggestions if s.priority == "high"
            ),
            "languages_analyzed": list(self.language_pages.keys())
        }

        # Create report
        report = InternalLinkingReport(
            total_pages=len(self.pages),
            pages_by_language={lang: len(nodes) for lang, nodes in self.language_pages.items()},
            orphaned_pages=orphaned_pages,
            link_suggestions=suggestions,
            linking_map=linking_map,
            statistics=stats
        )

        # Save report if output file specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            report_data = {
                "statistics": stats,
                "pages_by_language": report.pages_by_language,
                "orphaned_pages": [
                    {"url": p.url, "file": p.file_path, "language": p.language, "incoming_links": p.incoming_links}
                    for p in orphaned_pages
                ],
                "linking_map": {
                    source: links for source, links in linking_map.items()
                },
                "sample_suggestions": [
                    {
                        "source": s.source_url,
                        "target": s.target_url,
                        "anchor_text": s.anchor_text,
                        "priority": s.priority,
                        "relevance_score": s.relevance_score
                    }
                    for s in suggestions[:50]  # Limit sample size
                ]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"📊 Report saved to: {output_path}")

        return report


def main():
    """CLI entry point for internal linking analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Internal Linking Engine with Graph Analysis")
    parser.add_argument("--root", "-r", default=".", help="Root directory to scan")
    parser.add_argument("--base-url", "-b", default="", help="Base URL of the website")
    parser.add_argument("--output", "-o", default="internal_linking_map.json", help="Output JSON file")
    args = parser.parse_args()

    engine = InternalLinkingEngine(root_dir=args.root, base_url=args.base_url)
    report = engine.analyze(output_file=args.output)

    # Print summary
    print(f"\n{'='*60}")
    print(f"INTERNAL LINKING ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Total pages analyzed: {report.total_pages}")
    print(f"Languages found: {list(report.pages_by_language.keys())}")
    print(f"Orphaned pages: {len(report.orphaned_pages)}")
    print(f"Link suggestions generated: {len(report.link_suggestions)}")
    print(f"Avg suggestions per page: {report.statistics['avg_suggestions_per_page']:.1f}")
    print(f"{'='*60}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

