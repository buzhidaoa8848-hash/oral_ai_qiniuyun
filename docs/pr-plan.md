# PR Plan — SceneTalk AI

## Launch Narrative

**"AI-powered conversation practice that actually listens."**

SceneTalk AI is an open-source, provider-flexible language learning tool. Unlike Duolingo (gamified translation) or Pimsleur (audio-only drills), SceneTalk puts learners into realistic scenes and gives them multi-dimensional feedback on every word they speak — powered by the LLM/STT/TTS provider of their choice.

## Target Outlets

### Developer / Tech
- **Hacker News** (Show HN): "SceneTalk AI — Open-source conversation practice with pluggable AI providers"
- **Product Hunt**: Launch with demo video and free tier
- **r/programming**, **r/languagelearning**: Cross-post

### Chinese Tech Community
- **掘金 (Juejin)**: Technical deep-dive on the provider abstraction pattern
- **知乎 (Zhihu)**: "如何用AI练口语？我们开源了一个方案" (How to practice speaking with AI? We open-sourced a solution)
- **V2EX**: Launch thread in the "Create" node
- **GitHub Trending**: Aim for trending in "Python" and "TypeScript" topics

### AI / EdTech
- **Twitter/X**: Thread from project maintainer, tagging AI and EdTech influencers
- **Reddit**: r/artificial, r/edtech, r/ChineseLanguage
- **Dev.to**: "Building a multi-provider AI speaking coach with FastAPI + Next.js"

## Key Messages

| Angle                     | Pitch                                                                 |
|---------------------------|-----------------------------------------------------------------------|
| **Provider flexibility**  | "Use OpenAI, DashScope, DeepSeek, or Azure — you control your AI."   |
| **Open source**           | "Self-host your speaking practice. Your voice data stays yours."      |
| **Scene-based learning**  | "Practice real conversations, not flashcards."                        |
| **Technical depth**       | "A clean example of provider abstraction, streaming STT/TTS, and Next.js + FastAPI integration." |

## Launch Checklist

- [ ] README with GIF demo
- [ ] Live demo URL (Vercel for frontend, Railway/Render for backend)
- [ ] 10+ built-in scene cards covering A1–B2
- [ ] Provider setup guide (OpenAI, DashScope, DeepSeek, Azure)
- [ ] CONTRIBUTING.md with "good first issue" tags
- [ ] LICENSE (MIT)
- [ ] Social media assets (banner, demo GIF, screenshots)

## Timeline

| Week | Activity                                                    |
|------|-------------------------------------------------------------|
| 1    | Core loop working (scene → record → STT → evaluate → TTS)  |
| 2    | Provider adapters for all 4 providers, mock fallback        |
| 3    | UI polish, progress dashboard, 10+ scenes                   |
| 4    | Demo video, docs finalization, outreach prep                |
| 5    | Launch week: HN, PH, Reddit, Chinese platforms              |

## Success Metrics

- GitHub stars (target: 500 in first month)
- Demo completions (user finishes a full scene loop)
- Provider diversity (how many users configure non-OpenAI providers)
- Community contributions (PRs, new scene cards, new language pairs)
