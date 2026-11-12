# Securing Enterprise LLMs: The Definitive Guide to Prompt Injection and Jailbreak Defense

**Companion code and practical exercises for _Securing Enterprise LLMs: The Definitive Guide to Prompt Injection and Jailbreak Defense_.**

**Book author:** Adrian Cross

## About the book

This book delivers a comprehensive, technically rigorous guide to defending enterprise large language model (LLM) deployments against prompt injection and jailbreak attacks. It systematically covers the threat landscape, attack methodologies, and the unique risks these attacks pose to sensitive data and agentic workflows in organizational contexts. Readers will find actionable, layered mitigation strategies, including architectural patterns, code-level defenses, and reproducible example implementations. The book also provides integration guidance for enterprise environments, security testing frameworks, and practical advice for adapting defenses to evolving attack vectors. Limitations of current approaches and vendor-specific considerations are clearly addressed, equipping readers to make informed, context-sensitive security decisions.

## Who this is for

Enterprise security professionals, solution architects, and technical leaders responsible for deploying and safeguarding large language model (LLM) systems within organizations handling sensitive data and agentic workflows.

## What you will find here

This repository accompanies the book with chapter-specific implementation projects, examples, and reproducible exercises. Each implementation folder has its own README with the setup and execution instructions relevant to that chapter.

The book provides the explanations and context; this repository provides the companion implementation material.

## Chapter guide

- **Chapter 1: Why Prompt Injection and Jailbreaks Matter for Enterprise LLMs** — Reading chapter; no separate implementation required
- **Chapter 2: The Threat Landscape: Taxonomy of Prompt Injection and Jailbreak Attacks** — Reading chapter; no separate implementation required
- **Chapter 3: Enterprise LLM Architectures and Trust Boundaries** — Reading chapter; no separate implementation required
- **Chapter 4: Red-Teaming Enterprise LLMs: Building an Attack Harness** — [Companion implementation](chapter-04/)
- **Chapter 5: Foundational Defenses: Guardrails, Policies, and Content Firewalls** — [Companion implementation](chapter-05/)
- **Chapter 6: Defending Against Direct Prompt Injection** — [Companion implementation](chapter-06/)
- **Chapter 7: Hardening Retrieval-Augmented Generation Against Indirect Prompt Injection** — [Companion implementation](chapter-07/)
- **Chapter 8: Securing Agentic Workflows and Tool Use** — [Companion implementation](chapter-08/)
- **Chapter 9: Advanced Jailbreak Defense and Response** — [Companion implementation](chapter-09/)
- **Chapter 10: Architecting for Least Privilege and Blast Radius Reduction** — [Companion implementation](chapter-10/)
- **Chapter 11: Security Testing, Benchmarking, and Continuous Assurance** — [Companion implementation](chapter-11/)
- **Chapter 12: Vendor Architectures, Managed Services, and Open Source Models** — [Companion implementation](chapter-12/)
- **Chapter 13: Case Studies: Securing Enterprise LLM Deployments End-to-End** — [Companion implementation](chapter-13/)
- **Chapter 14: Limitations, Open Problems, and Future Directions** — Reading chapter; no separate implementation required
- **Chapter 15: Putting It All Together: A Playbook for Securing Enterprise LLMs** — Reading chapter; no separate implementation required

## Getting started

1. Read the chapter you want to explore in the book.
2. Open the corresponding `chapter-XX/` folder above, where an implementation is available.
3. Follow that folder’s `README.md` for prerequisites, setup, configuration, and commands.
4. Run the chapter’s examples and compare the results with the discussion in the book.

Different chapters may have different dependencies and environment requirements; use the instructions in each chapter folder rather than assuming one setup works for all projects.

## Repository structure

```text
README.md                  # This repository overview
chapter-XX/                # Chapter-specific companion projects (where provided)
  README.md                # Setup and execution instructions for that chapter
  ...                      # Source code, tests, and other chapter assets
```

## Notes

- The chapter folders are intended to complement the book, not replace it.
- Follow each chapter README before running code, especially when external services or API credentials are involved.
- Keep secrets and local environment files out of version control.

## Book and repository

- **Companion repository:** https://github.com/bookauthority/securing-enterprise-llms-prompt-injection-jailbreak-defense
- **Book:** Securing Enterprise LLMs: The Definitive Guide to Prompt Injection and Jailbreak Defense

---

This README is generated from the book’s approved chapter plan. Chapter-specific instructions live in their respective folders.
