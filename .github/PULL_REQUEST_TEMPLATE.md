## Description
<!-- Briefly describe the changes in this PR. -->

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Content/SEO update (internal links, meta tags, hreflang)
- [ ] Refactoring (no functional changes)

## Content-Quality Guardrail Checklist
*Required for all PRs adding or modifying internal links.*

- [ ] **Plain Text Test:** Each new link's context sentence makes sense and is factually accurate if the hyperlink is removed.
- [ ] **No Misleading Claims:** Checked for inaccurate size/weight claims (e.g., calling a full-frame camera "smaller" or "pocketable").
- [ ] **No Unverified Comparisons:** Removed unsupported superlatives (e.g., "stronger stabilization", "better autofocus") unless explicitly verified against target specs.
- [ ] **Accurate Categorization:** Category labels match the target content (e.g., not labeling drone or full-frame footage as "compact-camera technique").
- [ ] **Descriptive Anchors:** Anchor text is descriptive and avoids generic phrases like "click here", "read more", or "this page".

## Validation Results
<!-- Paste the output of your local validation scripts here. -->

- [ ] `python internal_link_audit.py` passed (0 broken links, 0 orphans).
- [ ] `python scripts/validate_hreflang_consistency.py` passed.
- [ ] `python scripts/validate_link_context_quality.py` passed.
- [ ] `git diff --check` passed.
