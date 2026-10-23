| Call | Model | Requests | Fixed context (first request) | Content added later | Output |
|---|---|---|---|---|---|
| gp-tiny | claude-fable-5-1 | 3 | 65,773 | 5,065 | 513 |
| lean-tiny | claude-opus-5-5 | 3 | 16,686 | 2,656 | 510 |
| lean-empty | claude-opus-5-5 | 3 | 16,850 | 2,492 | 588 |
| lean-known | claude-opus-5-5 | 3 | 16,682 | 7,409 | 1,761 |

lean-tiny: startup context 42,230 characters
   22,073    52%  instruction file CLAUDE.md
    7,574    18%  instruction file CLAUDE.md
    4,644    11%  SubagentStart hook (first principles, work line)
    3,718     9%  tool schemas (Read, Write, SubagentHandback, advisor)
    1,624     4%  system prompt
    1,547     4%  git status snapshot
      709     2%  instruction file MEMORY.md
      341     1%  hand-back reminder

gp-tiny: startup context 195,552 characters
  100,042    51%  tool schemas (Agent, Artifact, Bash, Edit, Read, SearchPlugins, Skill, Too)
   28,869    15%  skills listing
   22,073    11%  instruction file CLAUDE.md
   21,039    11%  deferred tool names
    7,574     4%  instruction file CLAUDE.md
    5,242     3%  agent listing
    4,644     2%  SubagentStart hook (first principles, work line)
    2,814     1%  system prompt
    1,546     1%  git status snapshot
      709     0%  instruction file MEMORY.md
      581     0%  attribution reminder
      419     0%  hand-back reminder

lean: instruction files and memory index share = 0.719
